import cv2
import picamera2

# Initialize the camera
cap = picamera2.Picamera2()
config = cap.create_video_configuration(main={"format": 'XRGB8888', "size": (820, 616)})
cap.configure(config)
cap.set_controls({"ColourGains": (1.4, 1.5)})

# Start the camera
cap.start()
frame = cap.capture_array()
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

# Convert to different color spaces
hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)

# Display the frames
cv2.imshow("HSV Frame", hsv_frame)
cv2.imshow("Lab Frame", lab_frame)
cv2.waitKey(0)  # Wait for a key press to exit

# Clean up
cap.close()
cv2.destroyAllWindows()
