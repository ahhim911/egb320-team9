# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Inherit from DetectionBase
import os
import sys

# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class


class Obstacle(DetectionBase):
    def __init__(self):
        super().__init__("Obstacle")

    def find_obstacle(self, image, color_ranges):
        """
        Detects obstacles by using color and contour analysis.
        """
        # Define the HSV color range for the obstacle
        lower_hsv, upper_hsv = color_ranges['Obstacle']

        # Preprocess the image to create a mask for the obstacle
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(5, 5), sigmaX=2, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(5, 5))

        # Analyze the contours of the detected obstacle
        detected_obstacles = self.analyze_contours(mask)

        # If the obstacle is detected, draw bounding boxes and labels
        if detected_obstacles:
            final_image = self.draw_bounding_box(scaled_image, detected_obstacles)
        else:
            final_image = scaled_image  # Return original image if no obstacle is found

        return detected_obstacles, final_image, mask

    def analyze_contours(self, mask, min_area=400):
        """
        Analyzes contours for the detected obstacle.
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

    def draw_bounding_box(self, image, detected_obstacles):
        """
        Draws a bounding box around the detected obstacles and adds a label.
        """
        for obj in detected_obstacles:
            x, y, w, h = obj['position']

            # Draw the bounding box around the obstacle
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add the label "Obstacle" in the center of the bounding box
            text_x = x + w // 2
            text_y = y + h // 2
            cv2.putText(image, "Obstacle", (text_x - 80, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image
