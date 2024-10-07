# from Computer_Vision_Tutorial.live_detection3 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame
from Vision.main_vision import Vision as VisionClass
#from navigation.state_machine import StateMachine
import time

def main():
    # Create the state machine object
    #state_machine = StateMachine()

    # start the vision threads (one is sampling images, one is processing)
    # thread should update attribute of class to store object RB (Vision.objectRB)
    Vision = VisionClass()
    Vision.start() # Start the threads (Captrue and Pipeline)

    print('Start Loop')
    while True:
        now = time.time()   # get the time

        # access the attributes of the data
        #data = Vision.objectRB

        # Run State machine and send information back to the vision using "requested_objects"
        # Vision.requested_objects = state_machine.run_state_machine(data)
        # state_machine.run_state_machine(data)
        Vision.requested_objects = 0b111111 # Shelves
        # elapsed = time.time() - now  # how long was it running?
        # fps = 1.0/elapsed
        # print('Elapsed Time: ', elapsed, 'FPS: ', fps)

    # Stop the camera
if __name__ == "__main__":
    main()












 