import csv
import numpy as np

"""
Homography module for loading homography matrix.
"""



class Homography:
    def __init__(self):
        self.homography_matrix = None

    def load_homography_matrix(self, csv_file):
        self.homography_matrix = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                self.homography_matrix.append([float(val) for val in row])
        self.homography_matrix = np.array(self.homography_matrix)