from Computer_Vision_Tutorial.live_detection3 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame
from navigation.state_machine import StateMachine
from picamera2 import Picamera2
from threading import Thread
import json

def main():
    # Create the state machine object
    state_machine = StateMachine()
    
    # Load the color thresholds, focal length, and homography matrix

    # Load color thresholds from CSV
    color_ranges = load_color_thresholds('calibrate.csv')

    # Load homography matrix & focal length
    load_homography_matrix('calibrate_homography.csv')
    load_focal_length('calibrate_focal_length.csv')

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()

    while True:
        frame = picam2.get_frame()
        if frame is not None:
            # Process the frame
            process_frame(frame, color_ranges)
            # Path to the JSON file
            json_file_path = '../../Computer_Vision_Tutorial/output_data.json'

            # Open and load the JSON file
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                        
            # Extract the range and bearing data
            itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing = data
            # Run the state machine using treading
            state_machine.run_state_machine(itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing)
            # Display the frame
            picam2.display_frame(frame)

    
if __name__ == "__main__":
    main()













