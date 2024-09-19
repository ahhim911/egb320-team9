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

    
    # Create and start the threads
    mobility_thread = Thread(target=mobility.start(), args=())
    mobility_thread.daemon = True
    mobility_thread.start()

    # Camera Threads Capture video
    camera_thread = Thread(target=camera.capture_video(duration=15), args=())
    camera_thread.daemon = True
    camera_thread.start()


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
