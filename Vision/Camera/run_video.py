import cv2
import numpy as np

def main():
    # Replace 'your_video.mp4' with the path to your video file
    file_path = 'Vision/Camera/Videos/'
    file_name = 'test_video.mp4'
    cap = cv2.VideoCapture(file_path + file_name)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Process the frame (insert your vision system's processing here)
        processed_frame = process_frame(frame)

        # Display the processed frame
        cv2.imshow('Processed Frame', processed_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def process_frame(frame):
    # Example processing: Convert to grayscale (replace with your processing code)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray_frame

if __name__ == '__main__':
    main()