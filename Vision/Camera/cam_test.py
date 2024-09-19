import cv2
import os
import sys
import time
from threading import Thread

# define the system path "../../"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Vision.Camera.camera import Camera
from mobility.WASDMOTION import WASDMotion


def main():
    camera = Camera()
    mobility = WASDMotion()

    try:
        # Create and start the mobility thread
        mobility_thread = Thread(target=mobility.start)
        mobility_thread.daemon = True
        mobility_thread.start()

        # Create and start the camera thread
        # camera_thread = Thread(target=camera.capture_video, kwargs={'duration': 15})
        # camera_thread.daemon = True
        # camera_thread.start()
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
        camera.capture_video(duration=300)

    finally:
        camera.close()

    # Stop the robot in 10 seconds
    print("Stopping the robot in 10 seconds...")
    time.sleep(10)
    
    mobility.stop()


if __name__ == "__main__":
    main()
