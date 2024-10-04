import cv2
import numpy as np
from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Obstacle(DetectionBase):
    def __init__(self, real_obstacle_width=0.05, focal_length=300, homography_matrix=None, draw=False):
        """
        Initializes the Obstacle class with optional parameters.
        
        Args:
        - real_obstacle_width: Real-world width of the obstacle (in meters).
        - focal_length: Focal length of the camera (in pixels).
        - homography_matrix: Matrix used for perspective transformation.
        - draw: Flag to enable or disable drawing bounding boxes and labels.
        """
        super().__init__("Obstacle")
        self.real_obstacle_width = real_obstacle_width
        self.focal_length = focal_length
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)
        self.draw = draw  # Flag to control drawing

    def find_obstacle(self, image, color_ranges):
        """
        Detects obstacles using color and contour analysis.

        Args:
        - image: Input image from the camera.
        - color_ranges: Dictionary with HSV color ranges for obstacle detection.

        Returns:
        - data_list: List of detected obstacle "data" (bearing and distance).
        - final_image: Processed image with or without bounding boxes and labels.
        - mask: Binary mask representing detected obstacles.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # 2. Detect Obstacles
        detected_obstacles = self._detect_obstacles(mask)

        # 3. Extract Data (Bearing, Distance)
        data_list = [obj["data"] for obj in detected_obstacles]
        #print("OBST DATA ", data_list)

        # 4. Draw if enabled
        final_image = self._draw_if_enabled(image, detected_obstacles)

        return data_list, final_image, mask

    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image using defined color ranges.
        """
        lower_hsv, upper_hsv = color_ranges['Obstacle']
        mask, scaled_image = Preprocessing.preprocess(image,lower_hsv=lower_hsv,upper_hsv=upper_hsv)
        return mask

    def _detect_obstacles(self, mask, min_area=400):
        """
        Analyzes contours to detect obstacles and estimates their distance and bearing.

        Args:
        - mask: Binary mask from preprocessing.
        - image_width: Width of the input image.
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
                "data": [bearing, distance]  # Add the "data" list for easy access
            })

        return detected_objects

    def _draw_if_enabled(self, image, detected_obstacles):
        """
        Draw bounding boxes and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return the original image if drawing is disabled

        return self._draw_bounding_box(image, detected_obstacles)

    def _draw_bounding_box(self, image, detected_obstacles):
        """
        Draws bounding boxes and labels for detected obstacles.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_obstacles: List of detected obstacle objects with positions, distances, and bearings.

        Returns:
        - The image with bounding boxes and labels drawn.
        """
        local_image = image.copy()
        for obj in detected_obstacles:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw bounding box
            cv2.rectangle(local_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add label for distance and bearing
            label = f"{distance:.2f}m, {bearing:.2f}deg"
            cv2.putText(local_image, label, (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return local_image
