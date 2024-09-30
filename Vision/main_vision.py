from Camera.camera import Camera
from Preprocessing.preprocessing import Preprocessing
from Detection.detection import DetectionBase
from Calibration.calibration import Calibration
from threading import Thread
import cv2


"""
process_category(category, blurred_image, lower_hsv, upper_hsv, image_width, output_data)
- Process the category of the detected object.
- Apply color thresholding and morphological filters.
- Analyze contours and classify objects based on category.
- Return the classified objects.

process_image_pipeline(camera, color_ranges, calibration)
- Process the image pipeline.
- Capture frames from the camera.
- Preprocess the frame.
- Run the processing pipeline in parallel.
- Display the processed frame.
- Break the loop if 'q' is pressed.
- Close the camera and destroy all windows.

main()
- Create a camera object.
- Load the calibration data.
- Process the image pipeline.
- Close the camera and destroy all windows.

"""

class Vision(DetectionBase):
    def __init__(self):
        self.objectRB = None
        self.requested_object = None
        self.camera = Camera()

        self.calibration = Calibration()

    # def process_category(self, category, blurred_image, lower_hsv, upper_hsv, image_width, output_data):
        
    #     return 

    def process_image_pipeline(self, camera, color_ranges):
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
            
            blurred_image = Preprocessing.preprocess(frame)
        return

    def start(self):
        self.color_ranges, homography_matrix, focal_length = self.calibration.load_csv()
        Thread(target=self.camera.capture_frame, args=(self.camera, self.color_ranges)).start()
        Thread(target=self.process_image_pipeline, args=(self.camera, self.color_ranges, self.calibration)).start()
        return self
    

    def __del__(self):
        self.camera.close()
        cv2.destroyAllWindows()
        return