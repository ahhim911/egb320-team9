import cv2
import numpy as np
import os
from picamera2 import Picamera2
from libcamera import Transform # type: ignore
import time
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import ctypes
import logging
from threading import Event

# Initialize Xlib threading for multi-threaded GUI operations
ctypes.CDLL('libX11.so').XInitThreads()

logger = logging.getLogger(__name__)

class Camera:
    def __init__(self, config=None):
        """
        Initialize the camera and configure it.
        """
        logger.info("Initializing camera...")
        self.HSVframe = None
        self.RGBframe = None
        self.picam2 = None
        self.stop_event = Event()

        try:
            self.picam2 = Picamera2()
            if config is None:
                config = self.picam2.create_preview_configuration(
                    main={"format": "XRGB8888", "size": (820, 616)},
                    transform=Transform(vflip=True, hflip=True)
                )
            self.picam2.configure(config)  # type: ignore
            self.picam2.start()
            self.picam2.set_controls({"AnalogueGain": 1, "ColourGains": (1.4, 1.5)})
            self.running = True
            logger.info("Camera initialization complete.")
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            self.running = False
            raise

    def live_feed(self, stop_event):
        """
        Capture live feed from the camera and update the frames.
        """
        logger.info("Starting live feed...")
        while self.running and not stop_event.is_set():
            try:
                self.RGBframe = cv2.resize(self.picam2.capture_array(), (0, 0), fx=0.5, fy=0.5)
                self.HSVframe = cv2.cvtColor(self.RGBframe, cv2.COLOR_BGR2HSV)
            except Exception as e:
                logger.error(f"Error during live feed capture: {e}")
                break
            
    
    def get_frame(self):
        """
        Return the current frames (RGB and HSV).
        """
        #logger.debug("Getting current frame.")
        return self.RGBframe, self.HSVframe
    
    def display_frame(self, frame):
        """Display a single frame."""
        try:
            if frame is not None:
                cv2.imshow('Frame', frame)
                cv2.waitKey(1)
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def capture_frame(self):
        """Capture a single frame."""
        try:
            frame = self.picam2.capture_array()
            cv2.imshow("Frame",frame)
            return frame
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None

    def capture_image(self, filename=None):
        """Capture an image and save it to the Images folder."""
        try:
            if filename is None:
                filename = time.strftime("image_%Y%m%d_%H%M%S.png")
            filepath = os.path.join("Images", filename)
            if not os.path.exists("Images"):
                os.makedirs("Images")
            frame = self.capture_frame()
            if frame is not None:
                cv2.imwrite(filepath, frame)
                print(f"Image saved to {filepath}")
            else:
                print("Error: Frame not captured.")
            return filepath
        except Exception as e:
            print(f"Error saving image: {e}")
            return None

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
        self.picam2.configure(video_config) # type: ignore

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

    def play_video(self, video_path, loop=True):
        """Play a video as if it is a live feed."""
        cap = cv2.VideoCapture(video_path)
        time.sleep(2)
        if not cap.isOpened():
            print(f"Error: Unable to open video file {video_path}")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
                    continue
                else:
                    break

            # Resize frame if needed (similar to live_feed)
            self.RGBframe = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5) #capture_frame()
            self.HSVframe = cv2.cvtColor(self.RGBframe, cv2.COLOR_BGR2HSV)


            # Simulate real-time frame rate (adjust sleep for desired speed)
            #time.sleep(1 / 30)  # Assuming 30 FPS playback

            #if cv2.waitKey(1) & 0xFF == ord('q'):
                #break

        cap.release()
        cv2.destroyAllWindows()


    def close(self):
        """
        Close the camera and release resources.
        """
        logger.info("Closing the camera.")
        self.stop_event.set()  # Signal the live_feed to stop
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
        cv2.destroyAllWindows()

    def __del__(self):
        self.close()
