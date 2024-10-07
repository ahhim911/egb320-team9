import cv2
import numpy as np
from collections import Counter

from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class

class Marker(DetectionBase):
    def __init__(self, real_marker_width=0.07, focal_length=300, draw=True):
        super().__init__("Marker")
        self.real_marker_width = real_marker_width  # Real-world width of the marker in meters
        self.focal_length = focal_length  # Focal length of the camera in pixels
        self.distance_estimator = DistanceEstimation(focal_length=focal_length)
        self.draw = draw  # Flag to control drawing

    def find_marker(self, image, filled_wall_mask, color_ranges):
        """
        Detect markers using color and contour analysis.

        Args:
        - image: Input image from the camera.
        - color_ranges: Dictionary with HSV color ranges for marker detection.

        Returns:
        - detected_markers: List of detected marker objects with positions, distances, and bearings.
        - final_image: Processed image with or without bounding boxes and labels.
        - mask: Binary mask representing detected markers.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # Use bitwise AND to keep only markers on the wall
        marker_on_wall_mask = cv2.bitwise_and(mask, filled_wall_mask)

        # 2. Detect Markers and Calculate Properties
        detected_markers = self._detect_and_classify_markers(marker_on_wall_mask)

        if not detected_markers:
            return [], image, mask  # Return early if no markers detected

        # 3. Classify Markers based on counts
        marker_type = self._classify_marker_type(detected_markers)

        # 4. Draw if enabled
        final_image = self._draw_if_enabled(image, detected_markers, marker_type)

        return detected_markers, final_image, marker_on_wall_mask

    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image using defined color ranges.
        """
        lower_hsv, upper_hsv = color_ranges['Marker']
        mask, _ = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        return mask

    def _detect_and_classify_markers(self, mask, min_area=100):
        """
        Detects markers, classifies shapes, and calculates distances and bearings.

        Args:
        - mask: Binary mask from preprocessing.
        - min_area: Minimum area for contour detection.

        Returns:
        - detected_markers: List of detected marker objects with positions, shapes, distances, and bearings.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_markers = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * (area / (perimeter ** 2)) # type: ignore

            # Classify shape
            if circularity >= 0.85:
                shape = "Circle"
            else:
                # Approximate the contour
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                if 4 <= len(approx) <= 7:
                    shape = "Square"
                else:
                    continue  # Skip unknown shapes

            x, y, w, h = cv2.boundingRect(contour)
            marker_width = w  # Use width of bounding box
            marker_center_x = x + (w / 2)

            # Estimate distance and bearing
            distance = self.distance_estimator.estimate_distance(marker_width, self.real_marker_width)
            bearing = self.distance_estimator.estimate_bearing(marker_center_x)

            detected_markers.append({
                "position": (x, y, w, h),
                "contour": contour,
                "shape": shape,
                "distance": distance,
                "bearing": bearing
            })

        return detected_markers

    def _classify_marker_type(self, detected_markers):
        """
        Classifies markers based on the counts of circles and squares.

        Args:
        - detected_markers: List of detected marker objects.

        Returns:
        - marker_type: String indicating the type of marker detected.
        """
        shape_counts = Counter(marker['shape'] for marker in detected_markers)
        circle_count = shape_counts.get("Circle", 0)
        square_count = shape_counts.get("Square", 0)

        # Classify the marker type based on the counts of circles and squares
        if square_count > 0:
            return "Packing Station Marker"
        elif circle_count == 1:
            return "Row Marker 1"
        elif circle_count == 2:
            return "Row Marker 2"
        elif circle_count == 3:
            return "Row Marker 3"
        else:
            return "Unknown Marker"

    def _draw_if_enabled(self, image, detected_markers, marker_type):
        """
        Draw bounding boxes and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return the original image if drawing is disabled

        return self._draw_bounding_box(image, detected_markers, marker_type)

    def _draw_bounding_box(self, image, detected_markers, marker_type):
        """
        Draws bounding boxes around detected markers and adds a label with average distance and bearing.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_markers: List of detected marker objects.
        - marker_type: String indicating the type of marker detected.

        Returns:
        - image: The image with bounding boxes and labels drawn.
        """
        # Avoid copying image if possible
        x_coords = []
        y_coords = []
        distances = []
        bearings = []

        for marker in detected_markers:
            x, y, w, h = marker['position']
            distance = marker['distance']
            bearing = marker['bearing']

            # Collect positions for overall bounding box
            x_coords.extend([x, x + w])
            y_coords.extend([y, y + h])

            distances.append(distance)
            bearings.append(bearing)

            # Optionally, draw individual bounding boxes
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)

        # Calculate overall bounding box
        x_min = min(x_coords)
        y_min = min(y_coords)
        x_max = max(x_coords)
        y_max = max(y_coords)

        # Draw the overall bounding box
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 0, 0), 2)

        # Calculate average distance and bearing
        avg_distance = np.mean(distances)
        avg_bearing = np.mean(bearings)
        #print(bearings)

        # Add labels
        cv2.putText(image, f"{marker_type}",
                    (x+10, y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(image, f"{avg_distance:.2f}m, {avg_bearing:.2f}deg",
                    (x+10, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return image
