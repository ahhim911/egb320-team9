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
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(5, 5), sigmaX=2, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(5, 5))

        # Step 2: Analyze contours for the wall
        self.analyze_contours(scaled_image, mask)

        # Step 3: Create a filled wall mask using the contours
        filled_wall_mask = np.zeros_like(mask)
        if self.detected_objects:
            for obj in self.detected_objects:
                cv2.drawContours(filled_wall_mask, [obj["contour"]], -1, 255, thickness=cv2.FILLED)
            
            # Optionally apply smoothing for consistency
            #filled_wall_mask = cv2.GaussianBlur(filled_wall_mask, (5, 5), sigmaX=2)
        
        return self.detected_objects, filled_wall_mask, mask

    def analyze_contours(self, image, mask, min_area=800, solidity_threshold=0.1):
        """
        Analyzes contours for the detected wall. Filters contours based on area and solidity.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            # Early bounding box filtering based on minimum area
            x, y, w, h = cv2.boundingRect(contour)
            if w * h < min_area:  # Skip small bounding boxes early
                continue

            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            # Calculate the convex hull and its area
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)

            # Compute solidity (area / hull_area)
            solidity = float(area) / hull_area if hull_area > 0 else 0

            # Filter out contours with low solidity
            if solidity < solidity_threshold:
                continue

            # If all conditions are met, save the contour
            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "solidity": solidity,
                "contour": contour
            })

    def draw_contours(self, image):
        """
        Draws the contours of the detected wall on the original image.
        """
        contour_image = image.copy()
        for obj in self.detected_objects:
            contour = obj["contour"]
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

        return contour_image
