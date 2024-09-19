from Computer_Vision_Tutorial.live_detection3 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame
from navigation.state_machine import StateMachine
from picamera2 import Picamera2
from threading import Thread
import json

def main():
    # Create the state machine object
    state_machine = StateMachine()
    
    # Load the color thresholds, focal length, and homography matrix
    print('loading CV')
    # Load color thresholds from CSV
    color_ranges = load_color_thresholds('Computer_Vision_Tutorial/calibrate.csv')

    # Load homography matrix & focal length
    load_homography_matrix('Computer_Vision_Tutorial/calibrate_homography.csv')
    load_focal_length('Computer_Vision_Tutorial/calibrate_focal_length.csv')

    print('init cam')
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()

    print('Start Loop')
    while True:
        frame = picam2.capture_array()
        if frame is not None:
            print('Get Frame Success')
            # Process the frame
            process_frame(frame, color_ranges)
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
            # Run the state machine using treading
            print(shelfRangeBearing)
            state_machine.run_state_machine(itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing)


    # Stop the camera
if __name__ == "__main__":
    main()












 