# Import the necessary modules
import cv2
import numpy as np

from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Marker(DetectionBase):
    def __init__(self, real_marker_width=0.07, focal_length=300):
        super().__init__("Marker")
        self.real_marker_width = real_marker_width  # Real-world width of the marker in meters
        self.focal_length = focal_length  # Focal length of the camera in pixels

    def find_marker(self, image, filled_wall_mask, color_ranges):
        """
        Detect markers within the wall's bounding box using a bitwise AND to isolate markers on walls.
        """
        lower_hsv, upper_hsv = color_ranges['Marker']
        
        # Preprocess image for marker detection
        marker_mask, scaled_image = Preprocessing.preprocess(
            image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))

        # Use bitwise AND to keep only markers on the wall
        marker_on_wall_mask = cv2.bitwise_and(marker_mask, filled_wall_mask)

        # Analyze contours for the markers
        detected_markers = self.analyze_contours(marker_on_wall_mask)
        
        # Classify markers and determine their type
        marker_type = self.classify_marker(detected_markers)

        # Calculate distance and bearing for each marker
        for marker in detected_markers:
            marker_width = marker['position'][2]  # Width of the bounding box
            marker_center_x = marker['position'][0] + (marker_width // 2)

            # Estimate distance and bearing using DistanceEstimation
            marker['distance'] = DistanceEstimation.estimate_distance(
                marker_width, self.real_marker_width, self.focal_length
            )
            marker['bearing'] = DistanceEstimation.estimate_bearing(
                marker_center_x, image.shape[1]/2
            )
            #print(image.shape[0])

        # Draw the bounding box with label
        final_image = self.draw_bounding_boxes(scaled_image, detected_markers, marker_type)

        return detected_markers, final_image, marker_on_wall_mask

    def analyze_contours(self, mask):
        """
        Analyzes contours for the detected markers, filters small noise.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_markers = []

        for contour in contours:
            if cv2.contourArea(contour) < 100:  # Skip small noise-like contours
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
        Classifies markers as circles or squares and determines their type.
        """
        circle_count, square_count = 0, 0

        for marker in detected_markers:
            if marker['shape'] == "Circle":
                circle_count += 1
            elif marker['shape'] == "Square":
                square_count += 1

        # Classify the marker type based on the counts of circles and squares
        if square_count > 0:
            return "Packing Station Marker"
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
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)  # Approximate the contour shape
        area = cv2.contourArea(contour)

        # Use circularity to classify as a circle
        circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter > 0 else 0

        if circularity >= 0.85:  # Threshold for circular shapes
            return "Circle"
        elif 4 <= len(approx) <= 7:  # Threshold for square-like shapes
            return "Square"
        else:
            return "Unknown"

    def draw_bounding_boxes(self, image, detected_markers, marker_type):
        """
        Draws bounding boxes around detected markers and adds a label in the middle of the box.
        Also calculates and displays the average distance and bearing if there are multiple markers.
        """
        if not detected_markers:
            return image  # Return original image if no valid markers are found

        # Calculate the overall bounding box for all markers
        x_min = min([marker['position'][0] for marker in detected_markers])
        y_min = min([marker['position'][1] for marker in detected_markers])
        x_max = max([marker['position'][0] + marker['position'][2] for marker in detected_markers])
        y_max = max([marker['position'][1] + marker['position'][3] for marker in detected_markers])

        # Calculate the average distance and bearing for multiple markers
        distances = [marker.get('distance', 0) for marker in detected_markers if marker.get('distance') is not None]
        bearings = [marker.get('bearing', 0) for marker in detected_markers if marker.get('bearing') is not None]

        if distances:
            avg_distance = sum(distances) / len(distances)
        else:
            avg_distance = "Unknown"

        if bearings:
            avg_bearing = sum(bearings) / len(bearings)
        else:
            avg_bearing = "Unknown"

        # Draw the overall bounding box around all markers
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        # Add marker type, average distance, and average bearing label to the image
        text_x = 40  # Fixed x position for text
        text_y = image.shape[0]-50  # Fixed y position for text
        cv2.putText(image, f"{marker_type}",
                    (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(image, f"Avg Dist: {avg_distance:.2f}m | Avg Bearing: {avg_bearing:.2f}deg",
                    (text_x, text_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Optionally, draw individual bounding boxes and display distances for each marker
        for marker in detected_markers:
            x, y, w, h = marker['position']

            # Draw bounding box around each marker
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display the individual marker distance and bearing
            distance = marker.get('distance', 'Unknown')
            bearing = marker.get('bearing', 'Unknown')
            #cv2.putText(image, f"Dist: {distance:.2f}m | Bearing: {bearing:.2f}°", (x + w // 2 - 50, y + h // 2),
                        #cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image

