import cv2
import os
import numpy as np
from shelf import Shelf  # Import the Shelf detector class
#from item import Item
#from marker import Marker
#from obstacle import Obstacle

# Predefined color ranges for different categories
color_ranges = {
    'Shelf': (np.array([80, 60, 0]), np.array([140, 255, 255])),
    'Obstacle': (np.array([50, 0, 0]), np.array([69, 185, 155])),
    'Item': (np.array([0, 150, 27]), np.array([14, 255, 255])),
    'Marker': (np.array([0, 40, 40]), np.array([29, 94, 90]))
}

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
    #item_detector = Item()
    #marker_detector = Marker()
    #obstacle_detector = Obstacle()

    # Detect objects in the image
    detected_shelves, shelf_frame, mask = shelf_detector.find_shelf(image, color_ranges)
    #detected_items, item_frame = item_detector.find_item(image, color_ranges)
    #detected_markers, marker_frame = marker_detector.find_marker(image, color_ranges)
    #detected_obstacles, obstacle_frame = obstacle_detector.find_obstacle(image, color_ranges)

    # Display the detection results
    cv2.imshow('Shelf Detection', shelf_frame)
    cv2.imshow('Mask Detection', mask)
    #cv2.imshow('Item Detection', item_frame)
    #cv2.imshow('Marker Detection', marker_frame)
    #cv2.imshow('Obstacle Detection', obstacle_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def detect_in_video(video_path):
    """Detect objects in each frame of a video and display live preview."""
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video {video_path}")
        return

    # Initialize detectors
    shelf_detector = Shelf()
    #item_detector = Item()
    #marker_detector = Marker()
    #obstacle_detector = Obstacle()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Detect objects in the current frame
        detected_shelves, shelf_frame, mask = shelf_detector.find_shelf(frame, color_ranges)
        #detected_items, item_frame = item_detector.find_item(frame, color_ranges)
        #detected_markers, marker_frame = marker_detector.find_marker(frame, color_ranges)
        #detected_obstacles, obstacle_frame = obstacle_detector.find_obstacle(frame, color_ranges)

        # Display the detection results
        cv2.imshow('Shelf Detection', shelf_frame)
        cv2.imshow('Mask Detection', mask)
        #cv2.imshow('Item Detection', item_frame)
        #cv2.imshow('Marker Detection', marker_frame)
        #cv2.imshow('Obstacle Detection', obstacle_frame)

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
    run_detection(file_path)

if __name__ == '__main__':
    main()