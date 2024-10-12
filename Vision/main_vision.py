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
from threading import Event
import logging
import cv2

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("vision_system.log", mode='a')
    ]
)
logging.getLogger('picamera2').setLevel(logging.WARNING)  # Only show warnings and errors for picamera2
logger = logging.getLogger(__name__)

# Constants for the object bitmask
PACKING_BAY = 0b100000
MARKERS = 0b010001
SHELVES = 0b001000
ITEMS = 0b000100
OBSTACLES = 0b000010
WALLPOINTS = 0b000001

state_requests = {
    'INIT': 0b000000,
    'SEARCH_FOR_PS': PACKING_BAY | MARKERS,
    'MOVE_TO_PS': PACKING_BAY | OBSTACLES,
    'SEARCH_FOR_SHELF': MARKERS | SHELVES,
    'MOVE_TO_SHELF': SHELVES | OBSTACLES,
    'SEARCH_FOR_ROW': MARKERS,
    'MOVE_TO_ROW': MARKERS | OBSTACLES | SHELVES,
    'SEARCH_FOR_ITEM': ITEMS | SHELVES,
    'COLLECT_ITEM': ITEMS,
    'ROTATE_TO_EXIT': MARKERS,
    'MOVE_TO_EXIT': MARKERS | OBSTACLES,
    'EXIT_PS': MARKERS,
    'ALL': 0b111111
}

class Vision(DetectionBase):
    def __init__(self,camera):
        """
        Initialize the Vision system
        """
        logger.info("Initializing Vision system")
        self.objectRB = [[], [], [], [], [], []]
        self.requested_objects = 0b000000
        # self.camera = None
        self.stop_event = Event()  # Event to signal threads to stop
        self.thread = None  # Thread for the live feed
        self.is_stopped = False  # To track if the system is already stopped

        self.camera = camera
        # try:
        # except Exception as e:
        #     logger.error(f"Error initializing camera: {e}")
        #     raise  # Exit if the camera can't be initialized

        self.calibration = Calibration()
        self.color_ranges = None
        self.homography_matrix = None
        self.focal_length = None  # Default focal length

    def start(self, path):
        """
        Start the Vision system with live video feed or recorded video
        """
        logger.info(f"Starting vision system with path: {path}")
        draw = True
        # focal_length = 321
        try:
            self.color_ranges, self.homography_matrix, self.focal_length = self.calibration.load_csv()
        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")
            return  # Exit if the calibration fails

        # Initialize detectors
        self.shelf_detector = Shelf(homography_matrix=self.homography_matrix, draw=draw)
        self.marker_detector = Marker(focal_length=self.focal_length, draw=draw)
        self.wall_detector = Wall(homography_matrix=self.homography_matrix, draw=draw)
        self.ramp_detector = PackingStationRamp(homography_matrix=self.homography_matrix, draw=draw)
        self.obstacle_detector = Obstacle(focal_length=self.focal_length, homography_matrix=self.homography_matrix, draw=draw)
        self.item_detector = Item(real_item_width=0.0375, focal_length=self.focal_length, draw=draw)

        #self.thread = Thread(target=self.camera.play_video, args=(path,))  # Recorded video from files
        #self.thread = Thread(target=self.camera.live_feed, args=(self.stop_event,))
        #self.thread.start()

    def update_item(self, item_width):
        """
        Update item width
        """
        logger.debug(f"Updating item width to: {item_width}")
        self.item_detector = Item(real_item_width=item_width, focal_length=self.focal_length, draw=True)

    def update_requested_objects(self, state):
        """
        Update the requested objects based on the current state
        """
        self.requested_objects = state_requests.get(state, 0b000000)
        logger.info(f"Updated requested objects for state {state}: {bin(self.requested_objects)}")

    def item_to_size(self, item_type):
        if item_type == "Bottle":
            size = 0.02 
        elif item_type == "Ball":
            size = 0.045
        elif item_type == "Cube":
            size = 0.037
        elif item_type == "Bowl":
            size = 0.055
        elif item_type == "Mug":
            size = 0.05
        elif item_type == "Weetbots":
            size = 0.065
        return size

    def process_image(self):
        """
        Process the current camera frame and detect objects
        """
        #logger.debug("Processing image")
        try:
            #RGBframe, HSVframe = self.camera.get_frame()
            RGBframe = self.camera.get_frame()

            if RGBframe is None: # or HSVframe is None:
                #logger.warning("RGBframe is None, skipping frame processing")
                return self.objectRB
            
            HSVframe = cv2.cvtColor(RGBframe, cv2.COLOR_BGR2HSV)            

            # Detection logic based on requested objects
            if self.requested_objects & SHELVES:
                detected_shelves, shelf_frame, shelf_mask = self.shelf_detector.find_shelf(HSVframe, RGBframe, self.color_ranges)
                #self.display_detection('Shelf Mask', shelf_mask)
                self.objectRB[2] = detected_shelves

            if self.requested_objects & WALLPOINTS:
                detected_walls, wall_frame, filled_wall_mask = self.wall_detector.find_wall(HSVframe, RGBframe, self.color_ranges)
                # self.display_detection('Wall Mask', filled_wall_mask)
                self.objectRB[5] = detected_walls

            if self.requested_objects & MARKERS:
                detected_markers, marker_frame, marker_mask = self.marker_detector.find_marker(HSVframe, RGBframe, self.color_ranges, filled_wall_mask=filled_wall_mask)
                # self.display_detection('Marker Mask', marker_mask)
                self.objectRB[1] = detected_markers

            if self.requested_objects & PACKING_BAY:
                detected_ramp, ramp_frame, ramp_mask = self.ramp_detector.find_packing_station_ramp(HSVframe, RGBframe, self.color_ranges)
                #self.display_detection('Ramp Mask', ramp_mask)
                self.objectRB[0] = detected_ramp

            if self.requested_objects & OBSTACLES:
                detected_obstacles, obstacle_frame, obstacle_mask = self.obstacle_detector.find_obstacle(HSVframe, RGBframe, self.color_ranges)
                #self.display_detection('Obstacle Mask', obstacle_mask)
                self.objectRB[4] = detected_obstacles

            if self.requested_objects & ITEMS:
                detected_items, item_frame, item_mask = self.item_detector.find_item(HSVframe, RGBframe, self.color_ranges)
                #self.display_detection('Item Mask', item_mask)
                self.objectRB[3] = detected_items

            self.display_detection('Detection', RGBframe)
            cv2.waitKey(1)
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self.stop()

    def display_detection(self, window_name, frame):
        """
        Display frames for different detections (temporarily disabled)
        """
        if frame is not None:
            # Disabled display for now, uncomment if needed
            cv2.imshow(f'{window_name}', frame)
            pass

    def stop(self):
        """
        Stop the live feed and join the thread
        """
        logger.info("Stopping Vision system")
        self.camera.close()  # Close camera resources
        self.is_stopped = True  # Mark the system as stopped
        #logger.info("Vision system already stopped.")

    def __del__(self):
        """
        Clean up resources when the Vision system is shut down
        """
        logger.info("Shutting down the Vision system")
        self.stop()
