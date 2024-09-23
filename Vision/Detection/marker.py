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

    def find_marker(self, image, detected_walls, color_ranges):
        """
        Find markers only within the wall's bounding box, classify them, and draw a bounding box with a label.
        """
        lower_hsv, upper_hsv = color_ranges['Marker']
        marker_mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))
    
        # Get marker contours
        marker_contours, _ = cv2.findContours(marker_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_markers = []
        
        # Detect markers only within the bounding box of the wall
        for wall_obj in detected_walls:
            wall_x, wall_y, wall_w, wall_h = wall_obj["position"]
            for marker_contour in marker_contours:
                x, y, w, h = cv2.boundingRect(marker_contour)
                # Ensure marker is within the wall's bounding box
                if wall_x <= x + (w // 2) <= wall_x + wall_w and wall_y <= y + (h // 2) <= wall_y + wall_h:
                    detected_markers.append({
                        "position": (x, y, w, h),
                        "contour": marker_contour
                    })
        
        # Classify markers as circle/square and determine their type
        marker_type = self.classify_marker(detected_markers)
        
        # Draw the bounding box with label
        final_image = self.draw_bounding_box(scaled_image, detected_markers, marker_type)

        return detected_markers, final_image, marker_mask

    def classify_marker(self, detected_markers):
        """
        Classifies markers as circles or squares, determines how many rows of circles there are,
        and identifies the packing station marker if it's a square.
        """
        circle_count = 0
        square_count = 0

        for obj in detected_markers:
            contour = obj['contour']
            shape = self.classify_shape(contour)

            # Debugging information for troubleshooting
            print(f"Detected shape: {shape}")

            if shape == "Circle":
                circle_count += 1
            elif shape == "Square":
                square_count += 1

        # Classify the marker type
        if square_count > 0:
            return "Packing Station Marker"  # If there's a square, it's the packing station
        elif circle_count == 1:
            return "Row Marker 1"
        elif circle_count == 2:
            return "Row Marker 2"
        elif circle_count == 3:
            return "Row Marker 3"
        else:
            return "Unknown Marker"

    def classify_shape(self, contour):
        """
        Classifies the shape as either a circle or a square using contour properties.
        """
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)  # Approximating the shape (more relaxed)
        area = cv2.contourArea(contour)

        # Use circularity to classify as a circle
        circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0
        print(f"Circularity: {circularity}, Vertices: {len(approx)}")  # Debugging info

        # Threshold for circular shapes
        if circularity >= 0.9:  # Adjusting the threshold for circularity
            return "Circle"
        elif 4 <= len(approx) <= 7:  # Allow some leniency for squares
            return "Square"
        else:
            return "Unknown"

    def draw_bounding_box(self, image, detected_markers, marker_type):
        """
        Draws a bounding box around all detected markers and adds the appropriate label text.
        """
        if not detected_markers:
            return image

        x_min = min([obj['position'][0] for obj in detected_markers])
        y_min = min([obj['position'][1] for obj in detected_markers])
        x_max = max([obj['position'][0] + obj['position'][2] for obj in detected_markers])
        y_max = max([obj['position'][1] + obj['position'][3] for obj in detected_markers])

        # Draw the bounding box around all markers
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        # Add the text in the center of the bounding box
        text_x = x_min + (x_max - x_min) // 2
        text_y = y_min - 10 if y_min - 10 > 10 else y_min + 30  # Ensure the text is visible

        cv2.putText(image, marker_type, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for obj in detected_markers:
            # Draw the marker contours
            contour = obj["contour"]
            cv2.drawContours(image, [contour], -1, (255, 0, 0), 2)

        return image
