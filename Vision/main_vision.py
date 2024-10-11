from .Camera.camera import Camera  # Refers to Camera module in the same Vision directory
from .Preprocessing.preprocessing import Preprocessing  # Preprocessing module within Vision
from .Detection.detection import DetectionBase
from .Detection.shelf import Shelf
from .Detection.marker import Marker
from .Detection.wall import Wall
from .Detection.packing_station import PackingStationRamp
from .Detection.obstacle import Obstacle
from .Detection.item import Item
from .Calibration.calibration import Calibration
from threading import Thread
import cv2
import time



"""
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
MARKERS = 0b010001
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
        self.objectRB = [[], [], [], [], [], []]
        self.requested_objects = 0b000000

        self.camera = Camera()

        self.calibration = Calibration()
        self.color_ranges = None
        self.homography_matrix = None
        self.focal_length = None

    def start(self, path):
        self.color_ranges, self.homography_matrix, self.focal_length = self.calibration.load_csv()
        self.shelf_detector = Shelf(homography_matrix=self.homography_matrix,draw=True)
        self.marker_detector = Marker(focal_length=300, draw=True)
        self.wall_detector = Wall(homography_matrix=self.homography_matrix,draw=True)
        self.ramp_detector = PackingStationRamp(homography_matrix=self.homography_matrix,draw=True)  # Initialize the ramp detector
        self.obstacle_detector = Obstacle(focal_length=300, homography_matrix=self.homography_matrix,draw=True)
        self.item_detector = Item(real_item_width=0.045, focal_length=300, draw=True)

        # Thread(target=self.camera.play_video, args=(path,)).start() # Recorded video from files
        Thread(target=self.camera.live_feed, args=()).start() # Live video from camera
        return
    
    def update_item(self, item_width):
        print("Item width Updated: ", item_width)
        self.item_detector = Item(real_item_width=item_width, focal_length=300, draw=True)
    
    def display_detection(self, window_name, frame):
        """
        Helper function to display frames for different detections.
        """
        if frame is not None:
            cv2.imshow(f'{window_name} Mask', frame)

    def process_image(self):
        RGBframe, HSVframe = self.camera.get_frame()
        if RGBframe is None or HSVframe is None:
            return self.objectRB
        # cv2.imshow("Frame", frame)
        if self.requested_objects & SHELVES:
            detected_shelves, shelf_frame, shelf_mask = self.shelf_detector.find_shelf(HSVframe, RGBframe, self.color_ranges)
            self.display_detection('Shelf', shelf_mask)
            # cv2.imshow('Shelf Detection', shelf_frame)
            #cv2.imshow('Shelf Mask', shelf_mask)
            #print("Process shelf",detected_shelves)
            self.objectRB[2] = detected_shelves # [[[R,B],[R,B]],[[R,B],[R,B]],...]

        if self.requested_objects & WALLPOINTS:
            detected_walls, wall_frame, filled_wall_mask = self.wall_detector.find_wall(HSVframe, RGBframe,  self.color_ranges)
            #self.display_detection('Wall', filled_wall_mask)
            # cv2.imshow('Wall Mask', filled_wall_mask)
            #print("Process wall", detected_walls)
            self.objectRB[5] = detected_walls # [[R,B],[R,B],...]
        
        
        if self.requested_objects & MARKERS:
            detected_markers, marker_frame, marker_mask = self.marker_detector.find_marker(HSVframe, RGBframe, self.color_ranges, filled_wall_mask=filled_wall_mask)
            #self.display_detection('Markers', marker_mask)
            #cv2.imshow('Marker Detection', marker_frame)
            # cv2.imshow('Marker Mask', marker_mask)
            #print("Process Markers", detected_markers)
            self.objectRB[1] = detected_markers # [[R,B,T],[R,B,T]]

        if self.requested_objects & PACKING_BAY:
            detected_ramp, ramp_frame, ramp_mask = self.ramp_detector.find_packing_station_ramp(HSVframe, RGBframe, self.color_ranges)  # Ramp detection
            # self.display_detection('Packing Bay', ramp_mask)
            #cv2.imshow('Ramp Detection', ramp_frame)
            #cv2.imshow('Ramp Mask', ramp_mask)
            #print("Process ramp", detected_ramp)
            self.objectRB[0] = detected_ramp # [[R,B],[R,B],...]

        if self.requested_objects & OBSTACLES:
            detected_obstacles, obstacle_frame, obstacle_mask = self.obstacle_detector.find_obstacle(HSVframe, RGBframe,  self.color_ranges)
            self.display_detection('Obstacles', obstacle_mask)
            #cv2.imshow('Obstacle Detection', obstacle_frame)
            #cv2.imshow('Obstacle Mask', obstacle_mask)
            #print("Process obstacles",detected_obstacles)
            self.objectRB[4] = detected_obstacles # [[R,B],[R,B],...]

        if self.requested_objects & ITEMS:
            detected_items, item_frame, item_mask = self.item_detector.find_item(HSVframe, RGBframe,  self.color_ranges)
            #self.display_detection('Items', item_mask)
            # cv2.imshow('Item Detection', item_frame)
            #cv2.imshow('Item Mask', item_mask)
            #print("Process item",detected_items)
            self.objectRB[3] = detected_items # [[R,B,L],[R,B,L],...]

        # Add State from State machine
        # cv2.putText(RGBframe, f"{StateMachine.robot_state}", (5, 10) ,cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
        
        self.display_detection('Detection', RGBframe)
        cv2.waitKey(1)


    def process_image_pipeline(self):
        while True:
            RGBframe, HSVframe = self.camera.get_frame()
            if RGBframe is None:
                continue
            self.local_frame = RGBframe.copy()
            now = time.time()
            self.process_image()
            elapsed = time.time() - now
            fps = 1/elapsed
            # print('Time: ', elapsed, ' - FPS: ',fps)
            # Exit on 'q' key press
            if 0xFF == ord('q'):
                break
        self.__del__()

    def __del__(self):
        self.camera.close()
        cv2.destroyAllWindows()
        return