import numpy as np
import pandas as pd
from enum import Enum


import navigation.path_planning as navigation
from i2c.main_i2c import I2C

# define the numbers
# 0b000000 = [Packing bay, Rowmarkers, Shelves, Items,  Obstacles, Wallpoints]

# STATE = Enum('STATE', [
# 	'LOST',
# 	'WANDER',
# 	'FIND_AISLE_FROM_OUTSIDE',
# 	'AISLE_DOWN',
# 	'AISLE_DOWN_BAY3',
# 	'FACE_BAY',
# 	'COLLECT_ITEM',
# 	'FACE_OUT',
# 	'WANDER_OUT',
# 	'FACE_PACKING',
# 	'APPROACH_PACKING',
# 	'ASCEND_PACKING',
# 	'DROP_ITEM',
# 	'DESCEND_PACKING',
# 	])

PACKING_BAY = 0b100000
ROW_MARKERS = 0b010000
SHELVES =     0b001000
ITEMS =       0b000100
OBSTACLES =   0b000010
WALLPOINTS =  0b000001

LEFT = 0
RIGHT = 1

MIN_SPEED = 20


class StateMachine:
    def __init__(self):
        # item_collection = itemCollection()
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
        self.row_position_L = [0.3, 1, 1.7] # row positions for left shelf
        self.row_position_R = [1.7, 1, 0.3] # row positions for left shelf
        self.found_shelf = False
        self.found_row = False
        self.at_ps = False
        self.action = []
        self.final_df = {}
        self.goal_position = {}
        self.current_item = 0
        self.draw = False
        self.holding_item = False
        self.i2c = I2C()

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

		# final_df for Order_1.csv
		# 	 Item Number  Shelf  Bay  Height Item Name  Row
		# 0            2      2    0       1    Bottle    1
		# 1            6      1    3       0  Weetbots    0
		# 2            1      0    2       2      Ball    0
		# 3            4      5    2       2      Bowl    2
		# 4            5      4    0       1       Mug    2
		# 5            3      3    3       0      Cube    1



		# final_df for Order_2.csv
		#    Item Number  Shelf  Bay  Height Item Name  Row
		# 0            2      3    1       1    Bottle    1
		# 1            4      2    1       2      Ball    1
		# 2            3      0    0       0      Cube    0
		# 3            1      5    3       2      Bowl    2
		# 4            6      3    0       1       Mug    1
		# 5            5      1    2       0  Weetbots    0
		
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
        self.L_dir = 'S'
        self.R_dir = 'S'
        # self.i2c.grip('open')

    def search_for_ps(self, packStationRangeBearing, rowMarkerRangeBearing):
        self.found_ps = packStationRangeBearing[0] is not None
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        if self.found_row:
            self.L_dir = 'S'
            self.R_dir = 'S'
            self.robot_state = 'MOVE_TO_ROW'
        # Rotate on the spot
        if self.at_ps:
            self.L_dir = 'S'
            self.R_dir = 'S'
            self.robot_state = 'SEARCH_FOR_SHELF'

        
        # Rotate on the spot
        self.rotate('R', MIN_SPEED)

        if self.found_ps:
            self.robot_state = 'MOVE_TO_PS'
            self.L_dir = 'S'
            self.R_dir = 'S'

    def move_to_ps(self, packStationRangeBearing, obstaclesRB):
        self.found_ps = packStationRangeBearing[0] is not None

        if self.found_ps:
            self.goal_position['range'] = packStationRangeBearing[0][0]
            self.goal_position['bearing'] = packStationRangeBearing[0][1]
            print(self.goal_position)

            # Calculate goal velocities
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - 1 < 0.01: # Middle of the area
                self.robot_state = 'SEARCH_FOR_SHELF'
                if self.target_row == 2:
                    self.shelf_side = RIGHT # Will turn left to find Right shelf (5)
                    # can rotate to the left faster with time delay
                else:
                    self.shelf_side = LEFT # Will turn right to find Left shelf (0)
                self.stop()
        else:
            self.robot_state = 'SEARCH_FOR_PS'
            self.stop()

    def search_for_shelf(self, rowMarkerRangeBearing, shelfRangeBearing):
        # Check if the row marker is found
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None
        if self.found_row:
            self.stop()
            self.robot_state = 'MOVE_TO_ROW'

        # Turn direction based on the shelf side
        if self.shelf_side == LEFT:  # Odd
            # Turn right
            self.rotate('R', MIN_SPEED)
            if shelfRangeBearing[0] is not None:
                self.found_shelf = True
                # LEFT SHELF FOUND
            
        else:
            # Turn left
            self.rotate('L', MIN_SPEED)
            if shelfRangeBearing[1] is not None:
                self.found_shelf = True
                # RIGHT SHELF FOUND

        # Rotate on the spot

        if self.found_shelf:
            self.stop()
            self.robot_state = 'MOVE_TO_SHELF'

    def move_to_shelf(self, shelfRangeBearing, obstaclesRB):
        self.found_shelf = False

        if self.shelf_side == LEFT & shelfRangeBearing[0] is not None:
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[0][0]
            self.goal_position['bearing'] = shelfRangeBearing[0][1]
            print(self.robot_state, "Going to: LEFT shelf", self.goal_position)

            # Calculate goal velocities
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            
            if self.goal_position['range'] - self.row_position_L[self.target_row] < 0.01:
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()

        elif self.shelf_side == RIGHT & shelfRangeBearing[1] is not None:
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[1][0]
            self.goal_position['bearing'] = shelfRangeBearing[1][1]
            print(self.robot_state, "Going to: RIGHT shelf", self.goal_position)

            # Calculate goal velocities
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.row_position_R[self.target_row] < 0.01:
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()
        else:
            self.robot_state = 'SEARCH_FOR_SHELF'
            self.stop()
        

    def search_for_row(self, rowMarkerRangeBearing):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        # Rotate on the spot
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = -0.1 if self.shelf_side == LEFT else 0.1

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
            np.append(obstaclesRB, shelfRangeBearing[0])
            np.append(obstaclesRB, shelfRangeBearing[3])

            # Calculate goal velocities
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.goal_bay_position[self.target_bay] < 0.01:
                self.robot_state = 'SEARCH_FOR_ITEM'
                self.stop()
        else:
            self.robot_state = 'SEARCH_FOR_ROW'
            self.stop()

    def search_for_item(self, itemsRB):
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = -0.1 if self.target_shelf % 2 == 1 else 0.1 # Rotate Right if odd, Left if even

        print(f"itemsRB: {itemsRB}")
        for i in itemsRB:
            if itemsRB[i] is not None:
                itemRange = itemsRB[i][0]
                itemBearing = itemsRB[i][1]
                if abs(itemBearing) < 0.05 and itemRange < 0.20:
                    self.robot_state = 'COLLECT_ITEM'
                    self.stop()
    
    def collect_item(self, itemsRB):
        print("Collecting item")
        # self.i2c.grip('open')
        # calibrate the orientation to the item
        for i in itemsRB:
            itemRange = itemsRB[i][0]
            itemBearing = itemsRB[i][1]
            itemLevel = itemsRB[i][2]
            if itemLevel == self.target_height:
                if abs(itemBearing) < 1: # 1 deg, TBC - select the right level
                    # Oriented to the item
                    # move to range 
                    if itemRange < 0.20: # TBC - select the right level
                
                
            # self.i2c.grip('close')
            self.holding_item = True
            self.robot_state = 'ROTATE_TO_EXIT'
        # Check is the item is collected
        
        # self.i2c.lift(self.target_height)
        self.robot_state = 'ROTATE_TO_EXIT'

    # def rotate_to_exit(self, obstaclesRB, wallpointsRB):



    def run_state_machine(self, dataRB):
        self.R_dir = '1'
        self.L_dir = '1'
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = 0
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
            self.collect_item([dataRB[3]])
            return ITEMS
        elif self.robot_state == 'ROTATE_TO_EXIT':
            self.rotate_to_exit(dataRB[4], dataRB[5])
            return SHELVES | WALLPOINTS
        # Add other state transitions...
        # print action
        print("Moving: ", self.LeftmotorSpeed, self.RightmotorSpeed)
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
        # self.i2c.drive(self.LeftmotorSpeed, self.RightmotorSpeed)
        return 0
        
        

    # Moving function
    def rotate(self, direction, speed):
        # Validate inputs
        if direction == "L":
            self.L_dir = '0'
            self.R_dir = '1'
        elif direction == "R":
            self.L_dir = '1'
            self.R_dir = '0'
        
        self.LeftmotorSpeed = speed
        self.RightmotorSpeed = speed
        return
    
    def stop(self):
        self.L_dir = 'S'
        self.R_dir = 'S'
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = 0
        return