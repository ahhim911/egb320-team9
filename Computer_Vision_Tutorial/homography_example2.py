import cv2
import numpy as np
from picamera2 import Picamera2

# Load the previously calculated homography matrix
# For this example, we'll assume you have saved the homography matrix `M` in a variable.
# Replace this with your actual homography matrix.
M = np.array([[ -1.98213666e-02,  5.25959025e-03, 6.59735964e+00],
              [ 2.75902675e-03,  1.38871335e-03,   -1.44504172e+01],
              [ 1.12711318e-04,   -4.39422194e-03,     1.0]])

def onClick(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked coordinates: ({x}, {y})")
        # Predict the ground point using the homography matrix
        point = np.array([[x, y]], dtype='float32')
        point = np.array([point])
        ground_point = cv2.perspectiveTransform(point, M)
        print(f"Predicted ground coordinates: {ground_point[0][0]}")

# Initialize the camera
cap = Picamera2()
config = cap.create_video_configuration(main={"format": 'XRGB8888', "size": (820, 616)})
cap.configure(config)
cap.start()

# Create a window and set mouse callback for ground point prediction
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

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    cap.close()
    cv2.destroyAllWindows()
