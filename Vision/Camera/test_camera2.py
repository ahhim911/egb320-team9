import cv2
from picamera2 import Picamera2

def main():
    # Initialize Picamera2
    picam2 = Picamera2()
    
    # Configure the camera settings (preview or low resolution)
    camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(camera_config)
    
    # Start the camera
    picam2.start()
    
    # Create an OpenCV window to display the video feed
    cv2.namedWindow("Camera Feed", cv2.WINDOW_AUTOSIZE)
    
    while True:
        # Capture frame-by-frame
        frame = picam2.capture_array()
        
        # Convert the image to BGR format (required by OpenCV)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Display the resulting frame
        cv2.imshow("Camera Feed", frame_bgr)
        
        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Stop the camera
    picam2.stop()
    
    # Release the OpenCV window
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
