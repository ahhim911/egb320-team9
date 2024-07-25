import cv2
import numpy as np
from picamera2 import Picamera2

# Global variables for homography
image_points = []
found_homography = False
M = None

def onClick(event, x, y, flags, params):
    global image_points, found_homography, M
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked coordinates: ({x}, {y})")
        if not found_homography:
            image_points.append([x, y])
            if len(image_points) == 4:
                M, mask = cv2.findHomography(np.float32(image_points).reshape(-1, 1, 2), ground_points.reshape(-1, 1, 2))
                found_homography = True
                print("Homography matrix found:")
                print(M)
        else:
            print("Predicted ground point:")
            pred_point = cv2.perspectiveTransform(np.float32([[x, y]]).reshape(-1, 1, 2), M)
            print(pred_point)

# Define ground plane points relative to the robot (in meters)
ground_points = np.float32([[-6, 10], [-6, 22], [6, 22], [6, 10]])

# Initialize the camera
cap = Picamera2()
config = cap.create_video_configuration(main={"format": 'XRGB8888', "size": (820, 616)})
cap.configure(config)
cap.start()

# Create a window and set mouse callback for homography point selection
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", onClick)

try:
    while True:
        # Capture an image
        frame = cap.capture_array()

        # Rotate the image by 180 degrees
        frame = cv2.flip(frame, -1)  # Flip both horizontally and vertically

        # Display the image
        cv2.imshow("Image", frame)

        # Check if homography has been found or needs to be calculated
        if len(image_points) == 4 and not found_homography:
            M, mask = cv2.findHomography(np.float32(image_points).reshape(-1, 1, 2), ground_points.reshape(-1, 1, 2))
            found_homography = True
            print("Found homography matrix:")
            print(M)

		if found_homography == True:
			if event == cv2.EVENT_LBUTTONDOWN:
				print(f"Clicked coordinates: ({x}, {y})")
				
        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    cap.close()
    cv2.destroyAllWindows()
