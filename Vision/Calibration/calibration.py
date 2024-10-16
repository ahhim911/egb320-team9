import numpy as np
import csv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Calibration')))
from color import Color, CalibrateColor
from homography import Homography, CalibrateHomography
from focal_length import FocalLength, CalibrateFocalLength


"""
Calibration module for loading calibration data.
"""


class Calibration:
    def __init__(self):
        self.color = Color()
        self.homography = Homography()
        self.focal_length = FocalLength()

    def load_csv(self):
        color_range = self.color.load_color_thresholds("/home/edmond/egb320-team9/Vision/Calibration/color_thresholds.csv")
        homography_matrix = self.homography.load_homography_matrix("/home/edmond/egb320-team9/Vision/Calibration/calibrate_homography.csv")
        focal_length = self.focal_length.load_focal_length("/home/edmond/egb320-team9/Vision/Calibration/focal_length.csv")
        #print("Color range: ", color_range)
        #print("homography_matrix: ", homography_matrix)
        #print("focal_length: ", focal_length)        
        return color_range, homography_matrix, focal_length
    
    def calibrate(self, focal_length=True, homography=True, color=True):
        if color:
            cal_color = CalibrateColor()
            cal_color.calibrate()
        if homography:
            cal_holomography = CalibrateHomography()
            cal_holomography.calibrate()
        if focal_length:
            cal_focal_length = CalibrateFocalLength()
            cal_focal_length.calibrate()
        return 
    
def main():
    cal = Calibration()
    cal.calibrate()
    return

if __name__ == "__main__":
    main()

"""
# Color calibration
1. Capture an image of the object to be detected.
- find a good lighting condition
- place the object in front of the camera
    - orange
    - green
    - blue
    - black
- 'c' to capture an image.

2. Run the calibration script.
- 'q' to quit
- 's' to save
- 'r' to reset
- '1' to select orange
- '2' to select green
- '3' to select blue
- '4' to select black
- '5' to select white
- '6' to select yellow

# Homography calibration
1. Capture an image of the ground plane with the calibration mat
- find a good lighting condition
- place the calibration mat on the ground
- 'c' to capture an image.

2. Run the calibration script.
- 'q' to quit
- 's' to save
- click on the corners of the calibration mat in the image with the following order:
    - bottom left
    - bottom right
    - top right
    - top left

# Focal length calibration



"""