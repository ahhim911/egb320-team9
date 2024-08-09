import cv2
import numpy as np
import picamera2

# Known parameters
real_world_width = 0.05  # 5 cm object width in meters
distance_to_object = 0.3  # 30 cm distance to the object in meters

# Function to initialize the Raspberry Pi camera
def initialize_camera(frame_height=320*2, frame_width=240*2, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({"ColourGains": (1.4, 1.5)})
    picam2.start()
    return picam2

# Initialize the camera
picam2 = initialize_camera()

# Capture an image from the camera
frame = picam2.capture_array()

# Convert the image to HSV color space
hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Define the HSV range for the blue color of the object
blue_lower = np.array([100, 150, 50])
blue_upper = np.array([130, 255, 255])

# Create a mask for the blue object
blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)

# Find contours in the mask
contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Check if any contour was found
if len(contours) == 0:
    print("Error: No blue object detected.")
    picam2.close()
    exit()

# Assume the largest contour is the object
contour = max(contours, key=cv2.contourArea)

# Get the bounding box around the object
x, y, w, h = cv2.boundingRect(contour)

# Calculate focal length
focal_length = (w * distance_to_object) / real_world_width
print(f"Calculated Focal Length: {focal_length:.2f} pixels")

# Optional: Display the image with the bounding box for visual verification
cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
cv2.imshow("Detected Object", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Clean up
picam2.close()
