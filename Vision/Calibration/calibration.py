import numpy as np
import csv

"""
Calibration module for loading calibration data.
"""


class Calibration:
    def __init__(self):
        self.focal_length = None
        self.homography_matrix = None

    def load_focal_length(self, csv_file):
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            self.focal_length = float(next(csv_reader)[1])

    def load_homography_matrix(self, csv_file):
        self.homography_matrix = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                self.homography_matrix.append([float(val) for val in row])
        self.homography_matrix = np.array(self.homography_matrix)

    @staticmethod
    def load_color_thresholds(csv_file):
        color_ranges = {}
        category_mapping = {
            'orange': 'Item',
            'green': 'Obstacle',
            'blue': 'Shelf',
            'black': 'Marker'
        }
        
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                category = category_mapping.get(row[0], None)
                if category:
                    lower_hsv = np.array([int(row[1]), int(row[2]), int(row[3])])
                    upper_hsv = np.array([int(row[4]), int(row[5]), int(row[6])])
                    color_ranges[category] = (lower_hsv, upper_hsv)
        return color_ranges