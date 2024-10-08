import numpy as np
import cv2

"""
After contours analyzation, we can estimate the distance and bearing of the detected object.
"""


# Function to apply homography to a point
#homography_matrix = None

class DistanceEstimation:
    def __init__(self, homography_matrix=None, focal_length=None):
        self.homography_matrix = homography_matrix
        self.focal_length = focal_length
        
    def estimate_distance(self, object_width, real_object_width):
        distance = (real_object_width * self.focal_length) / object_width
        return round(distance, 2)

    @staticmethod
    def estimate_bearing(object_center_x, half_image_width=210, max_bearing_angle=35):
        offset = object_center_x - half_image_width
        bearing = (max_bearing_angle * offset) / half_image_width
        return round(bearing, 2)
    
    @staticmethod
    def apply_homography_to_point(x, y, M):
        point = np.array([[x, y]], dtype='float32')
        point = np.array([point])
        transformed_point = cv2.perspectiveTransform(point, M)
        return transformed_point[0][0]
    

    def estimate_homography_distance(self, position):
        if self.homography_matrix is None:
            #print("Error: Homography matrix not loaded.")
            return None

        x, y, w, h = position
        bottom_center_x = x + w // 2
        bottom_center_y = y + h

        ground_coords = self.apply_homography_to_point(bottom_center_x, bottom_center_y, self.homography_matrix)
        distance = np.sqrt(ground_coords[0]**2 + ground_coords[1]**2) # type: ignore
        return round(distance, 2) # type: ignore
    