import cv2
import os
from preprocessing import Preprocessing  # Ensure the path is correct for your Preprocessing class

"""
test preprocessing.py library with image and video
"""


def is_video(file_path):
    """Check if the given file is a video based on its extension."""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in video_extensions

def load_image(image_path):
    """Load the image from the path and return the frame."""
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Unable to load image {image_path}")
        return None
    return frame

def preprocess_image(image):
    """Preprocess and display an image."""
    if image is None:
        print("Error: No image to process.")
        return

    # Apply full preprocessing pipeline
    preprocessed_image = Preprocessing.preprocess(image, resize_to=(640, 480), blur_ksize=(5, 5), sigmaX=2)

    # Display the original and preprocessed images
    cv2.imshow('Original Image', image)
    cv2.imshow('Preprocessed Image', preprocessed_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def preprocess_video(video_path):
    """Preprocess each frame of a video and display live preview."""
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video {video_path}")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Apply full preprocessing pipeline to each frame
        preprocessed_frame = Preprocessing.preprocess(frame, resize_to=(640, 480), blur_ksize=(5, 5), sigmaX=2)

        # Display the original and preprocessed frames
        cv2.imshow('Original Frame', frame)
        cv2.imshow('Preprocessed Frame', preprocessed_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run_preprocessing(file_path):
    """Run preprocessing on either an image or video based on the file type."""
    if os.path.isfile(file_path):
        if is_video(file_path):
            print(f"Processing video: {file_path}")
            preprocess_video(file_path)
        else:
            print(f"Processing image: {file_path}")
            image = load_image(file_path)
            preprocess_image(image)
    else:
        print(f"Error: File {file_path} does not exist.")

def main():
    # Replace with your file path (video or image)
    file_path = '/home/edmond3321/egb320-team9/Vision/Camera/Videos/1_searching_left_1.mp4'
    run_preprocessing(file_path)

if __name__ == '__main__':
    main()
