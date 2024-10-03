# import os, sys
# ROOT_DIR = os.path.abspath("../")
# sys.path.append(ROOT_DIR)

#Folder is navigation, module is NavClass.py renamed to nav within this script
from navigation import NavClass as nav

#Folder is vision, module is CamFrameGrabber.py renamed to cam within this script
from vision import CamFrameGrabber as cam

import time
import cv2

if __name__ == '__main__':
  

    Frequency = 5.0 #Hz
    Interval = 1.0/Frequency

    camera = cam.CamFrameGrabber(src=0, width=720, height=1280).start()
   
    navSystem = nav.NavClass(60)
    
    # execute control rate loop
    # very simple main robot loop
    while True:
        print('Executing Loop')
        now = time.time()            # get the time
        
        frame = camera.getCurrentFrame()
        # frame = cv2.rotate(frame, cv2.ROTATE_180)
        # elapsed = time.time()
        
        #do image processing here
        
        #objects_detected = process_image(frame)
        #update navigation system
        navSystem.update()

        #mobility.execute(f_vel, rot_vel)
       
        #mobility.updateMotors(navSystem.forward_vel, navSystem.rot_vel)

        
        cv2.imshow("test window", frame)
        cv2.waitKey(1)

        elapsed = time.time() - now  # how long was it running?
        if(Interval-elapsed > 0):
            time.sleep(Interval-elapsed) # wait for amount of time left from interval


        ## this is not needed but good for debugging rate
        elapsed2 = time.time() - now
        rate2 = 1.0/elapsed2
        print("Processing Rate after sleep is: {}.".format(rate2))