from Camera.camera import Camera
from Preprocessing.preprocessing import Preprocessing
from Detection.detection import Detection
from Detection.distanceestimation import DistanceEstimation
from threading.threadingmanager import ThreadingManager
from Visualization.visualization import Visualization
from Calibration.calibration import Calibration

def process_category(category, blurred_image, lower_hsv, upper_hsv, image_width, output_data):
    mask = Preprocessing.color_threshold(blurred_image, lower_hsv, upper_hsv)
    processed_mask = Preprocessing.apply_morphological_filters(mask)
    contour_image, objects = Detection.analyze_contours(blurred_image, processed_mask)
    classified_objects = apply_object_logic(objects, category, image_width, contour_image, output_data)
    return classified_objects

def process_image_pipeline(camera, color_ranges, calibration):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue

        blurred_image = Preprocessing.preprocess(frame)
        image_width = blurred_image.shape[1]
        output_data = {"items": [None] * 6, "shelves": [None] * 6, "row_markers": [None, None, None], "obstacles": None, "packing_bay": None}

        tasks = [{"function": process_category, "args": (category, blurred_image, color_ranges[category][0], color_ranges[category][1], image_width, output_data)} for category in color_ranges]

        ThreadingManager.run_parallel_processing(tasks)

        Visualization.show_image("Processed Frame", blurred_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def main():
    camera = Camera()
    camera.start()

    calibration = Calibration()
    calibration.load_focal_length('calibrate_focal_length.csv')
    calibration.load_homography_matrix('calibrate_homography.csv')

    color_ranges = {
        'Shelf': ([110, 50, 50], [130, 255, 255]),
        'Item': ([0, 70, 50], [10, 255, 255]),
        'Marker': ([100, 150, 0], [140, 255, 255]),
        'Obstacle': ([25, 50, 70], [35, 255, 255])
    }

    process_image_pipeline(camera, color_ranges, calibration)

    camera.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
