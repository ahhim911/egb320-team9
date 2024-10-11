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

        if self.requested_objects & SHELVES:
            detected_shelves, shelf_frame, shelf_mask = self.shelf_detector.find_shelf(HSVframe, RGBframe, self.color_ranges)
            self.display_detection('Shelf', shelf_mask)
            self.objectRB[2] = detected_shelves

        if self.requested_objects & WALLPOINTS:
            detected_walls, wall_frame, filled_wall_mask = self.wall_detector.find_wall(HSVframe, RGBframe,  self.color_ranges)
            #self.display_detection('Wall', filled_wall_mask)
            self.objectRB[5] = detected_walls
        
        
        if self.requested_objects & MARKERS:
            detected_markers, marker_frame, marker_mask = self.marker_detector.find_marker(HSVframe, RGBframe, self.color_ranges, filled_wall_mask=filled_wall_mask)
            #self.display_detection('Markers', marker_mask)
            self.objectRB[1] = detected_markers

        if self.requested_objects & PACKING_BAY:
            detected_ramp, ramp_frame, ramp_mask = self.ramp_detector.find_packing_station_ramp(HSVframe, RGBframe, self.color_ranges)  # Ramp detection
            # self.display_detection('Packing Bay', ramp_mask)
            self.objectRB[0] = detected_ramp

        if self.requested_objects & OBSTACLES:
            detected_obstacles, obstacle_frame, obstacle_mask = self.obstacle_detector.find_obstacle(HSVframe, RGBframe,  self.color_ranges)
            self.display_detection('Obstacles', obstacle_mask)
            self.objectRB[4] = detected_obstacles

        if self.requested_objects & ITEMS:
            detected_items, item_frame, item_mask = self.item_detector.find_item(HSVframe, RGBframe,  self.color_ranges)
            #self.display_detection('Items', item_mask)
            self.objectRB[3] = detected_items
        
        self.display_detection('Detection', RGBframe)
        cv2.waitKey(1)

    def __del__(self):
        self.camera.close()
        cv2.destroyAllWindows()
        return