import sys 
import os 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Vision')))

from Camera.camera import Camera
from Preprocessing.preprocessing import Preprocessing
from Detection.detection import DetectionBase
from Detection.shelf import Shelf
from Detection.marker import Marker
from Detection.wall import Wall
from Detection.packing_station import PackingStationRamp
from Detection.obstacle import Obstacle
from Detection.item import Item
from Calibration.calibration import Calibration
from threading import Thread
import cv2
import time


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
MARKERS = 0b010000
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
        print(self.homography_matrix)
        self.shelf_detector = Shelf(homography_matrix=self.homography_matrix)
        self.marker_detector = Marker()
        self.wall_detector = Wall()
        self.ramp_detector = PackingStationRamp(focal_length=300, homography_matrix=self.homography_matrix)  # Initialize the ramp detector
        self.obstacle_detector = Obstacle(focal_length=300, homography_matrix=self.homography_matrix)
        self.item_detector = Item()

        
        Thread(target=self.camera.live_feed, args=()).start()
        Thread(target=self.process_image_pipeline, args=()).start()
        return

    def process_image_pipeline(self):
        while True:
            frame = self.camera.get_frame()
            if frame is None:
                continue
            self.local_frame = frame.copy()
            now = time.time()
            # blurred_image = Preprocessing.preprocess(self.local_frame)
            if self.requested_objects & SHELVES:
                detected_shelves, shelf_frame, shelf_mask = self.shelf_detector.find_shelf(frame, self.color_ranges)
                cv2.imshow('Shelf Detection', shelf_frame)
                cv2.imshow('Shelf Mask', shelf_mask)
                self.objectRB[2] = detected_shelves # [[[R,B],[R,B]],[[R,B],[R,B]],...]

            if self.requested_objects & WALLPOINTS:
                detected_walls, filled_wall_mask, wall_mask = self.wall_detector.find_wall(frame,  self.color_ranges)
                cv2.imshow('Wall Mask', filled_wall_mask)
                self.objectRB[5] = detected_walls # [[R,B],[R,B],...]

            if self.requested_objects & MARKERS:
                detected_markers, marker_frame, marker_mask = self.marker_detector.find_marker(frame, filled_wall_mask,  self.color_ranges)
                cv2.imshow('Marker Detection', marker_frame)
                cv2.imshow('Marker Mask', marker_mask)
                self.objectRB[1] = detected_markers # [[R,B,T],[R,B,T]]

            if self.requested_objects & PACKING_BAY:
                detected_ramp, ramp_frame, ramp_mask = self.ramp_detector.find_packing_station_ramp(frame,  self.color_ranges)  # Ramp detection
                cv2.imshow('Ramp Detection', ramp_frame)
                cv2.imshow('Ramp Mask', ramp_mask)
                self.objectRB[0] = detected_ramp # [[R,B],[R,B],...]

            if self.requested_objects & OBSTACLES:
                detected_obstacles, obstacle_frame, obstacle_mask = self.obstacle_detector.find_obstacle(frame,  self.color_ranges)
                cv2.imshow('Obstacle Detection', obstacle_frame)
                cv2.imshow('Obstacle Mask', obstacle_mask)
                self.objectRB[4] = detected_obstacles # [[R,B],[R,B],...]

            if self.requested_objects & ITEMS:
                detected_items, item_frame, item_mask = self.item_detector.find_item(frame,  self.color_ranges)
                cv2.imshow('Item Detection', item_frame)
                cv2.imshow('Item Mask', item_mask)
                self.objectRB[3] = detected_items # [[R,B,L],[R,B,L],...]

                # # Display the detection results
                # self.objectRB[2] = [] # packing the RB into the RB

            elapsed = time.time() - now
            fps = 1/elapsed
            print('Time: ', elapsed, ' - FPS: ',fps)
            cv2.waitKey(1)
            # display the frame
            # self.camera.display_frame(frame)

    
    # def process_category(self, category, blurred_image, lower_hsv, upper_hsv, image_width, output_data):
        
    #     return 

    def __del__(self):
        self.camera.close()
        cv2.destroyAllWindows()
        return