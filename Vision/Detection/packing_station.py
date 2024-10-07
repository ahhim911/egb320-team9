import cv2
import numpy as np
from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class PackingStationRamp(DetectionBase):
    def __init__(self, real_station_width=0.8, focal_length=300, homography_matrix=None, draw=False):
        """
        Initializes the PackingStationRamp class with optional parameters.
        
        Args:
        - real_station_width: Real-world width of the packing station (in meters).
        - focal_length: Focal length of the camera (in pixels).
        - homography_matrix: Matrix used for perspective transformation.
        - draw: Flag to enable or disable drawing bounding boxes and labels.
        """
        super().__init__("Ramp")
        self.real_station_width = real_station_width
        self.focal_length = focal_length
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)
        self.draw = draw  # Flag to control drawing

    def find_packing_station_ramp(self, image, color_ranges):
        """
        Detects the packing station ramp using color and contour analysis.

        Args:
        - image: Input image from the camera.
        - color_ranges: Dictionary with HSV color ranges for ramp detection.

        Returns:
        - data_list: List of detected ramp "data" (bearing and distance).
        - final_image: Processed image with or without bounding boxes and labels.
        - mask: Binary mask representing detected ramp.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # 2. Detect Ramp
        detected_ramp = self._detect_ramp(mask)

        # 3. Extract Data (Distance, Bearing)
        data_list = [obj["data"] for obj in detected_ramp]

        # 4. Draw if enabled
        final_image = self._draw_if_enabled(image, detected_ramp)
        print("RAMP DATA ", data_list)

        return data_list, final_image, mask

    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image using defined color ranges.
        """
        lower_hsv, upper_hsv = color_ranges['Ramp']
        mask, _ = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        return mask

    def _detect_ramp(self, mask, min_area=1000):
        """
        Analyzes contours to detect the ramp and estimates their distance and bearing.

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
            distance = self.distance_estimator.estimate_homography_distance((x, y, w, h))
            object_center_x = x + (w // 2)
            bearing = self.distance_estimator.estimate_bearing(object_center_x)

            # Store position, distance, and bearing with "data"
            detected_objects.append({
                "position": (x, y, w, h),
                "distance": distance,
                "bearing": bearing,
                "contour": contour,
                "data": [distance,bearing]  # Add the "data" list for easy access
            })

        return detected_objects

    def _draw_if_enabled(self, image, detected_ramp):
        """
        Draw bounding boxes and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return the original image if drawing is disabled

        return self._draw_bounding_box(image, detected_ramp)

    def _draw_bounding_box(self, image, detected_ramp):
        """
        Draws bounding boxes and labels for detected ramps.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_ramp: List of detected ramp objects with positions, distances, and bearings.

        Returns:
        - The image with bounding boxes and labels drawn.
        """
        local_image = image.copy()
        for obj in detected_ramp:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw bounding box
            cv2.rectangle(local_image, (x, y), (x + w, y + h), (0, 255, 255), 2)

            # Add label for distance and bearing
            label = f"{distance:.2f}m, {bearing:.2f}deg"
            cv2.putText(local_image, label, (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return local_image
