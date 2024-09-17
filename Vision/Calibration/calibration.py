import numpy as np
import csv

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
