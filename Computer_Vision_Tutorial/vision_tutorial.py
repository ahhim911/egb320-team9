import cv2
import picamera2
import numpy as np
import time
import imutils

# Initialize the camera with custom settings
def initialize_camera(frame_height=320*2, frame_width=240*2, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({"ColourGains": (1.4, 1.5)})
    picam2.start()
    return picam2

# Initialize the camera
picam2 = initialize_camera()

# Define default HSV ranges for blue, green, and orange colors
blue_lower = np.array([80, 0, 0])
blue_upper = np.array([130, 255, 255])

green_lower = np.array([31, 0, 0])
green_upper = np.array([75, 255, 255])

orange_lower = np.array([0, 50, 50])
orange_upper = np.array([21, 255, 255])

# Create windows for the masks
cv2.namedWindow('Blue Mask')
cv2.namedWindow('Green Mask')
cv2.namedWindow('Orange Mask')
cv2.namedWindow('Contour Frame')

# Create trackbars for adjusting the Hue values
def nothing(x):
    pass

cv2.createTrackbar('Blue HMin', 'Blue Mask', 80, 179, nothing)
cv2.createTrackbar('Blue HMax', 'Blue Mask', 130, 179, nothing)

cv2.createTrackbar('Green HMin', 'Green Mask', 31, 179, nothing)
cv2.createTrackbar('Green HMax', 'Green Mask', 75, 179, nothing)

cv2.createTrackbar('Orange HMin', 'Orange Mask', 0, 179, nothing)
cv2.createTrackbar('Orange HMax', 'Orange Mask', 21, 179, nothing)

def find_contours(filtered_image, min_area=500):
    contours = cv2.findContours(filtered_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    return filtered_contours

try:
    while True:
        start = time.time()

        # Capture an image
        frame = picam2.capture_array()

        # Pre-processing: Resize, rotate, flip, and convert to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.flip(frame, 1)  # Flip the image horizontally
        
        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get current positions of the trackbars for Hue values
        blue_h_min = cv2.getTrackbarPos('Blue HMin', 'Blue Mask')
        blue_h_max = cv2.getTrackbarPos('Blue HMax', 'Blue Mask')
        green_h_min = cv2.getTrackbarPos('Green HMin', 'Green Mask')
        green_h_max = cv2.getTrackbarPos('Green HMax', 'Green Mask')
        orange_h_min = cv2.getTrackbarPos('Orange HMin', 'Orange Mask')
        orange_h_max = cv2.getTrackbarPos('Orange HMax', 'Orange Mask')

        # Update the HSV ranges for each color based on trackbar positions
        blue_lower = np.array([blue_h_min, 100, 100])
        blue_upper = np.array([blue_h_max, 255, 255])
        green_lower = np.array([green_h_min, 100, 100])
        green_upper = np.array([green_h_max, 255, 255])
        orange_lower = np.array([orange_h_min, 100, 100])
        orange_upper = np.array([orange_h_max, 255, 255])

        # Create masks for blue, green, and orange colors
        blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
        green_mask = cv2.inRange(hsv_frame, green_lower, green_upper)
        orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

        # Find contours for each mask, filtering out small contours
        blue_contours = find_contours(blue_mask, min_area=500)
        green_contours = find_contours(green_mask, min_area=500)
        orange_contours = find_contours(orange_mask, min_area=500)

        # Draw contours on the original frame for each color
        contour_frame = frame.copy()
        cv2.drawContours(contour_frame, blue_contours, -1, (255, 0, 0), 2)   # Blue contours
        cv2.drawContours(contour_frame, green_contours, -1, (0, 255, 0), 2)  # Green contours
        cv2.drawContours(contour_frame, orange_contours, -1, (0, 165, 255), 2)  # Orange contours

        # Display the original frame with contours
        cv2.imshow('Contour Frame', contour_frame)

        # Display the masks in separate windows
        cv2.imshow('Blue Mask', cv2.bitwise_and(frame, frame, mask=blue_mask))
        cv2.imshow('Green Mask', cv2.bitwise_and(frame, frame, mask=green_mask))
        cv2.imshow('Orange Mask', cv2.bitwise_and(frame, frame, mask=orange_mask))

        # Print the processing time
        print("Processing time:", time.time() - start)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
