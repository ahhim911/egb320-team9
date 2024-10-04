import cv2
import numpy as np
import os
import sys

# Define the system path "../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Detection.detection import DetectionBase  # Import DetectionBase from detection.py
from Detection.range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class


class Item(DetectionBase):
    def __init__(self, real_item_width=0.03, focal_length=300):
        super().__init__("Item")
        self.real_item_width = real_item_width  # Real-world width of the item (in meters)
        self.focal_length = focal_length  # Focal length of the camera (in pixels)

    def find_item(self, image, color_ranges):
        """
        Detects items by using color and contour analysis.
        """
        # Define the HSV color range for the item
        lower_hsv, upper_hsv = color_ranges['Item']

        # Preprocess the image to create a mask for the item
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))
        # Analyze the contours of the detected item
        detected_items = self.analyze_contours(mask, scaled_image.shape[1])

        # If the item is detected, draw bounding boxes and labels
        if detected_items:
            final_image = self.draw_bounding_box(scaled_image, detected_items)
        else:
            final_image = scaled_image  # Return original image if no item is found

        return detected_items, final_image, mask

    def analyze_contours(self, mask, image_width, min_area=40):
        """
        Analyzes contours for the detected item and estimates distance and bearing.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Estimate distance using object width in pixels
            distance = DistanceEstimation.estimate_distance(w, self.real_item_width, self.focal_length)

            # Estimate bearing using the object's center X position
            object_center_x = x + (w // 2)
            bearing = DistanceEstimation.estimate_bearing(object_center_x, image_width)

            detected_objects.append({
                "position": (x, y, w, h),
                "distance": distance,  # Add distance information
                "bearing": bearing,    # Add bearing information
                "contour": contour,
            })

        return detected_objects

    def draw_bounding_box(self, image, detected_items):
        """
        Draws a bounding box around the detected items, adds a label and distance/bearing info.
        """
        for obj in detected_items:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw the bounding box around the item
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add the label with distance and bearing in the center of the bounding box
            label = f"Item: {distance:.2f}m, {bearing:.2f}deg"
            text_x = x + w // 2
            text_y = y + h // 2
            cv2.putText(image, label, (text_x - 80, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image
