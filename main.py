# from Computer_Vision_Tutorial.live_detection3 import load_color_thresholds, load_focal_length, load_homography_matrix, process_frame
from Vision.main_vision import Vision as VisionClass
from navigation.state_machine import StateMachine
import time
from threading import Thread

def main():
    # Create the state machine object
    state_machine = StateMachine()
    

    # print('init cam')
    # picam2 = Picamera2()
    # picam2.configure(picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (820, 616)}))  # Set a larger resolution
    # picam2.start()

    # start the vision threads (one is sampling images, one is processing)
    # thread should update attribute of class to store object RB (Vision.objectRB)
    Vision = VisionClass()
    Vision.start("/home/edmond/egb320-team9/Videos/obs_search_ps_left_row1.mp4") # Start the threads (Captrue and Pipeline)
    #Vision.requested_objects = 0b000010
    time.sleep(1)
    data = [None] * 6
    print('Start Loop')
    while True:
        # Vision.requested_objects = 0b111111
        now = time.time()   # get the time
        print("Run single frame")
        process_thread = Thread(target=Vision.process_image)
        process_thread.start()
        process_thread.join()  # Wait for the thread to complete
        print("Process Complete")

        # access the attributes of the data
        data = Vision.objectRB
        # print(data)

        # Run State machine and send information back to the vision using "requested_objects"
        Vision.requested_objects = state_machine.run_state_machine(data)
        # state_machine.run_state_machine(data)
        #Vision.requested_objects = 0b000000 # Shelves
        elapsed = time.time() - now  # how long was it running?
        fps = 1.0/elapsed
        print('Elapsed Time: ', elapsed, 'FPS: ', fps)

    # Stop the camera
if __name__ == "__main__":
    main()












 