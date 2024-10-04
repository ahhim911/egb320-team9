import cv2
import numpy as np
from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Wall(DetectionBase):
    def __init__(self, focal_length=300, homography_matrix=None, draw=True):
        """
        Initializes the Wall class with optional parameters.
        
        Args:
        - focal_length: Focal length of the camera (in pixels).
        - homography_matrix: Matrix used for perspective transformation.
        - draw: Flag to enable or disable drawing bounding boxes and labels.
        """
        super().__init__("Wall")
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)
        self.focal_length = focal_length
        self.draw = draw  # Flag to control drawing

    def find_wall(self, image, RGBframe, color_ranges):
        """
        Detects walls using color and contour analysis.

        Args:
        - image: Input image from the camera.
        - color_ranges: Dictionary with HSV color ranges for wall detection.

        Returns:
        - data_list: List of detected wall "data" (bearing and distance to the bottom center).
        - filled_wall_mask: Binary mask with filled wall contours.
        - mask: Binary mask representing detected walls.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # 2. Detect Walls
        detected_walls = self._detect_walls(mask)

        # 3. Extract Data (Bearing, Distance to Bottom Center)
        data_list = [obj["data"] for obj in detected_walls]

        # 4. Create filled wall mask
        filled_wall_mask = self._create_filled_wall_mask(mask, detected_walls)

        # 5. Draw bounding boxes if enabled
        final_image = self._draw_if_enabled(RGBframe, detected_walls)

        #print("WALL DATA: ", data_list)

        return data_list, final_image, filled_wall_mask

    #def _preprocess_image(self, image, color_ranges):
    #    """
    #    Preprocess the image using defined color ranges.
    #    """
    #    lower_hsv, upper_hsv = color_ranges['Wall']
    #    mask, _ = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
    #    return mask
    
    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image by converting it to grayscale and applying thresholding.
        """
        # Convert image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply a threshold to the grayscale image
        _, mask = cv2.threshold(gray_image, 175, 255, cv2.THRESH_BINARY)

        return mask

    def _detect_walls(self, mask, min_area=800, solidity_threshold=0.5):
        """
        Analyzes contours to detect walls and estimates their distance and bearing.

        Args:
        - mask: Binary mask from preprocessing.
        - min_area: Minimum area for contour detection.
        - solidity_threshold: Minimum solidity to filter out non-solid contours.

        Returns:
        - List of detected objects with position, distance to bottom center, and bearing.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

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

            # Estimate homography distance and bearing for the bottom center
            distance = self.distance_estimator.estimate_homography_distance((x, y, w, h))
            bottom_center_x = x + (w // 2)
            bearing = self.distance_estimator.estimate_bearing(bottom_center_x)

            # Store position, distance, and bearing with "data"
            detected_objects.append({
                "position": (x, y, w, h),
                "distance": distance,
                "bearing": bearing,
                "contour": contour,
                "data": [distance, bearing]  # Data for easy access
            })

        return detected_objects

    def _create_filled_wall_mask(self, mask, detected_walls):
        """
        Create a filled mask from the wall contours.

        Args:
        - mask: Binary mask of the walls.
        - detected_walls: List of detected walls.

        Returns:
        - filled_wall_mask: Binary mask with filled wall contours.
        """
        filled_wall_mask = np.zeros_like(mask)
        for wall in detected_walls:
            cv2.drawContours(filled_wall_mask, [wall["contour"]], -1, 255, thickness=cv2.FILLED)
        return filled_wall_mask

    def _draw_if_enabled(self, image, detected_walls):
        """
        Draw bounding boxes and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return the original image if drawing is disabled

        return self._draw_bounding_box(image, detected_walls)

    def _draw_bounding_box(self, image, detected_walls):
        """
        Draws bounding boxes and labels for detected walls.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_walls: List of detected wall objects with positions, distances, and bearings.

        Returns:
        - The image with bounding boxes and labels drawn.
        """
        for obj in detected_walls:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 255), 2)

            # Add label for distance and bearing
            label = f"{distance:.2f}m, {bearing:.2f}deg"
            cv2.putText(image, label, (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return image
