import cv2
import numpy as np
import csv
from picamera2 import Picamera2

# Global variables for calibration
focal_length = None
captured_image = None

# Known parameters for focal length calibration
real_world_width = 0.07  # 7 cm object width in meters
distance_to_object = 0.28  # 28 cm distance to the object in meters

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
        #if solidity < 0.5:
            #continue  # Skip contours with solidity less than 0.5
        if fill_ratio < 0.1:
            continue  # Skip contours with fill ratio less than 0.1
        if circularity < 0.7:
            continue

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

# Function to calculate focal length based on detected marker
def calibrate_focal_length(detected_objects):
    global focal_length
    if len(detected_objects) > 0:
        marker = detected_objects[0]  # Assuming the largest object is the marker
        x, y, w, h = marker['position']
        focal_length = (w * distance_to_object) / real_world_width
        print(f"Calculated Focal Length: {focal_length:.2f} pixels")
        return marker
    else:
        print("No marker detected for focal length calibration.")
        return None

# Function to save focal length to a CSV file
def save_focal_length(focal_length):
    with open("calibrate_focal_length.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Focal Length", focal_length])
    print("Focal length data saved to focal_length_data.csv")

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

def main():
    global captured_image, focal_length

    # Load color thresholds from CSV
    color_ranges = load_color_thresholds('calibrate.csv')
    
    # Initialize the Picamera2 feed
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()
    
    while True:
        frame = picam2.capture_array()
        scale = 0.5
        frame = cv2.flip(frame, 0)  # Flip horizontally and vertically
        blurred_image = preprocess_image(frame, scale)
        
        # Process the marker category only
        category = "Marker"
        lower_hsv, upper_hsv = color_ranges[category]
        mask = color_threshold(blurred_image, lower_hsv, upper_hsv)
        processed_mask = apply_morphological_filters(mask)
        contour_image, detected_objects = analyze_contours(blurred_image, processed_mask)

        # Display the result image
        cv2.imshow("Marker Detection", contour_image)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):  # Capture the image if 'c' is pressed
            captured_image = frame.copy()
            print("Image captured!")
            cv2.destroyWindow("Marker Detection")  # Close the Marker Detection window
            break

    # If an image was captured, display it in a new window and perform calibration steps
    if captured_image is not None:
        cv2.imshow("Captured Image", captured_image)  # Display the captured frame
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):  # Exit the loop if 'q' is pressed
                break
            elif key == ord('1'):  # Calibrate focal length if '1' is pressed
                marker = calibrate_focal_length(detected_objects)
                if marker is not None:
                    print(f"Focal length: {focal_length:.2f} pixels")
            elif key == ord('s'):  # Save the calibration data if 's' is pressed
                if focal_length is not None:
                    save_focal_length(focal_length)
                    print("Calibration data saved.")
                else:
                    print("Ensure the focal length is calibrated before saving.")

    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
