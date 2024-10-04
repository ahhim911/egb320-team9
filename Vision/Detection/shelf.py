import cv2
import numpy as np
from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing

class Shelf(DetectionBase):
    def __init__(self, real_shelf_width=0.5, focal_length=300, homography_matrix=None, draw=False):
        """
        Initializes the Shelf class with optional parameters.

        Args:
        - real_shelf_width: Real-world width of the shelf (in meters).
        - focal_length: Focal length of the camera (in pixels).
        - homography_matrix: Matrix used for perspective transformation.
        - draw: Flag to enable or disable drawing bounding boxes and labels.
        """
        super().__init__("Shelf")
        self.real_shelf_width = real_shelf_width
        self.focal_length = focal_length
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)
        self.draw = draw  # Flag to control drawing

    def find_shelf(self, image, RGBframe, color_ranges):
        """
        Detect the shelf by creating a mask based on the color range, analyzing contours, and calculating range/bearing for corners.
        """
        # 1. Preprocess Image
        mask = self._preprocess_image(image, color_ranges)

        # 2. Detect Shelves
        detected_shelves = self._detect_shelves(mask)

        # 3. Process Corners (Bottom-left and Bottom-right) and calculate range/bearing
        data_list = []
        for obj in detected_shelves:
            shelf_data = self._process_corners(obj)
            if shelf_data:
                data_list.append(shelf_data)  # Append the corner data for the current shelf

        # 4. Draw contours and corners if enabled
        final_image = self._draw_if_enabled(RGBframe, detected_shelves, data_list)
        # print("SHELF DATA: ", data_list)

        return data_list, final_image, mask

    def _preprocess_image(self, image, color_ranges):
        """
        Preprocess the image using the defined color ranges.
        """
        lower_hsv, upper_hsv = color_ranges['Shelf']
        mask, _ = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)
        return mask

    def _detect_shelves(self, mask, min_area=800):
        """
        Analyzes contours to detect shelves and calculates range/bearing for their corners.

        Args:
        - mask: Binary mask from preprocessing.
        - min_area: Minimum area for contour detection.

        Returns:
        - List of detected shelf objects.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)
            hull = cv2.convexHull(contour)

            # Simplify contour using cv2.approxPolyDP
            epsilon = 0.001 * cv2.arcLength(hull, True)
            smoothed_contour = cv2.approxPolyDP(hull, epsilon, True)

            detected_objects.append({
                "position": (x, y, w, h),
                "contour": smoothed_contour
            })

        return detected_objects

    def _process_corners(self, obj):
        """
        Process the bottom-left and bottom-right corners of the detected object and calculate range and bearing.

        Args:
        - obj: Detected shelf object.

        Returns:
        - List of corner data for a single shelf in the form [[corner_type, distance, bearing, position], ...].
        """
        corners = self._get_contour_corners_for_object(obj)

        shelf_data = []

        # 2 represents bottom-right, 1 represents bottom-left
        for corner_type, criterion in [(1, "bottom-left"), (2, "bottom-right")]:
            corner = self._get_specific_corner(corners, criterion=criterion)

            if corner is not None:
                # Calculate homography distance and bearing
                distance = self.distance_estimator.estimate_homography_distance((corner[0], corner[1], 0, 0))
                bearing = self.distance_estimator.estimate_bearing(corner[0])

                # Append in the format [corner_type, distance, bearing, position] where corner_type is 1 or 2
                shelf_data.append([corner_type, distance, bearing, corner])

        return shelf_data  # Return the corner data for the current shelf



    def _draw_if_enabled(self, image, detected_shelves, corners_data):
        """
        Draw bounding boxes, corners, and labels if the draw flag is enabled.
        """
        if not self.draw:
            return image  # Return original image if drawing is disabled

        # Draw contours and corners
        image = self._draw_contours(image, detected_shelves)
        image = self._draw_corners(image, corners_data)

        return image


    def _draw_contours(self, image, detected_shelves):
        """
        Draws bounding boxes and labels for detected shelves.

        Args:
        - image: The image on which bounding boxes will be drawn.
        - detected_shelves: List of detected shelf objects with positions, distances, and bearings.

        Returns:
        - The image with bounding boxes and labels drawn.
        """

        for obj in detected_shelves:
            contour = obj["contour"]
            cv2.drawContours(image, [contour], -1, (255, 0, 0), 2)

        return image

    def _draw_corners(self, image, corners_data):
        """
        Draws the bottom-left (1) and bottom-right (2) corners of the shelf, with labels for distance and bearing.
    
        Args:
        - image: The image on which corners will be drawn.
        - corners_data: List of corner data in the format [[corner_type, distance, bearing, position], ...].
    
        Returns:
        - The image with corners and labels drawn.
        """
        for shelf in corners_data:
            for corner_data in shelf:
                if len(corner_data) < 4:  # Ensure corner_data has at least corner_type, distance, bearing, and position
                    print(f"Error: corner_data is missing elements: {corner_data}")
                    continue
                
                # Unpack the corner_type, distance, bearing, and position
                corner_type, distance, bearing, corner_position = corner_data
    
                # Assign the color based on the corner type
                color = (0, 0, 255) if corner_type == 2 else (255, 0, 0)  # Red for bottom-right, blue for bottom-left
    
                # Draw circle at the corner position
                cv2.circle(image, corner_position, 5, color, -1)
    
                # Add label for distance and bearing
                label = f"{distance:.2f}m, {bearing:.2f}deg"
                cv2.putText(image, label, (corner_position[0] + 10, corner_position[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
        return image



    def _get_contour_corners_for_object(self, obj):
        """
        Extract corner points for a specific object's contour.
        """
        return [tuple(point.ravel()) for point in obj["contour"]]

    def _get_specific_corner(self, corners, criterion="bottom-right", x_threshold=6):
        """
        Get the bottom-right or bottom-left corner based on the criterion.

        Args:
        - corners: List of corner points.
        - criterion: "bottom-right" or "bottom-left" to get the respective corner.
        - x_threshold: Threshold to filter points near the rightmost/leftmost point.

        Returns:
        - The corner point based on the criterion.
        """
        if not corners:
            return None

        if criterion == "bottom-right":
            reference_x = max(corners, key=lambda c: c[0])[0]
        else:  # criterion == "bottom-left"
            reference_x = min(corners, key=lambda c: c[0])[0]

        filtered_corners = [c for c in corners if reference_x - x_threshold <= c[0] <= reference_x + x_threshold]
        return max(filtered_corners, key=lambda c: c[1], default=None) if filtered_corners else None

