import numpy as np
import csv
from typing import Dict, Tuple
import os
from picamera2 import Picamera2
import cv2
import time

"""
Calibration module for loading calibration data.
"""


class Color:
    category_mapping: Dict[str, str] = { 
        'orange': 'Item',
        'green': 'Obstacle',
        'blue': 'Shelf',
        'black': 'Marker'
    }
    def __init__(self, csv_file: str = ""):
        """
        Initializes a new instance of the Color class and optionally loads color thresholds.

        Parameters:
            csv_file (str): Optional. Path to the CSV file containing color thresholds.
        """
        self.color_ranges: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        if csv_file:
            self.load_color_thresholds(csv_file)

    def load_color_thresholds(self, csv_file: str) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"The file '{csv_file}' does not exist.")
        
        
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                category = self.category_mapping.get(row[0], None)
                if category:
                    try:
                        lower_hsv = np.array([int(row[1]), int(row[2]), int(row[3])])
                        upper_hsv = np.array([int(row[4]), int(row[5]), int(row[6])])
                        self.color_ranges[category] = (lower_hsv, upper_hsv)
                    except ValueError as e:
                        print(f"Error parsing HSV values in row {row}: {e}")
                else:
                    print(f"Warning: Unrecognized color '{row[0]}' in row {row}")
        return self.color_ranges
    


class CalibrateColor:
    """
    A class to calibrate color thresholds using HSV values from a captured image.
    """

    def __init__(self):
        """
        Initializes the CalibrateColor class by setting up the camera and default values.
        """
        # Variables to store calibration data
        self.captured_image = None  # Variable to store the captured image
        self.valueHSV = set()  # Set of HSV values captured by the user

        # Default color HSV ranges
        self.color_ranges = {
            'orange': (np.array([0, 158, 45]), np.array([13, 255, 235])),
            'green': (np.array([40, 64, 11]), np.array([70, 255, 99])),
            'blue': (np.array([90, 136, 9]), np.array([120, 255, 94])),
            'black': (np.array([0, 0, 43]), np.array([179, 55, 109]))
        }

        # Variable to hold the current color key
        self.current_color_key = None

        # Buffer to be applied to the HSV range
        self.bufferHSV = np.array([10, 50, 20])

        # Initialize the camera
        self.cap = Picamera2()
        frameWidth, frameHeight = 820, 616
        config = self.cap.create_video_configuration(main={"format": 'RGB888', "size": (frameWidth, frameHeight)})
        self.cap.configure(config)
        self.cap.start()

    def resize_image(self, image, scale=0.5):
        """
        Resizes the given image by a scaling factor.

        Parameters:
            image (np.ndarray): The image to resize.
            scale (float): The scaling factor.

        Returns:
            np.ndarray: The resized image.
        """
        resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
        return resized_image

    def add_point_in(self, point):
        """
        Adds an HSV point to the set of captured HSV values.

        Parameters:
            point (tuple): The HSV values at a specific point.
        """
        self.valueHSV.add((point[0], point[1], point[2]))
        print(f"Point added for {self.current_color_key}: ", self.valueHSV)

    def OnMouseClick(self, event, x, y, flags, param):
        """
        Mouse callback function to capture HSV values on mouse click.

        Parameters:
            event: The event type.
            x (int): The x-coordinate of the mouse event.
            y (int): The y-coordinate of the mouse event.
            flags: Any flags associated with the event.
            param: Additional parameters.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            paramHSV = cv2.cvtColor(param, cv2.COLOR_BGR2HSV)
            self.add_point_in(paramHSV[y, x])
            self.update_thresh()

    def update_thresh(self):
        """
        Updates the HSV thresholds based on the captured HSV values and buffer.
        """
        if self.current_color_key is not None and len(self.valueHSV) > 0:
            arr = np.array(list(self.valueHSV))
            lowerHSV = np.maximum(arr.min(0) - self.bufferHSV, 0)
            upperHSV = np.minimum(arr.max(0) + self.bufferHSV, 255)
            self.color_ranges[self.current_color_key] = (lowerHSV, upperHSV)
            print(f"Updated {self.current_color_key} HSV range with buffer: ", self.color_ranges[self.current_color_key])

            if self.captured_image is not None:
                captured_imageHSV = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(captured_imageHSV, self.color_ranges[self.current_color_key][0], self.color_ranges[self.current_color_key][1])
                cv2.imshow("Mask", cv2.bitwise_and(self.captured_image, self.captured_image, mask=mask))
        else:
            print(f"No points selected for {self.current_color_key}.")

    def reset(self):
        """
        Resets the set of captured HSV values.
        """
        self.valueHSV = set()
        print("Resetting points")

    def calibrate(self):
        """
        Main method to perform the calibration process.
        """
        # First, capture the image
        while True:
            t1 = time.time()  # For measuring FPS

            frame = self.cap.capture_array()  # Capture a single image frame
            frame = self.resize_image(frame)  # Resize image
            frame = cv2.flip(frame, -1)  # Flip horizontally and vertically

            # Display the obtained frame in a window called "Image"
            cv2.imshow("Image", frame)

            fps = 1.0 / (time.time() - t1)  # Calculate frame rate
            print("Frame Rate: ", int(fps), end="\r")

            key = cv2.waitKey(1) & 0xFF  # Wait for a key press

            if key == ord('c'):  # Capture the image if 'c' is pressed
                self.captured_image = frame.copy()
                print("Image captured!")
                cv2.destroyWindow("Image")
                break

        # If an image was captured, display it in a new window
        if self.captured_image is not None:
            cv2.imshow("Captured Image", self.captured_image)
            cv2.setMouseCallback("Captured Image", self.OnMouseClick, self.captured_image)

        # Now handle user inputs
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Exit the loop if 'q' is pressed
                break
            elif key == ord('s'):  # Save the HSV range if 's' is pressed
                print("Saving color thresholds...")
                with open("calibrate.csv", "w") as file:
                    for color, (lower, upper) in self.color_ranges.items():
                        lower_str = ','.join(map(str, lower))
                        upper_str = ','.join(map(str, upper))
                        file.write(f"{color},{lower_str},{upper_str}\n")
                print("Color thresholds saved to calibrate.csv")
            elif key == ord('r'):  # Reset the HSV range if 'r' is pressed
                self.reset()
                self.update_thresh()
            elif key == ord('1'):
                self.current_color_key = 'orange'
                print("Selected 'orange' for calibration")
                self.reset()
            elif key == ord('2'):
                self.current_color_key = 'green'
                print("Selected 'green' for calibration")
                self.reset()
            elif key == ord('3'):
                self.current_color_key = 'blue'
                print("Selected 'blue' for calibration")
                self.reset()
            elif key == ord('4'):
                self.current_color_key = 'black'
                print("Selected 'black' for calibration")
                self.reset()

        self.cap.close()
        cv2.destroyAllWindows()
