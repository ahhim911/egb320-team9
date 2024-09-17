import numpy as np

class DistanceEstimation:
    @staticmethod
    def estimate_distance(object_width, real_object_width, focal_length):
        return (real_object_width * focal_length) / object_width

    @staticmethod
    def estimate_bearing(object_center_x, image_width, max_bearing_angle=30):
        offset = object_center_x - (image_width / 2)
        return (max_bearing_angle * offset) / (image_width / 2)
