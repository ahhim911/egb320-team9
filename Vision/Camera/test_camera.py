import cv2
from camera import Camera 

def main():
    camera = Camera()
    try:
        # Capture and display a frame
        # frame = camera.capture_frame()
        # cv2.imshow('Captured Frame', frame)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Save an image
        # camera.capture_image()
        # camera.capture_image('test_image.png')

        # Record a video for 5 seconds
        # camera.capture_video(duration=5)
        camera.capture_video(duration=30)

    finally:
        camera.close()

if __name__ == "__main__":
    main()
