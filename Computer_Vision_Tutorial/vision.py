import cv2
import numpy as np
import imutils
from picamera2 import Picamera2

# Initialize the camera with custom settings
def initialize_camera(frame_height=1080, frame_width=1920, format='XRGB8888'):
    picam2 = Picamera2()
    
    # Set camera configuration with a larger resolution
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.start()
    return picam2

# Homography matrix (replace this with your actual homography matrix)
M = np.array([[ 1.1547,  0.7071, -100.0],
              [-0.7071,  1.1547,   50.0],
              [ 0.001,   0.002,     1.0]])

def apply_homography_to_point(x, y, M):
    point = np.array([[x, y]], dtype='float32')
    point = np.array([point])
    transformed_point = cv2.perspectiveTransform(point, M)
    return transformed_point[0][0]

def calculate_distance_to_ground_plane(bottom_point, homography_matrix):
    # Apply the homography matrix to the bottom point of the contour
    ground_coords = apply_homography_to_point(bottom_point[0], bottom_point[1], homography_matrix)
    
    # Calculate the Euclidean distance from the origin (assuming the camera is at the origin)
    distance = np.sqrt(ground_coords[0]**2 + ground_coords[1]**2)
    return distance, ground_coords

# Initialize the camera
picam2 = initialize_camera()

# Define HSV range for the orange color
orange_lower = np.array([0, 100, 100])
orange_upper = np.array([25, 255, 255])

# Define the distance threshold for the alert (e.g., 25 cm)
distance_threshold = 0.25  # in meters

# Create windows for the mask and visualization
cv2.namedWindow('Orange Mask')
cv2.namedWindow('Bounding Box and Distance')

def find_contours(filtered_image, min_area=500):
    contours = cv2.findContours(filtered_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    return filtered_contours

try:
    while True:
        # Capture an image
        frame = picam2.capture_array()

        # Pre-processing: Resize, rotate, flip, and convert to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.flip(frame, 1)  # Flip the image horizontally

        # Apply Gaussian Blur to reduce noise and smooth the image
        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)

        # Create mask for orange color
        orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

        # Find contours for the orange mask, filtering out small contours
        orange_contours = find_contours(orange_mask, min_area=500)

        # Create a new frame to draw bounding boxes, display distances, and color labels
        bbox_frame = frame.copy()
        
        # Process orange contours
        for contour in orange_contours:
            # Get the bottom-most point of the contour
            bottom_point = tuple(contour[contour[:, :, 1].argmax()][0])
            
            # Calculate the distance to the ground plane using the homography matrix
            distance, ground_coords = calculate_distance_to_ground_plane(bottom_point, M)
            color_label = "Orange"

            # Draw the bounding box and display the distance and color label
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(bbox_frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
            cv2.putText(bbox_frame, f"{color_label} Dist: {distance:.2f}m", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        # Display the mask and the bounding boxes with distances
        cv2.imshow('Orange Mask', cv2.bitwise_and(frame, frame, mask=orange_mask))
        cv2.imshow('Bounding Box and Distance', bbox_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
