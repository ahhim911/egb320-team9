import csv
import cv2
import numpy as np
from picamera2 import Picamera2
import os
import sys

# sys path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from Detection.detection import DetectionBase

"""
Focal length module for loading focal length data.
"""



class FocalLength:
    def __init__(self):
        self.focal_length = None

    def load_focal_length(self, csv_file):
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            self.focal_length = float(next(csv_reader)[1])



class CalibrateFocalLength:
    """
    A class to calibrate the focal length of the camera using a known object.
    """

    def __init__(self):
        """
        Initializes the CalibrateFocalLength class by setting up the camera and default values.
        """
        # import detection base
        self.detection_base = DetectionBase("marker")
        # Known parameters for focal length calibration
        self.real_world_width = 0.07  # 7 cm object width in meters
        self.distance_to_object = 1.04  # 28 cm distance to the object in meters

        # Variables for calibration
        self.focal_length = None
        self.captured_image = None

        # Load color thresholds from CSV
        self.color_ranges = self.load_color_thresholds('color_thresholds.csv')

        # Initialize the camera
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))
        self.picam2.start()

    def preprocess_image(self, image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
        """
        Preprocesses the image by resizing and applying Gaussian blur.

        Parameters:
            image (np.ndarray): The input image.
            scale (float): The scaling factor for resizing.
            blur_ksize (tuple): Kernel size for Gaussian blur.
            sigmaX (float): Standard deviation in X for Gaussian blur.

        Returns:
            np.ndarray: The preprocessed image.
        """
        resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
        blurred_image = cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)
        return blurred_image

    def color_threshold(self, image, lower_hsv, upper_hsv):
        """
        Applies color thresholding to the image.

        Parameters:
            image (np.ndarray): The input image.
            lower_hsv (np.ndarray): Lower bound of HSV values.
            upper_hsv (np.ndarray): Upper bound of HSV values.

        Returns:
            np.ndarray: The mask after thresholding.
        """
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
        return mask

    def apply_morphological_filters(self, mask, kernel_size=(5, 5)):
        """
        Applies morphological operations to the mask.

        Parameters:
            mask (np.ndarray): The input mask.
            kernel_size (tuple): The size of the structuring element.

        Returns:
            np.ndarray: The processed mask.
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)
        return closed_image

    def analyze_contours(self, image, mask, min_area=400, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
        """
        Analyzes contours in the mask and extracts relevant features.

        Parameters:
            image (np.ndarray): The original image.
            mask (np.ndarray): The mask to find contours.
            min_area (int): Minimum area of contour to be considered.
            min_aspect_ratio (float): Minimum aspect ratio of contour.
            max_aspect_ratio (float): Maximum aspect ratio of contour.

        Returns:
            tuple: The image with contours drawn and a list of detected objects.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_image = image.copy()

        detected_objects = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # Skip contours that are too small

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
                continue  # Skip contours with an aspect ratio out of bounds

            # Calculate contour features
            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * np.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = (area / hull_area) if hull_area > 0 else 0
            bounding_box_area = w * h
            fill_ratio = (area / bounding_box_area) if bounding_box_area > 0 else 0

            # Skip contours with low solidity or fill ratio
            if fill_ratio < 0.1:
                continue  # Skip contours with fill ratio less than 0.1
            if circularity < 0.7:
                continue

            # Draw contour and bounding box on the image
            cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)  # Green contours
            cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Blue bounding box

            # Store detected object features
            detected_objects.append({
                "position": (x, y, w, h),
                "area": area,
                "aspect_ratio": aspect_ratio,
                "solidity": solidity,
                "fill_ratio": fill_ratio,
                "circularity": circularity,
                "hull": hull,
                "perimeter": perimeter
            })

        return contour_image, detected_objects

    def calibrate_focal_length(self, detected_objects):
        """
        Calculates the focal length based on the detected marker.

        Parameters:
            detected_objects (list): List of detected objects from contour analysis.

        Returns:
            dict or None: The marker object if detected, else None.
        """
        if len(detected_objects) > 0:
            marker = detected_objects[0]  # Assuming the first object is the marker
            x, y, w, h = marker['position']
            self.focal_length = (w * self.distance_to_object) / self.real_world_width
            print(f"Calculated Focal Length: {self.focal_length:.2f} pixels")
            return marker
        else:
            print("No marker detected for focal length calibration.")
            return None

    def save_focal_length(self):
        """
        Saves the calculated focal length to a CSV file.
        """
        if self.focal_length is not None:
            with open("focal_length.csv", "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Focal Length", self.focal_length])
            print("Focal length data saved to focal_length.csv")
        else:
            print("Focal length is not calculated yet.")

    def load_color_thresholds(self, csv_file):
        """
        Loads color thresholds from a CSV file.

        Parameters:
            csv_file (str): The path to the CSV file.

        Returns:
            dict: A dictionary containing color ranges.
        """
        color_ranges = {}
        category_mapping = {
            'orange': 'Item',
            'green': 'Obstacle',
            'blue': 'Shelf',
            'black': 'Marker'
        }
        
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                category = category_mapping.get(row[0], None)
                if category:
                    lower_hsv = np.array([int(row[1]), int(row[2]), int(row[3])])
                    upper_hsv = np.array([int(row[4]), int(row[5]), int(row[6])])
                    color_ranges[category] = (lower_hsv, upper_hsv)
        return color_ranges

    def calibrate(self):
        """
        Main method to perform the calibration process.
        """
        try:
            while True:
                frame = self.picam2.capture_array()
                scale = 0.5
                frame = cv2.flip(frame, 0)  # Flip horizontally and vertically
                blurred_image = self.preprocess_image(frame, scale)

                # Process the marker category only
                category = "Marker"
                lower_hsv, upper_hsv = self.color_ranges[category]
                mask = self.color_threshold(blurred_image, lower_hsv, upper_hsv)
                processed_mask = self.apply_morphological_filters(mask)
                contour_image, detected_objects = self.analyze_contours(blurred_image, processed_mask)

                # Display the result image
                cv2.imshow("Marker Detection", contour_image)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):  # Capture the image if 'c' is pressed
                    self.captured_image = frame.copy()
                    print("Image captured!")
                    cv2.destroyWindow("Marker Detection")  # Close the Marker Detection window
                    break
                elif key == ord('q'):
                    break

            # If an image was captured, display it in a new window and perform calibration steps
            if self.captured_image is not None:
                cv2.imshow("Captured Image", self.captured_image)  # Display the captured frame
                while True:
                    key = cv2.waitKey(1) & 0xFF

                    if key == ord('q'):  # Exit the loop if 'q' is pressed
                        break
                    elif key == ord('1'):  # Calibrate focal length if '1' is pressed
                        marker = self.calibrate_focal_length(detected_objects)
                        if marker is not None:
                            print(f"Focal length: {self.focal_length:.2f} pixels")
                    elif key == ord('s'):  # Save the calibration data if 's' is pressed
                        self.save_focal_length()
        finally:
            self.picam2.close()
            cv2.destroyAllWindows()
