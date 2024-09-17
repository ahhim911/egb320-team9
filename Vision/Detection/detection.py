import cv2
import numpy as np

class Detection:
    @staticmethod
    def detect_contours(image, mask, min_area=400, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_objects = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
                continue

            detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "aspect_ratio": aspect_ratio,
                "contour": contour
            })

        return detected_objects
