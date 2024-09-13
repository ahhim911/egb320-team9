import cv2
import numpy as np
import csv
from picamera2 import Picamera2

# Global variables to store calibration data
focal_length = None
homography_matrix = None

# Function to preprocess the image: resize and apply Gaussian blur
def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    blurred_image = cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)
    return blurred_image

# Function to apply color thresholding
def color_threshold(image, lower_hsv, upper_hsv):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
    return mask

# Function to apply morphological operations on a thresholded image
def apply_morphological_filters(mask, kernel_size=(5, 5)):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)
    return closed_image

# Function to analyze contours and extract relevant features
def analyze_contours(image, mask, min_area=400, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image = image.copy()

    detected_objects = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue  # Skip contours that are too small

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
            continue  # Skip contours with an aspect ratio out of bounds

        

        # Calculate contour features
        perimeter = cv2.arcLength(contour, True)
        circularity = (4 * np.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = (area / hull_area) if hull_area > 0 else 0
        bounding_box_area = w * h
        fill_ratio = (area / bounding_box_area) if bounding_box_area > 0 else 0

        

        # Skip contours with low solidity or fill ratio
        if solidity < 0.5:
            continue  # Skip contours with solidity less than 0.5
        if fill_ratio < 0.1:
            continue  # Skip contours with fill ratio less than 0.1

        # Draw contour and bounding box on the image
        cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)  # Green contours
        cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Blue bounding box

        # Store detected object features
        detected_objects.append({
            "position": (x, y, w, h),
            "area": area,
            "aspect_ratio": aspect_ratio,
            "solidity": solidity,
            "fill_ratio": fill_ratio,
            "circularity": circularity,
            "hull": hull,
            "perimeter": perimeter
        })

    return contour_image, detected_objects

# Function to apply category-specific logic and classify detected objects
def apply_object_logic(detected_objects, category, image_width):
    classified_objects = []

    for obj in detected_objects:
        x, y, w, h = obj['position']
        obj_type = category
        distance = None  # Initialize distance to None

        # Marker-specific logic
        if category == "Marker":
            obj_type = classify_marker(obj, detected_objects)
            #distance = w  # Estimate distance for Markers
            distance = estimate_distance(w, 0.07)  # Estimate distance for Markers

        # Obstacle-specific logic
        elif category == "Obstacle":
            obj_type = "Obstacle"
            #distance = w
            distance = estimate_distance(w, 0.05)  # Estimate distance for Obstacles

        # Shelf-specific logic
        elif category == "Shelf":
            obj_type = "Shelf"
            distance = estimate_homography_distance(obj['position'])

        # Item-specific logic
        elif category == "Item":
            obj_type = "Item"
            distance = estimate_distance(w, 0.03)  # Estimate distance for Items

        # If object type is valid and distance is calculated, update object
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

    return classified_objects

# Process logic for markers
def classify_marker(obj, detected_objects):
    circularity = obj['circularity']
    aspect_ratio = obj['aspect_ratio']

    if circularity > 0.8:  # Close to circular
        circle_count = sum(1 for o in detected_objects if o['circularity'] > 0.8)
        if circle_count == 1:
            return "Row Marker 1"
        elif circle_count == 2:
            return "Row Marker 2"
        elif circle_count == 3:
            return "Row Marker 3"
    elif 0.9 < aspect_ratio < 1.1:  # Square-like
        return "Packing Station Marker"

    return "Unknown Marker"

def draw_category_text(image, category, center, distance, bearing, width):
    text = f'{category}: {distance:.2f}m, {bearing:.2f}deg, W: {width}px'
    cv2.putText(image, text, center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def estimate_distance(object_width, real_object_width):
    global focal_length
    #print(f"{object_width:2}")
    return (real_object_width * focal_length) / object_width

def estimate_homography_distance(position):
    global homography_matrix
    if homography_matrix is None:
        print("Error: Homography matrix not loaded.")
        return None

    # Extract the bottom-center point (x, y) from the bounding box
    x, y, w, h = position
    bottom_center_x = x + w // 2
    bottom_center_y = y + h  # Use the bottom of the bounding box

    # Apply the homography matrix to the bottom-center point
    ground_coords = apply_homography_to_point(bottom_center_x, bottom_center_y, homography_matrix)

    # Calculate the Euclidean distance from the origin (assuming the camera is at the origin)
    distance = np.sqrt(ground_coords[0]**2 + ground_coords[1]**2)

    #print(f"Estimated Distance (Homography-based): {distance:.2f} meters")
    return distance

# Supporting function to apply the homography matrix
def apply_homography_to_point(x, y, M):
    point = np.array([[x, y]], dtype='float32')
    point = np.array([point])
    transformed_point = cv2.perspectiveTransform(point, M)
    return transformed_point[0][0]

def estimate_bearing(object_center_x, image_width):
    # Calculate the horizontal offset from the center of the frame
    horizontal_offset = object_center_x - (image_width / 2)

    # Define the range for the bearing (-30 degrees to 30 degrees)
    max_bearing_angle = 30

    # Calculate the bearing based on the proportion of the offset within the image width
    bearing = (max_bearing_angle * horizontal_offset) / (image_width / 2)

    return bearing

# Function to load color thresholds from CSV file
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
            category = category_mapping.get(row[0], None)
            if category:
                lower_hsv = np.array([int(row[1]), int(row[2]), int(row[3])])
                upper_hsv = np.array([int(row[4]), int(row[5]), int(row[6])])
                color_ranges[category] = (lower_hsv, upper_hsv)
    return color_ranges

# Function to load focal length from CSV
def load_focal_length(csv_file):
    global focal_length
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        focal_length = float(next(csv_reader)[1])

# Function to load homography matrix from CSV
def load_homography_matrix(csv_file):
    global homography_matrix
    homography_matrix = []
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header
        for row in csv_reader:
            homography_matrix.append([float(val) for val in row])
    homography_matrix = np.array(homography_matrix)

def main():
    global captured_image

    # Load color thresholds from CSV
    color_ranges = load_color_thresholds('calibrate.csv')

    # Load homography matrix & focal length
    load_homography_matrix('calibrate_homography.csv')
    load_focal_length('calibrate_focal_length.csv')

    # Initialize the Picamera2 feed
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()

    while True:
        frame = picam2.capture_array()
        scale = 0.5
        frame = cv2.flip(frame, -1)  # Flip horizontally and vertically
        blurred_image = preprocess_image(frame, scale)
        image_width = blurred_image.shape[1]  # Get the image width for bearing calculation

        masks = {}
        processed_masks = {}
        detected_objects = {}

        for category, (lower_hsv, upper_hsv) in color_ranges.items():
            masks[category] = color_threshold(blurred_image, lower_hsv, upper_hsv)
            processed_mask = apply_morphological_filters(masks[category])
            contour_image, objects = analyze_contours(blurred_image, processed_mask)
            classified_objects = apply_object_logic(objects, category, image_width)

            processed_masks[category] = (masks[category], processed_mask, contour_image)
            detected_objects[category] = classified_objects

            for obj in classified_objects:
                distance = obj['distance']
                width = obj['width']  # Retrieve the width of the object
                draw_category_text(contour_image, obj['type'], obj['center'], distance, obj['bearing'], width)
                
        # Display the result images for each category
        for category, (_, _, contour_image) in processed_masks.items():
            cv2.imshow(f'{category} Contour Analysis', contour_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
