import time
import cv2
from picamera2 import Picamera2
from base_camera import BaseCamera
from libcamera import Transform
import numpy as np

def initialize_camera(frame_height=320*2, frame_width=320*2, format='XRGB8888'):
    try:
        cap = Picamera2()
        config = cap.create_video_configuration(
            main={"format": format, "size": (frame_width, frame_height)},
            transform=Transform(vflip=True, hflip=True)
        )
        cap.configure(config)
        cap.start()
        return cap
    except Exception as e:
        print("Failed to initialize camera:", e)
        return None

class Camera(BaseCamera):
    # def __init__(self):
    #     super().__init__()
    #     self.cap = initialize_camera()
    #     if not self.cap:
    #         raise RuntimeError("Failed to initialize camera.")
    #     time.sleep(2)  # Allow the camera to warm up

    # def __del__(self):
    #     try:
    #         if hasattr(self, 'cap') and self.cap:
    #             self.cap.stop()
    #     except Exception as e:
    #         print("Error stopping camera:", e)

    # def get_frame(self, hsv_values):
    #     # This method should call the frames generator and return the next frame
    #     BaseCamera.last_access = time.time()
        
    #     # Wait for a signal from the camera thread
    #     BaseCamera.event.wait()
    #     BaseCamera.event.clear()

    #     try:
    #         # Use the instance method frames to get the next frame
    #         frame = next(self.frames(hsv_values))
    #         return frame
    #     except StopIteration:
    #         return None

    @staticmethod
    def frames(hsv_values):
        cap = initialize_camera()

        if not cap:
            raise RuntimeError("Cannot start camera frames generator; initialization failed.")

        try:
            while True:
                # Capture a frame from the camera
                frame = cap.capture_array()

                # Convert the frame to the HSV color space
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Get current HSV values
                lower = np.array([hsv_values['hMin'], hsv_values['sMin'], hsv_values['vMin']])
                upper = np.array([hsv_values['hMax'], hsv_values['sMax'], hsv_values['vMax']])

                # Create a mask based on the HSV range
                mask = cv2.inRange(hsv, lower, upper)

                # Apply the mask to the frame to get the result
                result = cv2.bitwise_and(frame, frame, mask=mask)

                # Encode the result image as JPEG
                ret, jpeg = cv2.imencode('.jpg', result)
                if not ret:
                    continue

                # Yield the encoded JPEG
                yield jpeg.tobytes()

        finally:
            if cap:
                cap.stop()
