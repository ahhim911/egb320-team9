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
            # Display the captured image
            cv2.imshow('Captured Image', captured_frame)

            # Perform image processing on the captured frame
            gray_frame = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_frame, 100, 200)

            # Find contours from the edge-detected image
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw the contours on the captured image
            contour_image = captured_frame.copy()
            cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

            # Display the processed image (edges)
            cv2.imshow('Processed Image (Edges)', edges)

            # Display the image with contours drawn
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
