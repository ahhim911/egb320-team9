import numpy as np
import csv
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
        color_range = self.color.load_color_thresholds("calibration/color_thresholds.csv")
        homography_matrix = self.homography.load_homography_matrix("calibration/homography_matrix.csv")
        focal_length = self.focal_length.load_focal_length("calibration/focal_length.csv")
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