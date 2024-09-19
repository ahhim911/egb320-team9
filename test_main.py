from Computer_Vision_Tutorial.live_detection_test import load_color_thresholds, load_focal_length, load_homography_matrix, process_image_pipeline, capture_frames
from navigation.state_machine import StateMachine
from threading import Thread, Lock
import cv2
import json
import time
import os
import cProfile
import pstats

# Global variables for frame handling and locking
frame = None
frame_lock = Lock()
color_ranges = {}

# Function to run the state machine in a separate thread
def run_state_machine_thread(state_machine):
    json_file_path = 'output_data.json'

    while True:
        try:
            # Since the processing thread writes the JSON output, we can read it
            if os.path.getsize(json_file_path) > 0:
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
        
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}. The file may be corrupted or not written correctly.")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        # Small delay to reduce CPU usage
        time.sleep(0.1)

def main():
    global frame, color_ranges

    # Create the state machine object
    state_machine = StateMachine()
    
    # Load the color thresholds, focal length, and homography matrix
    print('Loading calibration data')
    file_path = 'Computer_Vision_Tutorial/'
    color_ranges = load_color_thresholds(file_path + 'calibrate.csv')
    load_homography_matrix(file_path + 'calibrate_homography.csv')
    load_focal_length(file_path + 'calibrate_focal_length.csv')

    print('Starting video capture')
    v_file_path = 'Vision/Camera/Videos/'
    file_name = 'test_video.mp4'
    video_capture = cv2.VideoCapture(v_file_path + file_name)
    if not video_capture.isOpened():
        print("Error: Could not open video file.")
        return

    # Create and start the threads
    capture_thread = Thread(target=capture_frames, args=(video_capture,))
    capture_thread.daemon = True
    capture_thread.start()

    live_detection_thread = Thread(target=process_image_pipeline, args=(color_ranges,))
    live_detection_thread.daemon = True
    live_detection_thread.start()

    state_machine_thread = Thread(target=run_state_machine_thread, args=(state_machine,))
    state_machine_thread.daemon = True
    state_machine_thread.start()

    # Keep the main thread running until the video ends
    while True:
        if not capture_thread.is_alive() or not live_detection_thread.is_alive():
            break  # Exit if capture or processing thread has ended
        time.sleep(1)

if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)  # Print top 20 time-consuming functions
