from Camera.camera import Camera
from Preprocessing.preprocessing import Preprocessing
from Detection.detection import DetectionBase
from Detection.distanceestimation import DistanceEstimation
from threading.threadingmanager import ThreadingManager
from Visualization.visualization import Visualization
from Calibration.calibration import Calibration
import cv2


"""
process_category(category, blurred_image, lower_hsv, upper_hsv, image_width, output_data)
- Process the category of the detected object.
- Apply color thresholding and morphological filters.
- Analyze contours and classify objects based on category.
- Return the classified objects.

process_image_pipeline(camera, color_ranges, calibration)
- Process the image pipeline.
- Capture frames from the camera.
- Preprocess the frame.
- Run the processing pipeline in parallel.
- Display the processed frame.
- Break the loop if 'q' is pressed.
- Close the camera and destroy all windows.

main()
- Create a camera object.
- Load the calibration data.
- Process the image pipeline.
- Close the camera and destroy all windows.

"""


def process_category(category, blurred_image, lower_hsv, upper_hsv, image_width, output_data):
    mask = Preprocessing.color_threshold(blurred_image, lower_hsv, upper_hsv)
    processed_mask = Preprocessing.apply_morphological_filters(mask)
    contour_image, objects = DetectionBase.analyze_contours(blurred_image, processed_mask)
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

        ThreadingManager.run_parallel_processing(tasks) # Run the tasks in parallel
        
        Visualization.show_image("Processed Frame", blurred_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def main():
    camera = Camera()

    calibration = Calibration()
    color_ranges, homography_matrix, focal_length = calibration.load_csv()


    process_image_pipeline(camera, color_ranges, calibration)

    camera.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
