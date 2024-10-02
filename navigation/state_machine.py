import numpy as np
import pandas as pd
# import item_collection.item_collection as itemCollection
# from threading import Thread, Event
import os
import sys

# Define the root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../')) 

import navigation.path_planning as navigation
import mobility.intergration_master as mobility

# define the numbers
# 0b000000 = [Packing bay, Rowmarkers, Shelves, Items,  Obstacles, Wallpoints]

PACKING_BAY = 0b100000
ROW_MARKERS = 0b010000
SHELVES =     0b001000
ITEMS =       0b000100
OBSTACLES =   0b000010
WALLPOINTS =  0b000001

LEFT = 0
RIGHT = 1

class StateMachine:
    def __init__(self):
        # item_collection = itemCollection()
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
        self.row_position_L = [0.3, 1, 1.7] # row positions for left shelf
        self.row_position_R = [1.7, 1, 0.3] # row positions for left shelf
        self.found_shelf = False
        self.found_row = False
        self.at_ps = False
        self.action = {}
        self.final_df = {}
        self.goal_position = {}
        self.current_item = 0
        self.draw = False
        self.holding_item = False

        # Read the object order file
        with open("navigation/Order_2.csv", mode="r", encoding='utf-8-sig') as csv_file:
            # Load the CSV into a DataFrame, automatically using the first row as column names
            df = pd.read_csv(csv_file)

        # Group by 'Height' and find the minimum 'Shelf' for each height
        min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

        # Sort by 'Shelf' in descending order
        sorted_min_shelf  = min_shelf_by_height.sort_values(by='Shelf', ascending=False)
        remaining_rows = df.drop(min_shelf_by_height.index)
        sorted_remaining_rows = remaining_rows.sort_values(by='Shelf', ascending=False)
        self.final_df = pd.concat([sorted_min_shelf, sorted_remaining_rows])

        self.final_df['Row'] = self.final_df['Shelf'] // 2
        # Redefine the index
        self.final_df = self.final_df.reset_index(drop=True)

        # Display the result
        print("Optimised pickup order:")
        print(self.final_df)

        self.robot_state = 'INIT'

    def init_state(self):
        # Set initial parameters and switch to the next state
        self.robot_state = 'SEARCH_FOR_PS'
        self.holding_item = False

        # Set the target item position
        print(self.current_item)
        self.target_shelf = self.final_df['Shelf'][self.current_item]
        self.target_row = self.final_df['Row'][self.current_item]
        self.target_bay = self.final_df['Bay'][self.current_item]
        self.target_height = self.final_df['Height'][self.current_item]

        # Set the subtarget shelf (Opposite side of the target shelf)
        if self.target_shelf % 2 == 1:  # Odd
            self.subtarget_shelf = self.target_shelf - 1
        else:  # Even
            self.subtarget_shelf = self.target_shelf + 1

        # Reset the actuators
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = 0
        # item_collection.grip('open')

    def search_for_ps(self, packStationRangeBearing, rowMarkerRangeBearing):
        self.found_ps = packStationRangeBearing[0] is not None
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        if self.found_row:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'MOVE_TO_ROW'
        # Rotate on the spot
        if self.at_ps:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'SEARCH_FOR_SHELF'

        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1 # Rotate on the spot

        if self.found_ps:
            self.robot_state = 'MOVE_TO_PS'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

    def move_to_ps(self, packStationRangeBearing, obstaclesRB):
        self.found_ps = packStationRangeBearing[0] is not None

        if self.found_ps:
            self.goal_position['range'] = packStationRangeBearing[0][0]
            self.goal_position['bearing'] = packStationRangeBearing[0][1]
            print(self.goal_position)

            # Calculate goal velocities
            self.action = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - 1 < 0.01: # Middle of the area
                self.robot_state = 'SEARCH_FOR_SHELF'
                if self.target_row == 2:
                    self.shelf_side = RIGHT # Will turn left to find Right shelf (5)
                    # can rotate to the left faster with time delay
                else:
                    self.shelf_side = LEFT # Will turn right to find Left shelf (0)
                self.action['forward_vel'] = 0
                self.action['rotational_vel'] = 0
        else:
            self.robot_state = 'SEARCH_FOR_PS'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

    def search_for_shelf(self, rowMarkerRangeBearing, shelfRangeBearing):
        # Check if the row marker is found
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None
        if self.found_row:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'MOVE_TO_ROW'

        # Turn direction based on the shelf side
        if self.shelf_side == LEFT:  # Odd
            # Turn right
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0.1
            if shelfRangeBearing[0] is not None:
                self.found_shelf = True
                # LEFT SHELF FOUND
            
        else:
            # Turn left
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = -0.1
            if shelfRangeBearing[1] is not None:
                self.found_shelf = True
                # RIGHT SHELF FOUND

        # Rotate on the spot

        if self.found_shelf:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'MOVE_TO_SHELF'

    def move_to_shelf(self, shelfRangeBearing, obstaclesRB):
        self.found_shelf = False

        if self.shelf_side == LEFT & shelfRangeBearing[0] is not None:
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[0][0]
            self.goal_position['bearing'] = shelfRangeBearing[0][1]
            print(self.robot_state, "Going to: LEFT shelf", self.goal_position)

            # Calculate goal velocities
            self.action = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            
            if self.goal_position['range'] - self.row_position_L[self.target_row] < 0.01:
                self.robot_state = 'SEARCH_FOR_ROW'
                self.action['forward_vel'] = 0
                self.action['rotational_vel'] = 0

        elif self.shelf_side == RIGHT & shelfRangeBearing[1] is not None:
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[1][0]
            self.goal_position['bearing'] = shelfRangeBearing[1][1]
            print(self.robot_state, "Going to: RIGHT shelf", self.goal_position)

            # Calculate goal velocities
            self.action = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.row_position_R[self.target_row] < 0.01:
                self.robot_state = 'SEARCH_FOR_ROW'
                self.action['forward_vel'] = 0
                self.action['rotational_vel'] = 0
        else:
            self.robot_state = 'SEARCH_FOR_SHELF'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
        

    def search_for_row(self, rowMarkerRangeBearing):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        # Rotate on the spot
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1 if self.shelf_side == LEFT else 0.1

        if self.found_row:
            self.robot_state = 'MOVE_TO_ROW'

    def move_to_row(self, rowMarkerRangeBearing, obstaclesRB, shelfRangeBearing):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        if self.found_row:
            if rowMarkerRangeBearing[self.target_row] != None:
                self.goal_position['range'] = rowMarkerRangeBearing[self.target_row][0]
                self.goal_position['bearing'] = rowMarkerRangeBearing[self.target_row][1]
                print(self.goal_position)

            # Add shelves to obstacles
            np.append(obstaclesRB, shelfRangeBearing[self.target_shelf])

            # Calculate goal velocities
            self.action = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.goal_bay_position[self.target_bay] < 0.01:
                self.robot_state = 'SEARCH_FOR_ITEM'
                self.action['forward_vel'] = 0
                self.action['rotational_vel'] = 0
        else:
            self.robot_state = 'SEARCH_FOR_ROW'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

    def search_for_item(self, itemsRB):
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1 if self.target_shelf % 2 == 1 else 0.1 # Rotate Right if odd, Left if even

        print(f"itemsRB: {itemsRB}")
        for i in itemsRB:
            if itemsRB[i] is not None:
                itemRange = itemsRB[i][0]
                itemBearing = itemsRB[i][1]
                if abs(itemBearing) < 0.05 and itemRange < 0.20:
                    self.robot_state = 'COLLECT_ITEM'
                    self.action['forward_vel'] = 0
                    self.action['rotational_vel'] = 0
    
    def collect_item(self):
        print("Collecting item")
        # item_collection.grip('open')
        # item_collection.lift(self.target_height)
        self.robot_state = 'ROTATE_TO_EXIT'

    # Add more methods for other states...

    def run_state_machine(self, dataRB):
        
        # order of objects: [Packing bay, Rowmarkers, Shelves, Items,  Obstacles, Wallpoints] 
        # co-responding to the binary number 0b000000

        print(self.robot_state)
        if self.robot_state == 'INIT':
            self.init_state()
            return 0
        elif self.robot_state == 'SEARCH_FOR_PS':
            self.search_for_ps(dataRB[0], dataRB[1])
            return PACKING_BAY | ROW_MARKERS
        elif self.robot_state == 'MOVE_TO_PS':
            self.move_to_ps(dataRB[0], dataRB[4])
            return PACKING_BAY | OBSTACLES
        elif self.robot_state == 'SEARCH_FOR_SHELF':
            self.search_for_shelf(dataRB[1], dataRB[2])
            return ROW_MARKERS | SHELVES
        elif self.robot_state == 'MOVE_TO_SHELF':
            self.move_to_shelf(dataRB[2], dataRB[4])
            return SHELVES | OBSTACLES
        elif self.robot_state == 'SEARCH_FOR_ROW':
            self.search_for_row(dataRB[1])
            return ROW_MARKERS
        elif self.robot_state == 'MOVE_TO_ROW':
            self.move_to_row(dataRB[1], dataRB[4], dataRB[2])
            return ROW_MARKERS | OBSTACLES | SHELVES
        elif self.robot_state == 'SEARCH_FOR_ITEM':
            self.search_for_item(dataRB[3])
            return ITEMS
        elif self.robot_state == 'COLLECT_ITEM':
            self.collect_item()
            return ITEMS
        # Add other state transitions...

        mobility.drive(self.action['forward_vel'], self.action['rotational_vel'])
        return 0
        
        