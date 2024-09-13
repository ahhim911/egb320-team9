import numpy as np
import pandas as pd



class StateMachine:
    def __init__(self):
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
		self.found_shelf = False
		self.found_row = False
		self.at_ps = False
		self.action = {}
		self.goal_position = {}