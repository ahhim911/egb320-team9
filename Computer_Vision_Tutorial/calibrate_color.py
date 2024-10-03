import numpy as np
import cv2
import time
from picamera2 import Picamera2

def resize_image(image, scale=0.5):
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    return resized_image

# Create a Picamera2 object
cap = Picamera2()

# Configure the camera
frameWidth, frameHeight = 820, 616
config = cap.create_video_configuration(main={"format": 'RGB888', "size": (frameWidth, frameHeight)})
cap.configure(config)

# Start the camera
cap.start()

captured_image = None  # Variable to store the captured image
valueHSV = set()  # This is a set of HSV values captured by the user

# Default color HSV ranges
color_ranges = {
    'orange': (np.array([0, 158, 45]), np.array([13, 255, 235])),
    'green': (np.array([40, 64, 11]), np.array([70, 255, 99])),
    'blue': (np.array([90, 136, 9]), np.array([120, 255, 94])),
    'black': (np.array([0, 0, 43]), np.array([179, 55, 109]))
}

# Variable to hold current color key
current_color_key = None

# Buffer to be applied to the HSV range
bufferHSV = np.array([255, 120, 120])

def add_point_in(point):
    global valueHSV
    valueHSV.add((point[0], point[1], point[2]))
    print(f"Point added for {current_color_key}: ", valueHSV)

def OnMouseClick(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        paramHSV = cv2.cvtColor(param, cv2.COLOR_BGR2HSV)
        add_point_in(paramHSV[y, x])
        update_thresh()

def update_thresh():
    global color_ranges, current_color_key, valueHSV, bufferHSV
    if current_color_key is not None and len(valueHSV) > 0:
        arr = np.array(list(valueHSV))
        lowerHSV = np.maximum(arr.min(0) - bufferHSV, 0)
        upperHSV = np.minimum(arr.max(0) + bufferHSV, 255)
        color_ranges[current_color_key] = (lowerHSV, upperHSV)
        print(f"Updated {current_color_key} HSV range with buffer: ", color_ranges[current_color_key])

        if captured_image is not None:
            captured_imageHSV = cv2.cvtColor(captured_image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(captured_imageHSV, color_ranges[current_color_key][0], color_ranges[current_color_key][1])
            cv2.imshow("Mask", cv2.bitwise_and(captured_image, captured_image, mask=mask))
    else:
        print(f"No points selected for {current_color_key}.")

def reset():
    global valueHSV
    valueHSV = set()
    print("Resetting points")

if __name__ == "__main__":
    while True:
        t1 = time.time()  # for measuring fps

        frame = cap.capture_array()  # Capture a single image frame
        frame = resize_image(frame)  # Resize image
        frame = cv2.flip(frame, -1)  # Flip horizontally and vertically

        # Display the obtained frame in a window called "CameraImage"
        cv2.imshow("Image", frame)
        cv2.waitKey(1)  # Make the program wait for 1ms before continuing (also required to display image).

        fps = 1.0 / (time.time() - t1)  # Calculate frame rate
        print("Frame Rate: ", int(fps), end="\r")

        key = cv2.waitKey(1) & 0xFF  # Wait for a key press

        if key == ord('c'):  # Capture the image if 'c' is pressed
            captured_image = frame.copy()
            print("Image captured!")
            cv2.destroyWindow("Image")
            break

    # If an image was captured, display it in a new window
    if captured_image is not None:
        cv2.imshow("Captured Image", captured_image)
        cv2.setMouseCallback("Captured Image", OnMouseClick, captured_image)
        cv2.waitKey(0)  # Wait until a key is pressed to close the window

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # Exit the loop if 'q' is pressed
            break
        elif key == ord('s'):  # Save the HSV range if 's' is pressed
            print("Saving color thresholds...")
            with open("calibrate.csv", "w") as file:
                for color, (lower, upper) in color_ranges.items():
                    lower_str = ','.join(map(str, lower))
                    upper_str = ','.join(map(str, upper))
                    file.write(f"{color},{lower_str},{upper_str}\n")
            print("Color thresholds saved to calibrate.csv")
        elif key == ord('r'):  # Reset the HSV range if 'r' is pressed
            reset()
            update_thresh()
        elif key == ord('1'):
            current_color_key = 'orange'
            print("Selected 'orange' for calibration")
            reset()
        elif key == ord('2'):
            current_color_key = 'green'
            print("Selected 'green' for calibration")
            reset()
        elif key == ord('3'):
            current_color_key = 'blue'
            print("Selected 'blue' for calibration")
            reset()
        elif key == ord('4'):
            current_color_key = 'black'
            print("Selected 'black' for calibration")
            reset()

    cap.close()
    cv2.destroyAllWindows()
