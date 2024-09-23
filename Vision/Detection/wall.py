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
        lower_hsv, upper_hsv = color_ranges['Wall']

        # Step 1: Preprocess the image
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))

        # Step 4: Analyze contours for the wall using the cleaned-up edges
        self.analyze_contours(scaled_image, mask)

        return self.detected_objects, self.draw_contours(scaled_image), mask

    def analyze_contours(self, image, mask, min_area=1000, solidity_threshold=0.7):
        """
        Analyzes contours for the detected wall. Filters contours based on area and solidity.
        """
        # Get contours of the wall using RETR_EXTERNAL to focus on outermost contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            # Calculate the convex hull and its area
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)

            # Compute solidity (area / hull_area)
            if hull_area > 0:
                solidity = float(area) / hull_area
            else:
                solidity = 0

            # Filter out contours with low solidity
            if solidity < solidity_threshold:
                continue  # Skip contours with low solidity

            x, y, w, h = cv2.boundingRect(contour)

            # Add the detected wall to the list of detected objects
            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "solidity": solidity,
                "contour": contour,  # Store the convex hull of the contour
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
