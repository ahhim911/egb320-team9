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

# Define the HSV range for blue color based on your input
blue_lower = np.array([100, 50, 50])
blue_upper = np.array([179, 255, 255])

# Create a window for the blue mask
cv2.namedWindow('Blue Mask')

# Initialize the camera
picam2 = initialize_camera()

try:
    while True:
        start = time.time()

        # Capture an image
        frame = picam2.capture_array()

        # Pre-processing: Resize, rotate, flip, and convert to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.flip(frame, 1)  # Flip the image horizontally
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        # Create a mask for the blue color
        blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
        result = cv2.bitwise_and(frame, frame, mask=blue_mask)

        # Display the blue mask in the window
        cv2.imshow('Blue Mask', result)

        # Print the processing time
        print("Processing time:", time.time() - start)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
