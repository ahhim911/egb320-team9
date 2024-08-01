import cv2




def caculate_distance( Focal_Length, Width_px):
    #Return the distance to the camera
    REFRENCE_IMAGE_WIDTH = 3

    #View the source for the equation for distance(https://pyimagesearch.com/2015/01/19/find-distance-camera-objectmarker-using-python-opencv)
    return (REFRENCE_IMAGE_WIDTH * Focal_Length)/ Width_px 

def caculate_position(contours):
    #caculate the center of the image (x and y) relevant to the screen
    max_contours = contours
    X_Position, Y_Position, Rect_Width, Rect_Height = cv2.boundingRect(max_contours)

    #Using the above information, return the x center, y center, Height and Width
    return  (X_Position + Rect_Width//2), (Y_Position + Rect_Height//2), Rect_Height, Rect_Width 