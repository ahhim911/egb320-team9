import cv2

from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing


class Shelf(DetectionBase):
    def __init__(self, real_shelf_width=0.5, focal_length=300, homography_matrix=None):
        super().__init__("Shelf")
        self.real_shelf_width = real_shelf_width  # Real-world width of the shelf (in meters)
        self.focal_length = focal_length  # Camera focal length (in pixels)
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)  # Initialize distance estimator with homography

    def find_shelf(self, image, color_ranges):
        """
        Find the shelf by creating a mask based on the color range, analyzing contours, and calculating range/bearing for corners.
        """
        lower_hsv, upper_hsv = color_ranges['Shelf']
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))
        self.analyze_contours(scaled_image, mask)

        # Iterate through each detected object and get the bottom-left and bottom-right corners
        for obj in self.detected_objects:
            corners = self.get_contour_corners_for_object(obj)

            # Get bottom-right and bottom-left corners for each object
            bottom_right = self.get_specific_corner(corners, criterion="bottom-right")
            bottom_left = self.get_specific_corner(corners, criterion="bottom-left")

            # Calculate range and bearing for each corner
            if bottom_right:
                distance_right = self.distance_estimator.estimate_homography_distance((bottom_right[0], bottom_right[1], 1, 1))  # Dummy w, h
                bearing_right = self.distance_estimator.estimate_bearing(bottom_right[0], scaled_image.shape[1])

                # Draw a red circle on the bottom-right corner and annotate with distance and bearing
                cv2.circle(scaled_image, bottom_right, 5, (0, 0, 255), -1)
                cv2.putText(scaled_image, f"R: {distance_right:.2f}m, {bearing_right:.2f}deg", bottom_right, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            if bottom_left:
                distance_left = self.distance_estimator.estimate_homography_distance((bottom_left[0], bottom_left[1], 1, 1))  # Dummy w, h
                bearing_left = self.distance_estimator.estimate_bearing(bottom_left[0], scaled_image.shape[1])

                # Draw a blue circle on the bottom-left corner and annotate with distance and bearing
                cv2.circle(scaled_image, bottom_left, 5, (255, 0, 0), -1)
                cv2.putText(scaled_image, f"L: {distance_left:.2f}m, {bearing_left:.2f}deg", bottom_left, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return self.detected_objects, self.draw_contours(scaled_image), mask

    def analyze_contours(self, image, mask, min_area=800):
        """
        Overrides DetectionBase.analyze_contours to provide more specific logic for shelves.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Use convex hull for contour smoothing
            hull = cv2.convexHull(contour)

            # Use cv2.approxPolyDP for contour simplification (optional)
            epsilon = 0.001 * cv2.arcLength(hull, True)
            smoothed_contour = cv2.approxPolyDP(hull, epsilon, True)

            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "contour": smoothed_contour
            })

    def draw_contours(self, image):
        """
        Draw approximated shapes based on detected objects.
        """
        contour_image = image.copy()

        for obj in self.detected_objects:
            # Draw the smoothed contour
            contour = obj["contour"]
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

        return contour_image

    def get_contour_corners_for_object(self, obj):
        """
        Extract corner points for a specific object's contour.
        """
        return [tuple(point.ravel()) for point in obj["contour"]]

    def get_specific_corner(self, corners, criterion="bottom-right", x_threshold=4):
        """
        Get the bottom-right or bottom-left corner based on the criterion.
        Apply an x-threshold to filter points near the rightmost/leftmost point.
        """
        if not corners:
            return None

        if criterion == "bottom-right":
            # Find the rightmost x value
            reference_x = max(corners, key=lambda c: c[0])[0]
        else:  # criterion == "bottom-left"
            # Find the leftmost x value
            reference_x = min(corners, key=lambda c: c[0])[0]

        # Filter points within the x-threshold of the reference point
        filtered_corners = [c for c in corners if reference_x - x_threshold <= c[0] <= reference_x + x_threshold]

        # Find the bottom-most point from the filtered corners (largest y)
        return max(filtered_corners, key=lambda c: c[1], default=None) if filtered_corners else None
