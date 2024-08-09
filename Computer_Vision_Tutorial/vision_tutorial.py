import cv2
import picamera2
import numpy as np
import time

# Configure the camera settings
cam = picamera2.Picamera2()
config = cam.create_video_configuration(main={"format": 'XRGB8888', "size": (820, 616)})
cam.configure(config)
cam.set_controls({"ColourGains": (1.4, 1.5)})

# Start the camera
cam.start()

# Define the threshold variables
threshold_value = 127
max_value = 255

try:
    while True:
        start = time.time()

        # Capture an image
        frame = cam.capture_array()

        # Resize, rotate, and convert the image to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        # Split the HSV channels (we will threshold the hue channel as an example)
        h, s, v = cv2.split(hsv_frame)

        # Apply thresholding to the hue channel
        _, thresholded_frame = cv2.threshold(h, threshold_value, max_value, cv2.THRESH_BINARY)

        # Display the thresholded image
        cv2.imshow("Thresholded Image", thresholded_frame)

        # Print the processing time
        print("Processing time:", time.time() - start)

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    cam.close()
    cv2.destroyAllWindows()
