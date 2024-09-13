import cv2
from live_detection4 import (
    load_color_thresholds,
    load_homography_matrix,
    load_focal_length,
    process_frame
)

def main():
    # Load calibration data
    color_ranges = load_color_thresholds('calibrate.csv')
    load_homography_matrix('calibrate_homography.csv')
    load_focal_length('calibrate_focal_length.csv')

    # Load the image
    frame = cv2.imread('captured_image_0.png')
    if frame is None:
        print(f"Error: Unable to load image 'captured_image0.png'")
        return

    # Process the image frame
    process_frame(frame, color_ranges)

    # Wait a short time and then close all OpenCV windows
    cv2.waitKey(0)  # Wait or adjust the time as needed
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
