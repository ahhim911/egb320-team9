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

# Define the HSV ranges for blue, green, and orange colors
blue_lower = np.array([80, 50, 50])
blue_upper = np.array([130, 255, 255])

green_lower = np.array([35, 50, 50])
green_upper = np.array([79, 255, 255])

orange_lower = np.array([10, 100, 100])
orange_upper = np.array([25, 255, 255])

# Create windows for the masks
cv2.namedWindow('Blue Mask')
cv2.namedWindow('Green Mask')
cv2.namedWindow('Orange Mask')

# Initialize the camera
picam2 = initialize_camera()

def find_contours(filtered_image):
    contours = cv2.findContours(filtered_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contour_exist = (len(contours) != 0)
    width_px = []

    if contour_exist:
        for item in contours:
            width_px.append(int(cv2.minAreaRect(item)[1][0]))
    else:
        width_px.append(-1)

    return contours, width_px

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

        # Create masks for blue, green, and orange colors
        blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
        green_mask = cv2.inRange(hsv_frame, green_lower, green_upper)
        orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

        # Find contours for each mask
        blue_contours, _ = find_contours(blue_mask)
        green_contours, _ = find_contours(green_mask)
        orange_contours, _ = find_contours(orange_mask)

        # Draw contours and bounding boxes on the original frame for each color
        for contour in blue_contours:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Blue color bounding box

        for contour in green_contours:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green color bounding box

        for contour in orange_contours:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)  # Orange color bounding box

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
