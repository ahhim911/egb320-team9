import os, sys
ROOT_DIR = os.path.abspath("../egb320_test_repo/my_project")
sys.path.append(ROOT_DIR)

# -*- coding: utf-8 -*-
# from vision.CamFrameGrabber import CamFrameGrabber

from vision.CamFrameGrabber import CamFrameGrabber
import cv2

if __name__ == '__main__':
    
    print("Testing camera frame grabber class")

    camera = CamFrameGrabber(src=0, width=320, height=640).start()

    nFrames = 0
    while 1:
    
        frame = camera.getCurrentFrame()
        #do some processing
        cv2.imshow("Frame", frame)
        cv2.waitKey(1)
        
        nFrames = nFrames + 1
        print(nFrames)
        
    cv2.destroyAllWindows()
    camera.stop()
