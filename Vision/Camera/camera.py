import cv2
import numpy as np
import os
from picamera2 import Picamera2
from libcamera import Transform
import time
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

class Camera:
    def __init__(self, config=None):
        self.picam2 = Picamera2()
        if config is None:
            config = self.picam2.create_preview_configuration(
                main={"format": "XRGB8888", "size": (820, 616)},
                transform=Transform(vflip=True, hflip=True)
                )
        self.picam2.configure(config)
        self.picam2.start()
    
    def capture_frame(self):
        """Capture a single frame."""
        frame = self.picam2.capture_array()
        # frame = cv2.flip(frame, -1)  # Flip horizontally and vertically if needed
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

    def capture_video(self, filename=None, duration=5, preview=True):
        if filename is None:
            filename = time.strftime("video_%Y%m%d_%H%M%S.mp4")
        filepath = os.path.join("Videos", filename)
        if not os.path.exists("Videos"):
            os.makedirs("Videos")


        # Stop the camera before reconfiguring
        self.picam2.stop()

        # Configure video recording with vertical flip
        video_config = self.picam2.create_video_configuration(
            main={"size": (820, 616)},
            transform=Transform(vflip=True, hflip=True)
        )
        self.picam2.configure(video_config)

        # Create the encoder and output for MP4
        encoder = H264Encoder(bitrate=10000000)
        output = FfmpegOutput(filepath)

        # Start the camera
        self.picam2.start()

        # Start recording
        self.picam2.start_recording(encoder, output)
        print(f"Recording video to {filepath} for {duration} seconds...")
        
        if preview == True:
            # Start time for duration control
            start_time = time.time()
            while (time.time() - start_time) < duration:
                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    print("Error: Frame not captured.")
                    break

                # Convert color format from RGB to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Display the frame
                cv2.imshow('Recording...', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


        # Stop recording
        self.picam2.stop_recording()
        print(f"Video saved to {filepath}")

        # Close the OpenCV window
        cv2.destroyAllWindows()


        return filepath


    def close(self):
        """Close the camera and release resources."""
        self.picam2.close()
