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
        self.color.load_color_thresholds("calibration/color_thresholds.csv")
        self.homography.load_homography_matrix("calibration/homography_matrix.csv")
        self.focal_length.load_focal_length("calibration/focal_length.csv")
    
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