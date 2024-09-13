from Computer_Vision_Tutorial.live_detection4 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame, capture_frames
from navigation.state_machine import StateMachine
from picamera2 import Picamera2
from threading import Thread, Lock
import json
import time

# Global variables for frame handling and locking
frame = None
frame_lock = Lock()
color_ranges = {}

# Function to run the state machine in a separate thread
def run_state_machine_thread(state_machine):
    while True:
        # Path to the JSON file
        json_file_path = 'output_data.json'
        
        # Open and load the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Extract the range and bearing data
        itemsRB = data['items']
        packingBayRB = data['packing_bay']
        obstaclesRB = data['obstacles']
        rowMarkerRangeBearing = data['row_markers']
        shelfRangeBearing = data['shelves']
        
        # Run the state machine
        state_machine.run_state_machine(itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing)
        
        # Small delay to reduce CPU usage
        time.sleep(0.1)

# Function to run the live detection in a separate thread
def run_live_detection(picam2):
    global frame, color_ranges
    while True:
        with frame_lock:
            frame = picam2.capture_array()
        
        if frame is not None:
            process_frame(frame, color_ranges)
        
        # Small delay to reduce CPU usage
        time.sleep(0.01)

def main():
    global frame, color_ranges

    # Create the state machine object
    state_machine = StateMachine()
    
    # Load the color thresholds, focal length, and homography matrix
    print('loading CSV')
    color_ranges = load_color_thresholds('Computer_Vision_Tutorial/calibrate.csv')
    load_homography_matrix('Computer_Vision_Tutorial/calibrate_homography.csv')
    load_focal_length('Computer_Vision_Tutorial/calibrate_focal_length.csv')

    print('init cam')
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))
    picam2.start()

    # Create and start the threads
    live_detection_thread = Thread(target=run_live_detection, args=(picam2,))
    live_detection_thread.daemon = True
    live_detection_thread.start()

    state_machine_thread = Thread(target=run_state_machine_thread, args=(state_machine,))
    state_machine_thread.daemon = True
    state_machine_thread.start()

    # Keep the main thread running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
