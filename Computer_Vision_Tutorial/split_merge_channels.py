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

# Split the frame into color channels
b, g, r = cv2.split(frame)

# Set the blue and green channels to zero
b[:] = 0
g[:] = 0

# Merge the channels back
merged_frame = cv2.merge((b, g, r))

# Display the merged frame
cv2.imshow("Merged Frame", merged_frame)
cv2.waitKey(0)  # Wait for a key press to exit

# Clean up
cap.close()
cv2.destroyAllWindows()
