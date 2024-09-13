import io
import time
from picamera2 import Picamera2, Preview
from base_camera import BaseCamera

class Camera(BaseCamera):
    
    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # Wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frames()


    @staticmethod
    def frames():
        with Picamera2() as camera:
            camera.start()

            # let camera warm up
            time.sleep(2) 

            stream = io.BytesIO()
            try:
                while True:
                    camera.capture_file(stream, format='jpeg')
                    stream.seek(0)
                    yield stream.read()

                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()
            finally:
                camera.stop()