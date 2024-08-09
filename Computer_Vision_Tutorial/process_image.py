import cv2
import picamera2
import numpy as np

# Initialize the camera with custom settings
def initialize_camera(frame_height=480*2, frame_width=320*2, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({"ColourGains": (1.4, 1.5)})
    picam2.start()
    return picam2

# Initialize the camera
picam2 = initialize_camera()

# Define the HSV ranges for color thresholding
blue_lower = np.array([90, 50, 50])
blue_upper = np.array([130, 255, 255])

green_lower = np.array([35, 50, 50])
green_upper = np.array([85, 255, 255])

orange_lower = np.array([10, 100, 100])
orange_upper = np.array([25, 255, 255])

# Create a window to display the video feed
cv2.namedWindow('Video Feed')

# Initialize a variable to store the captured frame
captured_frame = None

try:
    while True:
        if captured_frame is None:
            # Capture an image from the camera
            frame = picam2.capture_array()

            # Pre-processing: Resize, flip to correct orientation, and display
            frame = cv2.resize(frame, (640, 480))  # Higher resolution for clarity
            frame = cv2.flip(frame, -1)  # Flip both horizontally and vertically

            # Display the video feed
            cv2.imshow('Video Feed', frame)

            # Check for key presses
            key = cv2.waitKey(1) & 0xFF

            # If 'c' is pressed, capture the current frame
            if key == ord('c'):
                captured_frame = frame.copy()  # Save the current frame
                cv2.imwrite('captured_frame.png', captured_frame)  # Save to disk
                print("Frame captured and saved as 'captured_frame.png'.")

                # Stop displaying the video feed
                cv2.destroyWindow('Video Feed')

        else:
            # Convert the captured frame to HSV color space
            hsv_frame = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2HSV)

            # Apply color thresholding to isolate blue, green, and orange regions
            blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
            green_mask = cv2.inRange(hsv_frame, green_lower, green_upper)
            orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

            # Combine the masks to focus on all specified colors
            combined_mask = cv2.bitwise_or(blue_mask, green_mask)
            combined_mask = cv2.bitwise_or(combined_mask, orange_mask)

            # Apply the mask to the captured frame
            masked_frame = cv2.bitwise_and(captured_frame, captured_frame, mask=combined_mask)

            # Perform edge detection on the masked frame
            gray_frame = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_frame, 100, 200)

            # Find contours from the edge-detected image
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw the contours on the captured image
            contour_image = captured_frame.copy()
            cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

            # Display the captured image, masked image, and contours
            cv2.imshow('Captured Image', captured_frame)
            cv2.imshow('Masked Image', masked_frame)
            cv2.imshow('Processed Image (Edges)', edges)
            cv2.imshow('Contours', contour_image)

            # Check for key presses to exit
            key = cv2.waitKey(1) & 0xFF

            # If 'q' is pressed, exit the loop
            if key == ord('q'):
                break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
