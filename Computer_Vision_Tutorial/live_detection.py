import cv2
import numpy as np
import csv
import json
from picamera2 import Picamera2
from threading import Thread, Lock
import time

# Global variables for frame handling
frame = None
processed_masks = {}
detected_objects = {}
frame_lock = Lock()

# Global variables to store calibration data
focal_length = None
homography_matrix = None

def capture_frames(picam2):
    """Capture frames from the camera and store them in a global variable."""
    global frame
    while True:
        with frame_lock:
            frame = cv2.flip(picam2.capture_array(), -1)  # Flip horizontally and vertically
        time.sleep(0.01)  # Small delay to reduce CPU usage

def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    return cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)

def color_threshold(image, lower_hsv, upper_hsv):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv_image, lower_hsv, upper_hsv)

def apply_morphological_filters(mask, kernel_size=(5, 5)):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)

def analyze_contours(image, mask, min_area=400, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image = image.copy()
    detected_objects = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
            continue

        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx_vertices = cv2.approxPolyDP(contour, epsilon, True)
        bottom_corners = sorted(approx_vertices, key=lambda p: p[0][1], reverse=True)[:2]
        bottom_corners = sorted(bottom_corners, key=lambda p: p[0][0])

        perimeter = cv2.arcLength(contour, True)
        circularity = (4 * np.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = (area / hull_area) if hull_area > 0 else 0
        bounding_box_area = w * h
        fill_ratio = (area / bounding_box_area) if bounding_box_area > 0 else 0

        if solidity < 0.5 or fill_ratio < 0.1:
            continue

        cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)
        cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        for corner in bottom_corners:
            cv2.circle(contour_image, tuple(corner[0]), 5, (0, 0, 255), -1)

        detected_objects.append({
            "position": (x, y, w, h),
            "area": area,
            "aspect_ratio": aspect_ratio,
            "solidity": solidity,
            "fill_ratio": fill_ratio,
            "circularity": circularity,
            "hull": hull,
            "perimeter": perimeter,
            "bottom_corners": bottom_corners
        })

    return contour_image, detected_objects

def apply_object_logic(detected_objects, category, image_width, contour_image, output_data):
    classified_objects = []

    for obj in detected_objects:
        x, y, w, h = obj['position']
        obj_type = category
        distance = None

        if category == "Marker":
            obj_type = classify_marker(obj, detected_objects)
            distance = estimate_distance(w, 0.07)
            bearing = estimate_bearing(x + w // 2, image_width)
            if obj_type.startswith("Row Marker"):
                marker_index = int(obj_type.split()[-1]) - 1
                if marker_index < 3:
                    output_data['row_markers'][marker_index] = [distance, bearing]
            elif obj_type == "Packing Station Marker":
                output_data['packing_bay'] = [distance, bearing]
        
        elif category == "Obstacle":
            obj_type = "Obstacle"
            distance = estimate_distance(w, 0.05)
            output_data['obstacles'] = output_data.get('obstacles', [])
            output_data['obstacles'].append([distance, estimate_bearing(x + w // 2, image_width)])

        elif category == "Shelf":
            obj_type = "Shelf"
            distance = estimate_homography_distance(obj['position'])
            for i, corner in enumerate(obj['bottom_corners']):
                corner_distance = estimate_homography_distance((corner[0][0], corner[0][1], 0, 0))
                bearing = estimate_bearing(corner[0][0], image_width)
                if i < 6:
                    output_data['shelves'][i] = [corner_distance, bearing]

        elif category == "Item":
            obj_type = "Item"
            distance = estimate_distance(w, 0.03)
            item_index = len([i for i in output_data['items'] if i is not None])
            if item_index < 6:
                output_data['items'][item_index] = [distance, estimate_bearing(x + w // 2, image_width)]

        if obj_type and distance is not None:
            bearing = estimate_bearing(x + w // 2, image_width)
            obj.update({
                "type": obj_type,
                "distance": distance,
                "bearing": bearing,
                "center": (x + w // 2, y + h // 2),
                "width": w
            })
            classified_objects.append(obj)
            
            draw_category_text(contour_image, obj_type, obj['center'], distance, bearing)

    return classified_objects

def classify_marker(obj, detected_objects):
    circularity = obj['circularity']
    aspect_ratio = obj['aspect_ratio']

    if circularity > 0.8:
        circle_count = sum(1 for o in detected_objects if o['circularity'] > 0.8)
        return f"Row Marker {circle_count}" if circle_count in [1, 2, 3] else "Unknown Marker"
    elif 0.9 < aspect_ratio < 1.1:
        return "Packing Station Marker"

    return "Unknown Marker"

def draw_category_text(image, label, center, distance, bearing):
    label_text = f'{label}:'
    range_text = f'Range: {distance:.2f}m'
    bearing_text = f'Bearing: {bearing:.2f}deg'

    positions = [(center[0], center[1] - offset) for offset in [30, 15, 0]]
    texts = [label_text, range_text, bearing_text]

    for pos, text in zip(positions, texts):
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

def estimate_distance(object_width, real_object_width):
    return (real_object_width * focal_length) / object_width

def estimate_homography_distance(position):
    if homography_matrix is None:
        raise ValueError("Homography matrix not loaded.")

    x, y, w, h = position
    bottom_center_x = x + w // 2
    bottom_center_y = y + h
    ground_coords = apply_homography_to_point(bottom_center_x, bottom_center_y, homography_matrix)
    return np.sqrt(ground_coords[0]**2 + ground_coords[1]**2)

def apply_homography_to_point(x, y, M):
    point = np.array([[[x, y]]], dtype='float32')
    return cv2.perspectiveTransform(point, M)[0][0]

def estimate_bearing(object_center_x, image_width):
    horizontal_offset = object_center_x - (image_width / 2)
    max_bearing_angle = 30
    return (max_bearing_angle * horizontal_offset) / (image_width / 2)

def load_color_thresholds(csv_file):
    color_ranges = {}
    category_mapping = {
        'orange': 'Item',
        'green': 'Obstacle',
        'blue': 'Shelf',
        'black': 'Marker'
    }
    
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            category = category_mapping.get(row[0])
            if category:
                lower_hsv = np.array(list(map(int, row[1:4])))
                upper_hsv = np.array(list(map(int, row[4:7])))
                color_ranges[category] = (lower_hsv, upper_hsv)
    return color_ranges

def load_focal_length(csv_file):
    global focal_length
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        focal_length = float(next(csv_reader)[1])

def load_homography_matrix(csv_file):
    global homography_matrix
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        homography_matrix = np.array([list(map(float, row)) for row in csv_reader])

def export_range_bearing(data, output_json='output_data.json'):
    with open(output_json, 'w') as file:
        json.dump(data, file, indent=4)

def process_image_pipeline(color_ranges):
    global frame, processed_masks, detected_objects
    while True:
        with frame_lock:
            if frame is None:
                continue
            local_frame = frame.copy()

        blurred_image = preprocess_image(local_frame)
        image_width = blurred_image.shape[1]

        local_processed_masks = {}
        local_detected_objects = {}

        output_data = {
            "items": [None] * 6,
            "shelves": [None] * 6,
            "row_markers": [None, None, None],
            "obstacles": None,
            "packing_bay": None
        }
        print(f"process image pipeline")

        for category, (lower_hsv, upper_hsv) in color_ranges.items():
            mask = color_threshold(blurred_image, lower_hsv, upper_hsv)
            processed_mask = apply_morphological_filters(mask)
            contour_image, objects = analyze_contours(blurred_image, processed_mask)
            classified_objects = apply_object_logic(objects, category, image_width, contour_image, output_data)

            local_processed_masks[category] = (mask, processed_mask, contour_image)
            local_detected_objects[category] = classified_objects

        with frame_lock:
            processed_masks = local_processed_masks.copy()
            detected_objects = local_detected_objects.copy()

        export_range_bearing(output_data)

def main():
    global processed_masks

    color_ranges = load_color_thresholds('calibrate.csv')
    load_homography_matrix('calibrate_homography.csv')
    load_focal_length('calibrate_focal_length.csv')
    
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))
    picam2.start()

    capture_thread = Thread(target=capture_frames, args=(picam2,))
    capture_thread.daemon = True
    capture_thread.start()

    processing_thread = Thread(target=process_image_pipeline, args=(color_ranges,))
    processing_thread.daemon = True
    processing_thread.start()

    while True:
        start_time = time.time()

        with frame_lock:
            if processed_masks:
                for category in color_ranges.keys():
                    _, _, contour_image = processed_masks.get(category, (None, None, None))
                    if contour_image is not None:
                        cv2.imshow(f'{category} Contour Analysis', contour_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        fps = 1 / (time.time() - start_time)
        #print(f"FPS: {fps:.2f}")

    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
