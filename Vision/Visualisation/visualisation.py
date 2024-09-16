import cv2
import csv
import numpy as np

"""
Visualization module for drawing bounding boxes and text on images.
"""


class Visualization:
    @staticmethod
    def draw_bounding_box(image, position, label, color=(255, 0, 0)):
        x, y, w, h = position
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    @staticmethod
    def draw_text(image, text, position, color=(255, 255, 255)):
        cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    @staticmethod
    def show_image(window_name, image):
        cv2.imshow(window_name, image)

    @staticmethod
    def save_image(file_name, image):
        cv2.imwrite(file_name, image)
