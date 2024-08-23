import cv2
import numpy as np

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
                # Compute the homography matrix
                M, mask = cv2.findHomography(np.float32(image_points).reshape(-1, 1, 2), ground_points.reshape(-1, 1, 2))
                found_homography = True
                print("Homography matrix found:")
                print(M)
        else:
            print("Predicted ground point:")
            pred_point = cv2.perspectiveTransform(np.float32([[x, y]]).reshape(-1, 1, 2), M)
            print(pred_point)

# Define ground plane points relative to the robot (in meters)
ground_points = np.float32([[-40, 100], [40, 100], [40, 70], [-40, 70]])

# Load the image from file
frame = cv2.imread('captured_image_3.png')

# Create a window and set mouse callback for homography point selection
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", onClick)

try:
    while True:
        # Display the image
        cv2.imshow("Image", frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
