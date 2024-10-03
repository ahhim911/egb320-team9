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
PACKING_BAY = 0b100000
ROW_MARKERS = 0b010000
SHELVES = 0b001000
ITEMS = 0b000100
OBSTACLES = 0b000010
WALLPOINTS = 0b000001
class Vision(DetectionBase):
    def __init__(self):
        """
        REQUESTED OBJECTS
        
        USAGE: Compare the requested_objects with the binary number to determine if the object is requested
        Example: if requested_objects & PACKING_BAY:
        """
        # order of objects: [Packing bay, Rowmarkers, Shelves, Items,  Obstacles, Wallpoints] 
        # co-responding to the binary number 0b000000
        self.objectRB = [None, None, None, None, None, None]
        self.requested_objects = 0b000000

        self.camera = Camera()

        self.calibration = Calibration()
        self.color_ranges = None
        self.homography_matrix = None
        self.focal_length = None

    def start(self):
        self.color_ranges, self.homography_matrix, self.focal_length = self.calibration.load_csv()
        Thread(target=self.camera.capture_frame, args=(self.camera, self.color_ranges)).start()
        Thread(target=self.process_image_pipeline, args=(self.camera, self.color_ranges, self.calibration,)).start()
        return

    def process_image_pipeline(self, self.camera, color_ranges):
        while True:
            frame = self.camera.get_frame()
            if frame is None:
                continue
            self.local_frame = frame.copy()
            
            blurred_image = Preprocessing.preprocess(self.local_frame)
            image_width = blurred_image.shape[1]
        return

    
    # def process_category(self, category, blurred_image, lower_hsv, upper_hsv, image_width, output_data):
        
    #     return 

    def __del__(self):
        self.camera.close()
        cv2.destroyAllWindows()
        return