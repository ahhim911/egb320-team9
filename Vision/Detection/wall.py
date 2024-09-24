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
        Detect the wall based on HSV color range, generate a filled mask, and return contours.
        """
        lower_hsv, upper_hsv = color_ranges['Wall']
        mask, scaled_image = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)

        # Analyze contours for the wall and generate a filled mask
        detected_walls = self.analyze_contours(mask)
        filled_wall_mask = self.create_filled_wall_mask(mask, detected_walls)

        return detected_walls, filled_wall_mask, mask

    def analyze_contours(self, mask, min_area=800, solidity_threshold=0.5):
        """
        Analyzes contours for the detected wall, filtering by area and solidity.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_walls = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)

            solidity = float(area) / hull_area if hull_area > 0 else 0
            if solidity < solidity_threshold:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            detected_walls.append({
                "position": (x, y, w, h),
                "contour": contour
            })

        return detected_walls

    def create_filled_wall_mask(self, mask, detected_walls):
        """
        Create a filled mask from the wall contours.
        """
        filled_wall_mask = np.zeros_like(mask)
        for wall in detected_walls:
            cv2.drawContours(filled_wall_mask, [wall["contour"]], -1, 255, thickness=cv2.FILLED)
        return filled_wall_mask