# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Import DetectionBase from detection.py
import os
import sys
# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing


class Shelf(DetectionBase):
    def __init__(self):
        super().__init__("Shelf")
    
    def find_shelf(self, image, color_ranges):
        """
        Find the shelf by creating a mask based on the color range and analyzing contours.
        """
        lower_hsv, upper_hsv = color_ranges['Shelf']
        mask, scaled_image = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        self.analyze_contours(scaled_image, mask)
        
        # Get corners directly from contours
        contour_image, corners = self.get_contour_corners(scaled_image)
        
        # Focus on a specific corner (e.g., bottom-right corner)
        specific_corner = self.get_specific_corner(corners, criterion="bottom-right")
        
        # Draw the specific corner
        if specific_corner is not None:
            x, y = specific_corner
            cv2.circle(contour_image, (x, y), 10, (255, 0, 0), -1)  # Blue circle for the specific corner
        
        for obj in self.detected_objects:
            x, y, w, h = obj["position"]
            range_, bearing = self.calculate_range_and_bearing(x, y, w, h)
            obj["range"] = range_
            obj["bearing"] = bearing

        return self.detected_objects, self.draw_contours(contour_image), mask
        
    def analyze_contours(self, image, mask, min_area=800):
        """
        Overrides DetectionBase.analyze_contours to provide more specific logic for shelves.
        The contours for objects sitting on the shelf should be filtered out by applying geometric constraints.
        Additionally, smooth out the contour using convex hull.
        """
        # Get only outermost contours using RETR_EXTERNAL
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Smooth the contour using convex hull
            hull = cv2.convexHull(contour)

            # Smooth the contour using cv2.approxPolyDP to reduce the number of points
            epsilon = 0.001 * cv2.arcLength(contour, True)  # Adjust epsilon for smoothness
            smoothed_contour = cv2.approxPolyDP(contour, epsilon, True)

            # Add the detected shelf to the list of detected objects with the smoothed contour
            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "contour": smoothed_contour  # Store the approximated contour with corner points
            })

    def draw_contours(self, image):
        """
        Draw approximated shapes based on detected objects.
        """
        contour_image = image

        for obj in self.detected_objects:
            # Draw the smoothed contour
            contour = obj["contour"]
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

        return contour_image

    def get_contour_corners(self, image):
        """
        Get corners directly from the contour using cv2.approxPolyDP (contour approximation).
        """
        contour_image = image.copy()

        all_corners = []

        for obj in self.detected_objects:
            # Get the approximated contour with fewer points (representing corners)
            contour = obj["contour"]
            
            # Draw circles at each corner point and store them
            for point in contour:
                x, y = point.ravel()
                all_corners.append((x, y))  # Store the corner points
                cv2.circle(contour_image, (x, y), 5, (0, 0, 255), -1)

        return contour_image, all_corners

    def get_specific_corner(self, corners, criterion="bottom-right"):
        """
        Get a specific corner based on the given criterion (e.g., bottom-right, top-left).
        """
        if len(corners) == 0:
            return None

        # Initialize the specific corner with the first corner
        specific_corner = corners[0]

        if criterion == "bottom-right":
            # Look for the corner with the largest x and y values
            specific_corner = max(corners, key=lambda c: (c[0], c[1]))
        elif criterion == "top-left":
            # Look for the corner with the smallest x and y values
            specific_corner = min(corners, key=lambda c: (c[0], c[1]))

        return specific_corner
