import cv2
from Vision.Camera.camera import Camera 
import os
import sys
from mobility.WASDMOTION import WASDMotion
import time

# define the system path "../../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


def main():
    camera = Camera()
    mobility = WASDMotion()

    mobility.start()
    time.sleep(1)
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
        camera.capture_video(duration=15)

    finally:
        camera.close()

if __name__ == "__main__":
    main()
