import cv2
from picamera2 import Picamera2
from threading import Thread, Lock

class Camera:
    def __init__(self, resolution=(640, 480), framerate=30):
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": resolution}))
        self.frame = None
        self.frame_lock = Lock()
        self.running = False
        self.framerate = framerate

    def start(self):
        self.picam2.start()
        self.running = True
        self.capture_thread = Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def capture_frames(self):
        while self.running:
            with self.frame_lock:
                self.frame = self.picam2.capture_array()
                self.frame = cv2.flip(self.frame, -1)
            time.sleep(1 / self.framerate)

    def stop(self):
        self.running = False
        self.picam2.close()

    def get_frame(self):
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
