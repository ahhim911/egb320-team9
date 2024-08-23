import cv2
import picamera2

# Initialize the camera with high resolution and wide FOV
def initialize_camera(frame_height=1080, frame_width=1920, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    #picam2.set_controls({"ColourGains": (1.4, 1.5)})  # Adjust color gains as needed
    picam2.start()
    return picam2

# Initialize the camera
cap = initialize_camera()

# Image counter for saving images with unique names
image_counter = 0

try:
    while True:
        # Capture a frame from the camera
        frame = cap.capture_array()

        # Apply any rotation or resize if needed
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # Display the captured frame
        cv2.imshow("High-Resolution Camera Image", frame)

        # Wait for a key press for 1ms
        key = cv2.waitKey(1) & 0xFF

        # If 'c' is pressed, capture and save the image
        if key == ord('c'):
            image_name = f"captured_image_{image_counter}.png"
            cv2.imwrite(image_name, frame)
            print(f"Image saved as {image_name}")
            image_counter += 1

        # If 'q' is pressed, exit the loop
        elif key == ord('q'):
            break

finally:
    # Clean up
    cap.close()
    cv2.destroyAllWindows()
