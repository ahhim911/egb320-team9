# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Inherit from DetectionBase
import os
import sys
# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class


class Wall(DetectionBase):
    def __init__(self):
        super().__init__("Wall")
    
    def find_wall(self, image, color_ranges):
        """
        Find the wall by creating a mask for the white color using color ranges.
        """
        # Extract the white color range for the wall from the color_ranges dictionary
        lower_hsv, upper_hsv = color_ranges['Wall']

        # Preprocess the image to create a mask for the white wall
        mask, scaled_image = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)

        # Analyze the contours of the detected wall
        self.analyze_contours(scaled_image, mask)

        return self.detected_objects, self.draw_contours(scaled_image), mask
    
    def analyze_contours(self, image, mask, min_area=1000):
        """
        Analyzes contours for the detected wall. Smooths the contour using convex hull.
        """
        # Get contours of the wall using RETR_EXTERNAL to focus on outermost contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Smooth the contour using convex hull
            hull = cv2.convexHull(contour)

            # Add the detected wall to the list of detected objects
            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "contour": hull,  # Store the convex hull of the contour
            })

    def draw_contours(self, image):
        """
        Draws the contours of the detected wall on the original image.
        """
        contour_image = image.copy()

        for obj in self.detected_objects:
            # Draw the wall contour (convex hull)
            contour = obj["contour"]
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

        return contour_image
