import cv2
import os
import numpy as np
from shelf import Shelf
from marker import Marker
from wall import Wall
from packing_station import PackingStationRamp
from obstacle import Obstacle
from item import Item
import time

# Predefined color ranges for different categories
color_ranges = {
    'Shelf': (np.array([80, 60, 15]), np.array([140, 255, 255])),
    'Obstacle': (np.array([40, 50, 0]), np.array([90, 255, 200])),
    'Item': (np.array([0, 150, 27]), np.array([14, 255, 255])),
    'Marker': (np.array([0, 0, 0]), np.array([179, 160, 120])),
    'Wall': (np.array([0, 0, 150]), np.array([255, 255, 255])),
    'PackingStationRamp': (np.array([0, 100, 200]), np.array([50, 255, 255]))
}

# from ..Calibration.calibration import Calibration

# # Load the color ranges from the calibration file
# calibration = Calibration()
# color_ranges = calibration.load_csv()[0]

def is_video(file_path):
    """Check if the given file is a video based on its extension."""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in video_extensions

def load_image(image_path):
    """Load the image from the path and return the frame."""
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Unable to load image {image_path}")
        return None
    return frame

def detect_in_image(image):
    """Detect objects in a single image."""
    if image is None:
        print("Error: No image to process.")
        return
        

    # Initialize detectors
    shelf_detector = Shelf()
    marker_detector = Marker()
    wall_detector = Wall()
    ramp_detector = PackingStationRamp()  # Initialize the ramp detector

    # Detect objects in the current frame
    detected_shelves, shelf_frame, shelf_mask = shelf_detector.find_shelf(image, color_ranges)
    detected_walls, filled_wall_mask, wall_mask = wall_detector.find_wall(image, color_ranges)
    detected_markers, marker_frame, marker_mask = marker_detector.find_marker(image, filled_wall_mask, color_ranges)
    detected_ramp, ramp_frame, ramp_mask = ramp_detector.find_packing_station_ramp(image, color_ranges)  # Ramp detection

    # Display the detection results
    #cv2.imshow('Shelf Detection', shelf_frame)
    #cv2.imshow('Shelf Mask', shelf_mask)
    #cv2.imshow('Marker Detection', marker_frame)
    #cv2.imshow('Marker Mask', marker_mask)
    cv2.imshow('Ramp Detection', ramp_frame)  # Display ramp detection results
    cv2.imshow('Ramp Mask', ramp_mask)
    #cv2.imshow('Wall Mask', filled_wall_mask)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

def detect_in_video(video_path):
    """Detect objects in each frame of a video and display live preview."""
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video {video_path}")
        return

    homography_matrix = np.array([[-0.0006663705008854376, 0.00010599070501256366, 0.11950082342807557],
                              [-2.7981731315770147e-05, -0.00026224463974209775, -0.13070560750233118],
                              [1.5216246479124574e-05, -0.007464510917774103, 1.0]])

    # Initialize detectors
    shelf_detector = Shelf(homography_matrix=homography_matrix)
    marker_detector = Marker()
    wall_detector = Wall()
    ramp_detector = PackingStationRamp()  # Initialize the ramp detector
    obstacle_detector = Obstacle(focal_length=300, homography_matrix=homography_matrix)
    item_detector = Item()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video
        now = time.time()
        # Detect objects in the current frame
        detected_shelves, shelf_frame, shelf_mask = shelf_detector.find_shelf(frame, color_ranges)
        detected_walls, filled_wall_mask, wall_mask = wall_detector.find_wall(frame, color_ranges)
        detected_markers, marker_frame, marker_mask = marker_detector.find_marker(frame, filled_wall_mask, color_ranges)
        #detected_ramp, ramp_frame, ramp_mask = ramp_detector.find_packing_station_ramp(frame, color_ranges)  # Ramp detection
        detected_obstacles, obstacle_frame, obstacle_mask = obstacle_detector.find_obstacle(frame, color_ranges)
        detected_items, item_frame, item_mask = item_detector.find_item(frame, color_ranges)

    #    # Display the detection results
    #    cv2.imshow('Shelf Detection', shelf_frame)
    #    #cv2.imshow('Shelf Mask', shelf_mask)
    #    cv2.imshow('Marker Detection', marker_frame)
    #    cv2.imshow('Marker Mask', marker_mask)
    #    cv2.imshow('Obstacle Detection', obstacle_frame)
    #    #cv2.imshow('Obstacle Mask', obstacle_mask)
    #    cv2.imshow('Item Detection', item_frame)
    #    #cv2.imshow('Item Mask', item_mask)
    #    #cv2.imshow('Ramp Detection', ramp_frame)  # Display ramp detection results
    #    #cv2.imshow('Ramp Mask', ramp_mask)
    #    cv2.imshow('Wall Mask', filled_wall_mask)

        elapsed = time.time() - now
        fps = 1/elapsed
        print('Time: ', elapsed, ' - FPS: ',fps)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run_detection(file_path):
    """Run object detection on either an image or video based on the file type."""
    if os.path.isfile(file_path):
        if is_video(file_path):
            print(f"Processing video: {file_path}")
            detect_in_video(file_path)
        else:
            print(f"Processing image: {file_path}")
            image = load_image(file_path)
            detect_in_image(image)
    else:
        print(f"Error: File {file_path} does not exist.")

def main():
    # Replace with your file path (video or image)
    file_path = '/home/edmond3321/egb320-team9/Vision/Camera/Videos/1_searching_left_1.mp4'
    # file_path = '../Camera/Videos/1_going_row3_2.mp4'
    # file_path = '../Camera/Videos/1_searching_left_1.mp4'
    # file_path = '../Camera/Videos/NG_search_packing station.mp4'
    # file_path = '../Camera/Videos/2_going_row1_ps.mp4'
    run_detection(file_path)

if __name__ == '__main__':
    main()
