# Import the necessary modules
import cv2

from .detection import DetectionBase  # Import DetectionBase from detection.py
from .range_bearing import DistanceEstimation  # Import the DistanceEstimation class
from ..Preprocessing.preprocessing import Preprocessing  # Import Preprocessing class


class PackingStationRamp(DetectionBase):
    def __init__(self, real_station_width=0.8, focal_length=300, homography_matrix=None):
        super().__init__("Ramp")
        self.real_station_width = real_station_width  # Real width of the packing station in meters
        self.focal_length = focal_length
        self.distance_estimator = DistanceEstimation(homography_matrix=homography_matrix)

    def find_packing_station_ramp(self, image, color_ranges):
        """
        Detects the packing station ramp by using color and contour analysis.
        """
        # Define the HSV color range for the ramp
        lower_hsv, upper_hsv = color_ranges['Ramp']

        # Preprocess the image to create a mask for the ramp
        mask, scaled_image = Preprocessing.preprocess(image, blur_ksize=(1, 1), sigmaX=1, lower_hsv=lower_hsv, upper_hsv=upper_hsv, kernel_size=(1, 1))

        # Analyze the contours of the detected ramp
        detected_ramp = self.analyze_contours(mask, scaled_image.shape[1])

        # If the ramp is detected, draw bounding boxes and labels
        if detected_ramp:
            final_image = self.draw_bounding_box(scaled_image, detected_ramp)
        else:
            final_image = scaled_image  # Return original image if no ramp is found

        return detected_ramp, final_image, mask

    def analyze_contours(self, mask, image_width, min_area=1000):
        """
        Analyzes contours for the detected ramp and estimates distance and bearing.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip small contours

            x, y, w, h = cv2.boundingRect(contour)

            # Estimate distance using the homography matrix or the known real width
            distance = self.distance_estimator.estimate_homography_distance((x, y, w, h))

            # Estimate bearing using the object's center X position
            object_center_x = x + (w // 2)
            bearing = self.distance_estimator.estimate_bearing(object_center_x, image_width)

            detected_objects.append({
                "position": (x, y, w, h),
                "distance": distance,  # Add distance information
                "bearing": bearing,    # Add bearing information
                "contour": contour,
            })

        return detected_objects

    def draw_bounding_box(self, image, detected_ramp):
        """
        Draws a bounding box around the detected packing station ramp and adds labels for distance and bearing.
        """
        for obj in detected_ramp:
            x, y, w, h = obj['position']
            distance = obj['distance']
            bearing = obj['bearing']

            # Draw the bounding box around the ramp
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add the label with distance and bearing in the center of the bounding box
            label = f"Ramp: {distance:.2f}m, {bearing:.2f}deg"
            text_x = x + w // 2
            text_y = y + h // 2
            cv2.putText(image, label, (text_x - 80, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return image
