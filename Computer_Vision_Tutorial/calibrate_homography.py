import cv2
import numpy as np
import csv
from picamera2 import Picamera2

# Global variables for calibration
homography_matrix = None
image_points = []
found_homography = False
captured_image = None

# Define the angle in degrees
angle_deg = 30

# Convert the angle to radians
angle_rad = np.radians(angle_deg)

# Ground plane points relative to the camera (for homography calibration)
#ground_points = np.float32([
#    [-0.20 * np.sin(angle_rad), 0.20 * np.cos(angle_rad)],
#    [0.20 * np.sin(angle_rad), 0.20 * np.cos(angle_rad)],
#    [0.35 * np.sin(angle_rad), 0.35 * np.cos(angle_rad)],
#    [-0.35 * np.sin(angle_rad), 0.35 * np.cos(angle_rad)]
#])
ground_points = np.float32([
    [-0.06, 0.20],
    [0.09, 0.20],
    [0.19, 0.50],
    [-0.16, 0.50]
])

# Function to handle mouse click events for homography calibration
def onClick(event, x, y, flags, params):
    global image_points, found_homography, homography_matrix
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked coordinates: ({x}, {y})")
        if not found_homography:
            image_points.append([x, y])
            if len(image_points) == 4:
                # Compute the homography matrix
                homography_matrix, _ = cv2.findHomography(np.float32(image_points).reshape(-1, 1, 2), ground_points.reshape(-1, 1, 2))
                found_homography = True
                print("Homography matrix found:")
                print(homography_matrix)
        else:
            print("Homography already calibrated.")

# Function to save homography matrix to a CSV file
def save_homography(homography_matrix):
    with open("calibrate_homography.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Homography Matrix"])
        for row in homography_matrix:
            writer.writerow(row)
    print("Homography matrix saved to calibrate_homography.csv")

# Function to resize the captured image
def resize_image(image, scale=0.5):
    return cv2.resize(image, (0, 0), fx=scale, fy=scale)

def main():
    global captured_image

    # Initialize the Picamera2 feed
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()
    
    while True:
        frame = picam2.capture_array()
        frame = cv2.flip(frame, -1)  # Flip horizontally and vertically
        cv2.imshow("Live Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):  # Capture the image if 'c' is pressed
            captured_image = frame.copy()
            captured_image = resize_image(captured_image)  # Resize the captured image
            print("Image captured!")
            cv2.destroyWindow("Live Feed")
            break

    # If an image was captured, display it in a new window and perform calibration steps
    if captured_image is not None:
        cv2.imshow("Captured Image", captured_image)
        cv2.setMouseCallback("Captured Image", onClick, captured_image)

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):  # Exit the loop if 'q' is pressed
                break
            elif key == ord('s'):  # Save the homography matrix if 's' is pressed
                if homography_matrix is not None:
                    save_homography(homography_matrix)
                    print("Calibration data saved.")
                else:
                    print("Ensure the homography matrix is calibrated before saving.")

    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
