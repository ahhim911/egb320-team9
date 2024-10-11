from Vision.main_vision import Vision as VisionClass
import time
from threading import Thread

def main():
    Vision = VisionClass()
    Vision.start("/home/edmond/egb320-team9/Videos/row2_exit_backward.mp4") # Start the threads (Captrue and Pipeline)
    Vision.requested_objects = 0b111111
    time.sleep(1)
    data = [None] * 6
    print('Start Loop')
    while True:
        now = time.time()   # get the time
        #print("Run single frame")
        process_thread = Thread(target=Vision.process_image)
        process_thread.start()
        process_thread.join()  # Wait for the thread to complete
        #print("Process Complete")

        # access the attributes of the data
        data = Vision.objectRB
        # print(data)

        # Vision.requested_objects = 0b000001
        elapsed = time.time() - now  # how long was it running?
        fps = 1.0/elapsed
        print('Elapsed Time: ', elapsed, 'FPS: ', fps)

    # Stop the camera
if __name__ == "__main__":
    main()
    
#TO DO implement a function that i can specify a state and update the bitmask
#    if self.robot_state == 'INIT':
#        request = 0
#    elif self.robot_state == 'SEARCH_FOR_PS':
#        request = PACKING_BAY | ROW_MARKERS
#    elif self.robot_state == 'MOVE_TO_PS':
#        request = PACKING_BAY | OBSTACLES
#    elif self.robot_state == 'SEARCH_FOR_SHELF':
#        request = ROW_MARKERS | SHELVES
#    elif self.robot_state == 'MOVE_TO_SHELF':
#        request = SHELVES | OBSTACLES
#    elif self.robot_state == 'SEARCH_FOR_ROW':
#        request = ROW_MARKERS
#    elif self.robot_state == 'MOVE_TO_ROW':
#        request = ROW_MARKERS | OBSTACLES | SHELVES
#    elif self.robot_state == 'SEARCH_FOR_ITEM':
#        request = ITEMS
#    elif self.robot_state == 'COLLECT_ITEM':
#        request = ITEMS
#    elif self.robot_state == 'ROTATE_TO_EXIT':
#        request = ROW_MARKERS
#    elif self.robot_state == 'MOVE_TO_EXIT':
#        request = ROW_MARKERS