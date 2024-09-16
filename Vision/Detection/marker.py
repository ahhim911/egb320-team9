# Import the necessary modules
import cv2
import numpy as np
from detection import DetectionBase  # Import DetectionBase from detection.py
import os
import sys
# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Preprocessing.preprocessing import Preprocessing
from wall import Wall  # Import the Wall detection class


class Marker(DetectionBase):
    def __init__(self):
        super().__init__("Marker")
        self.wall_detector = Wall()  # Initialize the Wall detector
    
    def find_marker(self, image, color_ranges):
        """
        Find the marker by creating a mask based on the color range and analyzing contours.
        Only detect markers if they are against a white wall.
        """
        # First, detect the wall and get the wall mask
        wall_frame, wall_mask = self.wall_detector.find_wall(image, color_ranges)
        
        # Now, preprocess the image to detect markers
        lower_hsv, upper_hsv = color_ranges['Marker']
        marker_mask, scaled_image = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)

        # Combine the marker mask with the wall mask to ensure markers are only detected on the white wall
        valid_marker_mask = cv2.bitwise_and(marker_mask, wall_mask)

        # Analyze contours only on the valid markers (i.e., markers that are on the white wall)
        self.analyze_contours(scaled_image, valid_marker_mask)
        
        # Process each detected marker to classify as circle or square
        for obj in self.detected_objects:
            shape = self.classify_shape(obj["contour"])
            obj["shape"] = shape  # Store the shape in the object
            
            # Check if the marker is in front of the white wall (already filtered by wall mask)
            obj["is_valid"] = True  # Since we've already filtered by the wall, they are valid

        return self.detected_objects, self.draw_contours(scaled_image), valid_marker_mask

    def analyze_contours(self, image, mask, min_area=150):
        """
        Analyzes contours for markers detected on the wall.
        Additionally, smooths the contour using convex hull.
        """
        # Get contours of the markers using RETR_EXTERNAL to focus on outermost contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Smooth the contour using convex hull
            hull = cv2.convexHull(contour)

            # Add the detected marker to the list of detected objects
            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "contour": hull,  # Store the convex hull of the contour
                "perimeter": cv2.arcLength(contour, True)  # Store the perimeter
            })

    def classify_shape(self, contour):
        """
        Classify the shape of the contour as either 'Circle' or 'Square'.
        Uses aspect ratio, circularity, and number of vertices.
        """
        # Calculate perimeter and area
        perimeter = cv2.arcLength(contour, True)
        area = cv2.contourArea(contour)

        # Calculate circularity
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

        # Use approxPolyDP to count the number of vertices
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Aspect ratio check (for square)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h

        # Check if it's a circle based on circularity
        if circularity > 0.8:
            return "Circle"

        # Check if it's a square based on number of vertices and aspect ratio
        if len(approx) == 4 and 0.9 <= aspect_ratio <= 1.1:
            return "Square"

        return "Unknown"

    def draw_contours(self, image):
        """
        Draw approximated shapes based on detected objects.
        """
        contour_image = image

        for obj in self.detected_objects:
            # Only draw valid objects that are on the white wall
            if not obj.get("is_valid", True):
                continue

            # Draw the smoothed contour
            contour = obj["contour"]
            shape = obj["shape"]
            
            # Draw the contour
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

            # Label the shape
            x, y, w, h = obj["position"]
            cv2.putText(contour_image, shape, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return contour_image
