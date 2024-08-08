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

# Resize and rotate the frame for display
frame = cv2.resize(frame, (320, 240))
frame = cv2.rotate(frame, cv2.ROTATE_180)

# Display the captured frame
cv2.imshow("Camera Image", frame)
cv2.waitKey(0)  # Wait for a key press to exit

# Save the image
cv2.imwrite("captured_image.png", frame)

# Clean up
cap.close()
cv2.destroyAllWindows()
