import time
import picamera2
import cv2

# Initialize and configure the camera with a wider resolution for a better field of view
picam2 = picamera2.Picamera2()
picam2.configure(picam2.create_video_configuration(main={"format": 'XBGR8888', "size": (1920, 1080)}))  # Full HD resolution

# Increase exposure time and gain to brighten the image
picam2.set_controls({
    "AnalogueGain": 4.0,           # Increase gain for brighter images (higher ISO equivalent)
    "ExposureTime": 50000,         # Increase exposure time in microseconds (1/20th of a second)
    "ColourGains": (1.8, 2.2),     # Adjust ColourGains for better color balance
    "AeEnable": False,             # Disable auto exposure
    "AwbEnable": False             # Disable auto white balance
})

# Start the camera
picam2.start()

# Allow the camera to stabilize
time.sleep(1)

# Create a window for the video feed
cv2.namedWindow("Camera Feed")

# Capture and display video frames
while True:
    frame = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)
    
    cv2.imshow("Camera Feed", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
picam2.close()
cv2.destroyAllWindows()
