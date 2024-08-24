import cv2
import picamera2
import numpy as np

# Initialize the camera with high resolution and wide FOV
def initialize_camera(frame_height=1080, frame_width=1920, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({
        "ExposureTime": 15000,  # Adjust based on your environment
        "AnalogueGain": 1.0,    # Adjust the gain; lower values reduce noise
        "ColourGains": (1.4, 1.5)  # Adjust color gains as needed
    })
    picam2.start()
    return picam2

# Define HSV color ranges for different objects
color_ranges = {
    "orange_item": ([10, 100, 100], [25, 255, 255]),  # Orange
    "green_obstacle": ([35, 100, 100], [79, 255, 255]),  # Green
    "blue_shelf": ([80, 100, 100], [130, 255, 255]),  # Blue
    "yellow_packing_station": ([20, 100, 100], [30, 255, 255]),  # Yellow
    "black_marker": ([0, 0, 0], [179, 255, 30]),  # Black
    "white_wall": ([0, 0, 231], [179, 18, 255]),  # White
    "grey_floor": ([0, 0, 50], [179, 18, 230])  # Grey
}

# Initialize the camera
cap = initialize_camera()

# Function to detect objects based on color ranges
def detect_objects(frame, hsv_frame, color_name, lower_hsv, upper_hsv):
    mask = cv2.inRange(hsv_frame, np.array(lower_hsv), np.array(upper_hsv))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Filter out small contours
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)  # Black rectangle
            cv2.putText(frame, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    return frame

try:
    while True:
        # Capture a frame from the camera
        frame = cap.capture_array()

        frame = cv2.flip(frame, 0)  # Flip the image

        # Convert the frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Detect and label each object based on its color
        for color_name, (lower_hsv, upper_hsv) in color_ranges.items():
            frame = detect_objects(frame, hsv_frame, color_name, lower_hsv, upper_hsv)

        # Display the frame with detected objects
        cv2.imshow("Object Detection", frame)

        # Wait for a key press for 1ms
        key = cv2.waitKey(1) & 0xFF

        # If 'q' is pressed, exit the loop
        if key == ord('q'):
            break

finally:
    # Clean up
    cap.close()
    cv2.destroyAllWindows()
