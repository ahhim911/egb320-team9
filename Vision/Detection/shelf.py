# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Import DetectionBase from detection.py
import os
import sys
# define the system path "../"
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
        mask,scaled_image = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        self.analyze_contours(image, mask)
        #image, corners = self.detect_corners(image)
        for obj in self.detected_objects:
            x, y, w, h = obj["position"]
            range_, bearing = self.calculate_range_and_bearing(x, y, w, h)
            obj["range"] = range_
            obj["bearing"] = bearing

        return self.detected_objects, self.draw_contours(scaled_image), mask
        
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
                "contour": hull  # Store the convex hull as the smoothed contour
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
    

    def detect_corners(self, image):
        # Convert image to grayscale for corner detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use Shi-Tomasi corner detection (Good Features to Track)
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=10, qualityLevel=0.01, minDistance=10)
        corners = np.int0(corners)

        # Draw the detected corners on the image
        for corner in corners:
            x, y = corner.ravel()
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)

        return image, corners
