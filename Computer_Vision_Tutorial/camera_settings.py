import time
import picamera2
import cv2

# Initialize the camera
picam2 = picamera2.Picamera2()

# Create and configure camera settings
config = picam2.create_video_configuration(main={"format": 'XBGR8888', "size": (320, 240)})
picam2.configure(config)
picam2.set_controls({"ExposureTime": 10000, "AnalogueGain": 1.0})

# Start the camera
picam2.start()

# Capture an image
frame = picam2.capture_array()
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

# Display the captured frame
cv2.imshow("Camera Image", frame)
cv2.waitKey(0)  # Wait for a key press to exit

# Clean up
picam2.close()
cv2.destroyAllWindows()
