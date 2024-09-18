import cv2
import numpy as np
import os
from picamera2 import Picamera2
import time

class Camera:
    def __init__(self, config=None):
        self.picam2 = Picamera2()
        if config is None:
            config = self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)})
        self.picam2.configure(config)
        self.picam2.start()
    
    def capture_frame(self):
        """Capture a single frame."""
        frame = self.picam2.capture_array()
        frame = cv2.flip(frame, -1)  # Flip horizontally and vertically if needed
        return frame

    def capture_image(self, filename=None):
        """Capture an image and save it to the Images folder."""
        if filename is None:
            filename = time.strftime("image_%Y%m%d_%H%M%S.png")
        filepath = os.path.join("Images", filename)
        if not os.path.exists("Images"):
            os.makedirs("Images")
        frame = self.capture_frame()
        cv2.imwrite(filepath, frame)
        print(f"Image saved to {filepath}")
        return filepath

    def capture_video(self, filename=None, duration=5):
        """Capture a video and save it to the Videos folder."""
        if filename is None:
            filename = time.strftime("video_%Y%m%d_%H%M%S.avi")
        filepath = os.path.join("Videos", filename)
        if not os.path.exists("Videos"):
            os.makedirs("Videos")
        
        frame_width = int(self.picam2.stream_configuration("main")["size"][0])
        frame_height = int(self.picam2.stream_configuration("main")["size"][1])

        fourcc = cv2.VideoWriter_fourcc(*'XVID') # type: ignore
        out = cv2.VideoWriter(filepath, fourcc, 20.0, (frame_width, frame_height))

        start_time = time.time()
        while (time.time() - start_time) < duration:
            frame = self.capture_frame()
            out.write(frame)
            time.sleep(0.05)  # Adjust sleep for desired FPS

        out.release()
        print(f"Video saved to {filepath}")
        return filepath

    def close(self):
        """Close the camera and release resources."""
        self.picam2.close()
