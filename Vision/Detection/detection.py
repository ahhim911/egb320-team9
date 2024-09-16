import cv2
import numpy as np

class DetectionBase:
    def __init__(self, name):
        self.name = name
        self.detected_objects = []

    def analyze_contours(self, image, mask, min_area=150, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
        """
        Base analyze_contours function to be overridden by subclasses for specific logic.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
                continue

            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * np.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = (area / hull_area) if hull_area > 0 else 0
            bounding_box_area = w * h
            fill_ratio = (area / bounding_box_area) if bounding_box_area > 0 else 0

            # Filter by solidity and fill ratio
            if solidity < 0.5 or fill_ratio < 0.1:
                continue

            self.detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "aspect_ratio": aspect_ratio,
                "solidity": solidity,
                "fill_ratio": fill_ratio,
                "circularity": circularity,
                "hull": hull,
                "perimeter": perimeter,
                "contour": contour
            })

    def draw_contours(self, image):
        """
        Draw contours on the image based on detected objects.
        """
        contour_image = image.copy()

        for obj in self.detected_objects:
            x, y, w, h = obj["position"]
            contour = obj["contour"]
            
            # Draw the contour
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)

            # Draw the bounding box
            cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        return contour_image

    def calculate_range_and_bearing(self, x, y, w, h):
        """
        Example function to calculate range and bearing for an object.
        """
        # Dummy calculation, customize with real logic
        range_ = np.sqrt(x**2 + y**2)
        bearing = np.arctan2(y, x)
        return range_, bearing
