# -*- coding: utf-8 -*-
import cv2
import picamera2
import numpy as np
from threading import Thread


def runVision():

    #does something
    range = 1
    bearing = 2
    return range, bearing

class CamFrameGrabber:
    
    #FOV = number of degrees for camera view
    def __init__(self, src, width, height):
        #self.camera = cv2.VideoCapture(src)
        self.camera = picamera2.Picamera2()
        self.width = width
        self.height = height

        config = self.camera.create_video_configuration(main={"format":'XRGB8888',"size":(height,width)})
        self.camera.configure(config)
        self.camera.start()
        
        # self.camera.set(3,width)
        # self.camera.set(4,height)
        
        self.cameraStopped = False
        self.gotFrame = False
        
        self.currentFrame = np.zeros((height,width,3),np.uint8)
        # (self.gotFrame, self.currentFrame) = self.camera.read()
        self.currentFrame = self.camera.capture_array()
        
    def start(self):
        
        Thread(target=self.captureImage,args=()).start()
        return self


    def  captureImage(self):
        # for the input goal in degrees iterate
        # through attractive field and compute 
        while True:
            if self.cameraStopped:
                return
            
            # (self.retVal, self.currentFrame) = self.camera.read()
            self.currentFrame = self.camera.capture_array()


    def getCurrentFrame(self):
        return self.currentFrame
    
    def stop(self):
        self.cameraStopped = True
    
    def __del__(self):
        
        self.camera.release()
        cv2.destroyAllWindows()