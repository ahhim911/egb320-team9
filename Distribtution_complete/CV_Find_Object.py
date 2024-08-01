import cv2
import numpy as np


"Accept the current frame of the camera and return the proocessed color mask"
def find_object(frame):
    
    #Upper and Lower HSV bounds for the color mask
    LWR_BOUND = (170,132,132)
    UPR_BOUND = (5,255,255)

    #Use GaussianBlur on the orignal parameter frame (https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html)
    blrd_frame = cv2.GaussianBlur(frame, (3,3),0) 

    #Use CvtColor to convert RGB to HSV (https://www.geeksforgeeks.org/python-opencv-cv2-cvtcolor-method)
    hsv_frame = cv2.cvtColor(blrd_frame , cv2.COLOR_BGR2HSV) 


    Hue_Overflow = True
    if Hue_Overflow:
        #The Upper and lower bounds of the overlaying HUE
        MAX_HUE = (180, UPR_BOUND[1], UPR_BOUND[2])
        MIN_HUE = (0, LWR_BOUND[1], LWR_BOUND[2])
        
        #Apply the color thresholds to the upper and lower part of our map using the inrange function (Lwr -> Max, Min -> Upr)
        # (https://www.educba.com/opencv-inrange) and the hsv frame
        Lower_Hue = cv2.inRange(hsv_frame, LWR_BOUND, MAX_HUE)
        Upper_Hue = cv2.inRange(hsv_frame, MIN_HUE, UPR_BOUND)

        binary_image = cv2.bitwise_or(Lower_Hue,Upper_Hue)
    else:
        #Apply the lower and upper bounds to the hsv image using the inrange function (https://www.educba.com/opencv-inrange)
        binary_image = cv2.inRange(hsv_frame, LWR_BOUND, UPR_BOUND) 

    #Threshold value
    KERNAL_THRESHOLD = np.ones((10,10))
    
    #Apply some filters using the aboove kernal and the binary image. Feel free to experiment with different options 
    # (https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html)
    #The main one you should use is the morphologyEx method
    filtered_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, KERNAL_THRESHOLD) 

    return [filtered_image, binary_image]