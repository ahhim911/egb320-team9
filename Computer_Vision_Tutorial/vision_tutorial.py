import cv2
import picamera2
import numpy as np
import time

# Initialize the camera with custom settings
def initialize_camera(frame_height=320*2, frame_width=240*2, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({"ColourGains": (1.4, 1.5)})
    picam2.start()
    return picam2

# Define the HSV ranges for different colors
blue_lower = np.array([100, 150, 50])
blue_upper = np.array([140, 255, 255])

green_lower = np.array([35, 100, 50])
green_upper = np.array([85, 255, 255])

orange_lower = np.array([10, 100, 100])
orange_upper = np.array([25, 255, 255])

# Create windows for each mask
cv2.namedWindow('Blue Mask')
cv2.namedWindow('Green Mask')
cv2.namedWindow('Orange Mask')
cv2.namedWindow('Combined Mask')

# Initialize the camera
picam2 = initialize_camera()

try:
    while True:
        start = time.time()

        # Capture an image
        frame = picam2.capture_array()

        # Pre-processing: Resize, rotate, blur, and convert to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_RGB2HSV)

        # Create masks for each color
        blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
        green_mask = cv2.inRange(hsv_frame, green_lower, green_upper)
        orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

        # Apply morphological operations to clean the masks
        kernel = np.ones((5, 5), np.uint8)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=1)

        green_mask = cv2.erode(green_mask, kernel, iterations=1)
        green_mask = cv2.dilate(green_mask, kernel, iterations=1)

        orange_mask = cv2.erode(orange_mask, kernel, iterations=1)
        orange_mask = cv2.dilate(orange_mask, kernel, iterations=1)

        # Combine the masks (if you want to detect all colors together)
        combined_mask = cv2.bitwise_or(blue_mask, green_mask)
        combined_mask = cv2.bitwise_or(combined_mask, orange_mask)

        # Find contours for each color mask
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) > 500:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display each mask in its own window
        cv2.imshow('Blue Mask', blue_mask)
        cv2.imshow('Green Mask', green_mask)
        cv2.imshow('Orange Mask', orange_mask)
        cv2.imshow('Combined Mask', frame)

        # Print the processing time
        print("Processing time:", time.time() - start)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
