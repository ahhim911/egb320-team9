import cv2
import numpy as np

"""
A preprocessing module for image processing tasks.
"""

class Preprocessing:
    
    @staticmethod
    def resize(image, size=(640, 480)):
        """Resize the image to a specified size."""
        return cv2.resize(image, size)
    
    @staticmethod
    def scale(image, fx=0.5, fy=0.5):
        """Scale the image by a given factor for x and y axes."""
        return cv2.resize(image, (0, 0), fx=fx, fy=fy)
    
    @staticmethod
    def blur(image, ksize=(5, 5), sigmaX=2):
        """Apply Gaussian blur to the image."""
        return cv2.GaussianBlur(image, ksize, sigmaX)
    
    @staticmethod
    def to_hsv(image):
        """Convert BGR image to HSV."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    @staticmethod
    def color_threshold(image, lower_hsv, upper_hsv):
        """Apply color thresholding in HSV color space."""
        hsv_image = Preprocessing.to_hsv(image)
        mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
        return mask

    @staticmethod
    def apply_morphological_filters(mask, kernel_size=(10, 10)):
        """Apply morphological operations to remove noise."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)
        return closed_image
    
    @staticmethod
    def preprocess(image, resize_to=(640, 480), scale=0.5, blur_ksize=(5, 5), sigmaX=2, lower_hsv=(80, 60, 0), upper_hsv=(140, 255, 255), kernel_size=(5, 5)):
        """
        Apply a full preprocessing pipeline:
        1. Resize the image
        2. Apply Gaussian blur
        3. Convert to HSV
        4. Apply color thresholding
        5. Apply morphological filtering
        """
        #resized = Preprocessing.resize(image, resize_to)
        #scaled = Preprocessing.scale(image,fx=scale,fy=scale)
        #blurred = Preprocessing.blur(scaled, blur_ksize, sigmaX)
        thresholded = Preprocessing.color_threshold(image, lower_hsv, upper_hsv)
        #processed = Preprocessing.apply_morphological_filters(thresholded, kernel_size)
        return thresholded, image
