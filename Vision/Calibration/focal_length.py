import csv
import cv2
import numpy as np
from threading import Thread, Event
from Vision.Camera.camera import Camera
from Vision.Detection.marker import Marker
from Vision.Detection.wall import Wall

class FocalLength:
    def __init__(self):
        self.focal_length = None

    def load_focal_length(self, csv_file):
        try:
            with open(csv_file, mode='r') as file:
                csv_reader = csv.reader(file)
                self.focal_length = float(next(csv_reader)[1])
            return self.focal_length
        except (FileNotFoundError, ValueError, IndexError) as e:
            print(f"Error loading focal length: {e}")
            return None

class CalibrateFocalLength:
    def __init__(self):
        """
        Initializes the CalibrateFocalLength class by setting up the camera, wall detection, and marker detection.
        """
        self.real_world_width = 0.07  # Marker width in meters
        self.distance_to_object = 0.3  # Distance to marker in meters

        self.focal_length = None
        self.captured_image = None

        # Load color thresholds from CSV
        self.color_ranges = self.load_color_thresholds('Vision/Calibration/color_thresholds.csv')

        # Initialize the camera and threading
        self.camera = Camera()
        self.stop_event = Event()
        self.live_thread = Thread(target=self.camera.live_feed, args=(self.stop_event,))

        # Initialize the marker and wall detectors
        self.marker_detector = Marker(real_marker_height=self.real_world_width)
        self.wall_detector = Wall()

    def load_color_thresholds(self, csv_file):
        """
        Loads color thresholds from a CSV file.

        Returns:
            dict: A dictionary containing color ranges or None if loading fails.
        """
        color_ranges = {}
        category_mapping = {
            'orange': 'Item',
            'green': 'Obstacle',
            'blue': 'Shelf',
            'black': 'Marker',   # Black will be used for marker detection
            'white': 'Wall',     # White will be used for wall detection
            'yellow': 'Ramp',    # Yellow will be used for ramp detection
            'white2': 'Wall2'    # White2 will be used for second wall detection (Wall2)
        }

        try:
            with open(csv_file, mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    category = category_mapping.get(row[0], None)
                    if category:
                        lower_hsv = np.array([int(row[1]), int(row[2]), int(row[3])])
                        upper_hsv = np.array([int(row[4]), int(row[5]), int(row[6])])
                        color_ranges[category] = (lower_hsv, upper_hsv)
            return color_ranges
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file}' not found.")
            return None
        except (IndexError, ValueError) as e:
            print(f"Error loading color thresholds: {e}")
            return None

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
            try:
                with open("focal_length.csv", "w", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Focal Length", self.focal_length])
                print("Focal length data saved to focal_length.csv")
            except IOError as e:
                print(f"Error saving focal length to file: {e}")
        else:
            print("Error: Focal length is not calculated yet.")

    def calibrate(self):
        """
        Main method to handle calibration and testing using live feed.
        """
        if self.color_ranges is None:
            print("Error: Color thresholds not loaded. Exiting.")
            return

        self.live_thread.start()
        captured = False

        try:
            while True:
                frame = self.camera.get_frame()  # Get the current frame
                if frame is None:
                    continue

                # Convert the frame to HSV color space
                HSVframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Detect the wall mask
                try:
                    lower_hsv_wall, upper_hsv_wall = self.color_ranges['Wall']
                except KeyError:
                    print("Error: Wall color thresholds not found in CSV.")
                    break

                #wall_mask = cv2.inRange(HSVframe, lower_hsv_wall, upper_hsv_wall)
                _, _, filled_wall_mask = self.wall_detector.find_wall(HSVframe, frame, self.color_ranges)
                cv2.imshow("filled_wall_mask",filled_wall_mask)
                # Detect the marker mask
                try:
                    lower_hsv_marker, upper_hsv_marker = self.color_ranges['Marker']
                except KeyError:
                    print("Error: Marker color thresholds not found in CSV.")
                    break

                marker_mask = cv2.inRange(HSVframe, lower_hsv_marker, upper_hsv_marker)
                cv2.imshow("marker_mask",marker_mask)
                # Bitwise AND to only keep the marker on the wall
                if filled_wall_mask is not None and marker_mask is not None:
                    marker_on_wall_mask = cv2.bitwise_and(marker_mask, filled_wall_mask)
                else:
                    print("Error: Wall or marker mask is None.")
                    continue

                # Perform marker detection on the combined mask
                detected_objects = self.marker_detector._detect_and_classify_markers(marker_on_wall_mask)

                if not captured:
                    # Display live detection with markers drawn on the frame
                    if len(detected_objects) > 0:
                        marker_frame = frame.copy()
                        frame_with_marker = self.marker_detector._draw_bounding_box(marker_frame, detected_objects, "Marker")
                        cv2.imshow("Live Feed", frame_with_marker)
                    else:
                        cv2.imshow("Live Feed", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):
                    # Capture the frame for calibration (no drawing on captured image)
                    self.captured_image = frame.copy()
                    print("Frame captured for calibration.")
                    marker = self.calibrate_focal_length(detected_objects)
                    if marker:
                        print(f"Focal length: {self.focal_length:.2f} pixels")
                        # Redraw markers with updated focal length for distance calculation
                        frame_with_marker, _ = self.marker_detector._draw_bounding_box(self.captured_image, detected_objects, "Marker")
                        cv2.imshow("Calibrated Image", frame_with_marker)
                        captured = True
                    else:
                        print("No markers detected. Returning to live feed in 2 seconds.")
                        cv2.waitKey(2000)  # Wait for 2 seconds before returning to live feed
                        captured = False

                elif key == ord('t'):
                    # Test the focal length with live feed
                    if self.focal_length is not None:
                        print(f"Testing focal length: {self.focal_length:.2f} pixels")
                        captured = False  # Resume live feed with marker detection
                    else:
                        print("Error: Focal length not set. Please calibrate first.")

                elif key == ord('s'):
                    # Save the calibrated focal length
                    self.save_focal_length()

                elif key == ord('q'):
                    print("Exit")
                    break

        finally:
            self.stop_event.set()  # Stop the live feed
            self.live_thread.join()
            self.camera.close()
            cv2.destroyAllWindows()
            print("Shutdown complete")

    def __del__(self):
        self.stop_event.set()
        self.live_thread.join()
        self.camera.close()
        cv2.destroyAllWindows()
        print("__del__")

if __name__ == "__main__":
    calibrator = CalibrateFocalLength()
    calibrator.calibrate()

