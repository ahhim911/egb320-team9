import cv2
import numpy as np
import picamera2
from threading import Thread, Lock
import time

# Global variables for frame handling
frame = None
processed_frame = None
frame_lock = Lock()

def capture_frames(picam2):
    """Capture frames from the camera and store them in a global variable."""
    global frame
    while True:
        with frame_lock:
            frame = cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)
        time.sleep(0.01)  # Small delay to reduce CPU usage

def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    """Resize, flip horizontally and vertically, and apply Gaussian blur to the image."""
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    flipped_image = cv2.flip(resized_image, -1)  # Flip both horizontally and vertically
    return cv2.GaussianBlur(flipped_image, blur_ksize, sigmaX)

def color_threshold(image, lower_hsv, upper_hsv):
    """Apply color thresholding to segment specific colors in the image."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv_image, lower_hsv, upper_hsv)

def apply_morphological_filters(mask, kernel_size=(5, 5)):
    """Apply morphological operations to clean up the mask."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)

def analyze_contours(image, mask, category, min_area=500):
    """Analyze contours and draw bounding boxes for detected objects based on a minimum area threshold."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image = image.copy()

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        cv2.drawContours(contour_image, contour, -1, (255, 0, 0), 2)
        cv2.putText(contour_image, f"Area: {int(area)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return contour_image

def process_image_pipeline():
    """Image processing pipeline that preprocesses, thresholds, applies morphological filters, and performs contour analysis."""
    global frame, processed_frame
    while True:
        with frame_lock:
            if frame is None:
                continue
            local_frame = frame.copy()  # Copy the frame for local processing

        # Preprocess image
        blurred_image = preprocess_image(local_frame)

        processed_frames = []

        # Apply color thresholding, morphological filters, and analyze contours for each category
        for category, (lower_hsv, upper_hsv) in color_ranges.items():
            mask = color_threshold(blurred_image, lower_hsv, upper_hsv)
            processed_mask = apply_morphological_filters(mask)
            
            # Analyze contours for the current category
            contour_image = analyze_contours(local_frame, processed_mask, category)
            processed_frames.append((category, contour_image))

        with frame_lock:
            processed_frame = contour_image # Store the contour_image of the last category processed

# Predefined color ranges for different categories
color_ranges = {
    'Shelf': (np.array([97, 0, 15]), np.array([125, 255, 230])),
    'Obstacle': (np.array([34, 98, 28]), np.array([75, 255, 225])),
    'Item': (np.array([0, 150, 27]), np.array([14, 255, 255])),
    'Marker': (np.array([0, 0, 0]), np.array([155, 155, 70]))
}

def main():
    # Initialize and configure the camera
    picam2 = picamera2.Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"format": 'XBGR8888', "size": (1920, 1080)}))
    picam2.set_controls({
        "AnalogueGain": 5.0,
        "ExposureTime": 50000,
    })
    picam2.start()

    # Start the frame capture thread
    capture_thread = Thread(target=capture_frames, args=(picam2,))
    capture_thread.daemon = True
    capture_thread.start()

    # Start the image processing pipeline thread
    processing_thread = Thread(target=process_image_pipeline)
    processing_thread.daemon = True
    processing_thread.start()

    # Create a window for the video feed
    cv2.namedWindow("Camera Feed")

    # Display the processed frames
    while True:
        start_time = time.time()  # Start time for processing

        with frame_lock:
            if processed_frame is not None:
                cv2.imshow("Camera Feed", processed_frame)

        end_time = time.time()  # End time for processing
        processing_time = end_time - start_time  # Calculate processing time
        print(f"Processing time for frame: {processing_time:.4f} seconds")  # Print processing time

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up
    picam2.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
