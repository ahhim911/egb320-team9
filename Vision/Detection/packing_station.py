# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Inherit from DetectionBase
import os
import sys

# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class


class PackingStationRamp(DetectionBase):
    def __init__(self):
        super().__init__("PackingStationRamp")

    def find_packing_station_ramp(self, image, color_ranges):
        """
        Detects the packing station ramp by using color and contour analysis.
        """
        # Define the HSV color range for the ramp
        lower_hsv, upper_hsv = color_ranges['PackingStationRamp']

        # Preprocess the image to create a mask for the ramp
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(5, 5), sigmaX=2, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(5, 5))

        # Analyze the contours of the detected ramp
        detected_ramp = self.analyze_contours(mask)

        # If the ramp is detected, draw bounding boxes and labels
        if detected_ramp:
            final_image = self.draw_bounding_box(scaled_image, detected_ramp)
        else:
            final_image = scaled_image  # Return original image if no ramp is found

        return detected_ramp, final_image, mask

    def analyze_contours(self, mask, min_area=1000):
        """
        Analyzes contours for the detected ramp.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)
            detected_objects.append({
                "position": (x, y, w, h),
                "contour": contour,
            })

        return detected_objects

    def draw_bounding_box(self, image, detected_ramp):
        """
        Draws a bounding box around the detected packing station ramp and adds a label.
        """
        for obj in detected_ramp:
            x, y, w, h = obj['position']

            # Draw the bounding box around the ramp
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add the label "Packing Station Ramp" in the center of the bounding box
            text_x = x + w // 2
            text_y = y + h // 2
            cv2.putText(image, "Packing Station Ramp", (text_x - 80, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image
