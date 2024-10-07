import cv2
import numpy as np
from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Item(DetectionBase):
    def __init__(self, real_item_width=0.03, focal_length=300, draw=False):
        """
        Initializes the Item class with optional parameters.

        Args:
        - real_item_width: Real-world width of the item (in meters).
        - focal_length: Focal length of the camera (in pixels).
        - draw: Flag to enable or disable drawing bounding boxes and labels.
        """
        super().__init__("Item")
        self.real_item_width = real_item_width
        self.focal_length = focal_length
        self.distance_estimator = DistanceEstimation(focal_length=focal_length)
        self.draw = draw  # Flag to control drawing

    def find_item(self, image, color_ranges):
        """
        Detects items using color and contour analysis.

        Args:
        - image: Input image from the camera.
        - color_ranges: Dictionary with HSV color ranges for item detection.

        Returns:
        - data_list: List of detected item "data" (bearing and distance).
        - final_image: Processed image with or without bounding boxes and labels.
        - mask: Binary mask representing detected items.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # 2. Detect Items
        detected_items = self._detect_items(mask)

        # 3. Extract Data (Bearing, Distance)
        data_list = [obj["data"] for obj in detected_items]

        # 4. Draw if enabled
        final_image = self._draw_if_enabled(image, detected_items)
        print("ITEM DATA: ", data_list)

        return data_list, final_image, mask

    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image using defined color ranges.
        """
        lower_hsv, upper_hsv = color_ranges['Item']
        mask, _ = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        return mask

    def _detect_items(self, mask, min_area=40):
        """
        Analyzes contours to detect items and estimates their distance and bearing.

        Args:
        - mask: Binary mask from preprocessing.
        - min_area: Minimum area for contour detection.

        Returns:
        - List of detected objects with position, distance, and bearing.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            distance = self.distance_estimator.estimate_distance(w, self.real_item_width)
            object_center_x = x + (w // 2)
            bearing = self.distance_estimator.estimate_bearing(object_center_x)

            # Store position, distance, and bearing with "data"
            detected_objects.append({
                "position": (x, y, w, h),
                "distance": distance,
                "bearing": bearing,
                "contour": contour,
                "data": [distance,bearing]
            })

        return detected_objects

    def _draw_if_enabled(self, image, detected_items):
        """
        Draw bounding boxes and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return the original image if drawing is disabled

        return self._draw_bounding_box(image, detected_items)

    def _draw_bounding_box(self, image, detected_items):
        """
        Draws bounding boxes and labels for detected items.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_items: List of detected item objects with positions, distances, and bearings.

        Returns:
        - The image with bounding boxes and labels drawn.
        """
        local_image = image.copy()
        for obj in detected_items:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw bounding box
            cv2.rectangle(local_image, (x, y), (x + w, y + h), (0, 165, 255), 2)

            # Add label for distance and bearing
            label = f"{distance:.2f}m, {bearing:.2f}deg"
            cv2.putText(local_image, label, (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return local_image
