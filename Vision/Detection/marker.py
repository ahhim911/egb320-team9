# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase
import os
import sys

# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Marker(DetectionBase):
    def __init__(self):
        super().__init__("Marker")

    def find_marker(self, image, filled_wall_mask, color_ranges):
        """
        Detect markers within the wall's bounding box using a bitwise AND to isolate markers on walls.
        """
        lower_hsv, upper_hsv = color_ranges['Marker']
        
        # Step 1: Preprocess image for marker detection
        marker_mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(5, 5), sigmaX=2, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(5, 5))

        # Step 2: Use bitwise AND to keep only markers on the wall
        marker_on_wall_mask = cv2.bitwise_and(marker_mask, marker_mask, mask=filled_wall_mask)

        # Step 3: Analyze contours for the markers
        detected_markers = self.analyze_contours(marker_on_wall_mask)
        
        # Step 4: Classify markers as circle/square and determine their type
        marker_type = self.classify_marker(detected_markers)

        # Step 5: Draw the bounding box with label
        final_image = self.draw_bounding_boxes(scaled_image, detected_markers, marker_type)

        return detected_markers, final_image, marker_on_wall_mask

    def analyze_contours(self, marker_mask):
        """
        Analyzes contours for the detected markers.
        """
        contours, _ = cv2.findContours(marker_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_markers = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Skip small noise-like contours
                continue
            
            shape = self.classify_shape(contour)

            if shape == "Unknown":
                continue

            x, y, w, h = cv2.boundingRect(contour)
            detected_markers.append({
                "position": (x, y, w, h),
                "contour": contour,
                "shape": shape
            })

        return detected_markers

    def classify_marker(self, detected_markers):
        """
        Classifies markers as circles or squares, determines how many rows of circles there are,
        and identifies the packing station marker if it's a square.
        """
        circle_count = 0
        square_count = 0

        for obj in detected_markers:
            if obj['shape'] == "Circle":
                circle_count += 1
            elif obj['shape'] == "Square":
                square_count += 1

        # Classify the marker type
        if circle_count == 1:
            return "Row Marker 1"
        elif circle_count == 2:
            return "Row Marker 2"
        elif circle_count == 3:
            return "Row Marker 3"
        elif square_count > 0:
            return "Packing Station Marker"
        else:
            return "Unknown Marker"

    def classify_shape(self, contour):
        """
        Classifies the shape as either a circle or a square using contour properties.
        """
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        area = cv2.contourArea(contour)

        # Use circularity to classify as a circle
        circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0
        if circularity >= 0.85:
            return "Circle"
        elif 4 <= len(approx) <= 8:
            return "Square"
        else:
            return "Unknown"

    def draw_bounding_boxes(self, image, detected_markers, marker_type):
        """
        Draws bounding boxes around detected markers and adds a label in the middle of the box.
        """
        valid_markers = [obj for obj in detected_markers]
        if not valid_markers:
            return image  # No valid markers to process

        x_min = min([obj['position'][0] for obj in valid_markers])
        y_min = min([obj['position'][1] for obj in valid_markers])
        x_max = max([obj['position'][0] + obj['position'][2] for obj in valid_markers])
        y_max = max([obj['position'][1] + obj['position'][3] for obj in valid_markers])

        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        text_x = x_min + (x_max - x_min) // 2
        text_y = y_min - 10 if y_min - 10 > 10 else y_min + 30
        cv2.putText(image, marker_type, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image
