import cv2
import picamera2
import numpy as np

# Initialize the camera
cap = picamera2.Picamera2()
config = cap.create_video_configuration(main={"format": 'XRGB8888', "size": (820, 616)})
cap.configure(config)
cap.set_controls({"ColourGains": (1.4, 1.5)})

# Start the camera
cap.start()
frame = cap.capture_array()
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

# Extract the blue channel and apply binary thresholding
frame_blue = frame[:, :, 0]
ret, thresholded_frame = cv2.threshold(frame_blue, 127, 255, cv2.THRESH_BINARY)

# Display the thresholded frame
cv2.imshow("Binary Thresholded Frame", thresholded_frame)
cv2.waitKey(0)  # Wait for a key press to exit

# Clean up
cap.close()
cv2.destroyAllWindows()
