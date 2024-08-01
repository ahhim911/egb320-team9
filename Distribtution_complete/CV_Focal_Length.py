from CV_Find_Object import find_object
from CV_Find_Contours import find_contours

import cv2

"Caculate the focal length of a camera based on a refrence image"


REFRENCE_IMAGE_WIDTH = 3
REFRENCE_IMAGE_DISTANCE = 30

def caculate_focal_Length():
    #caculate the focal length of our camera
    refrence_image = cv2.imread("./REFRENCE_IMAGE.jpg")

    imageObject = find_object(refrence_image)
    contours, width_px = find_contours(imageObject[0])

    if(len(contours) == 0):
        return 0

    #Return the focal length based on the Width and distance of the refrence image and the caculated width in pixels 
    #https://pyimagesearch.com/2015/01/19/find-distance-camera-objectmarker-using-python-opencv    
    return (REFRENCE_IMAGE_DISTANCE * width_px[0]) / REFRENCE_IMAGE_WIDTH 
    