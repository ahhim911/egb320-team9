# from Computer_Vision_Tutorial.live_detection3 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame
from Vision.main_vision import Vision as VisionClass
from navigation.state_machine import StateMachine
from picamera2 import Picamera2

def main():
    # Create the state machine object
    state_machine = StateMachine()
    

    print('init cam')
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    picam2.start()

    # start the vision threads (one is sampling images, one is processing)
    # thread should update attribute of class to store object RB (Vision.objectRB)
    Vision = VisionClass()
    Vision.start()

    print('Start Loop')
    while True:
        # Process the frame
        # process_frame(frame, color_ranges)

        # access the attributes of the data
        data = Vision.objectRB

        # Run State machine and send information back to the vision using "requested_objects"
        Vision.requested_objects = state_machine.run_state_machine(data)


    # Stop the camera
if __name__ == "__main__":
    main()












 