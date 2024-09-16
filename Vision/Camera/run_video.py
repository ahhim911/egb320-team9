import cv2
import numpy as np
#from Vision.main_vision import process_image_pipeline

def run_test_video(file_name='test_video.mp4',file_path='Videos/'):

    cap = cv2.VideoCapture(file_path + file_name)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        cv2.imshow('Playing...', frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    run_test_video(file_name='1_going_row3_2.mp4')

if __name__ == '__main__':
    main()