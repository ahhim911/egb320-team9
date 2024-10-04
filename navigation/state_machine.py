import numpy as np
import pandas as pd
from enum import Enum
import time 


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
ROW_MARKERS = 0b010001
SHELVES =     0b001000
ITEMS =       0b000100
OBSTACLES =   0b000010
WALLPOINTS =  0b000001

LEFT = 0
RIGHT = 1

MIN_SPEED = 50


class StateMachine:
    def __init__(self):
        # item_collection = itemCollection()
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
        self.row_position_L = [0.45, 1, 1.55] # row positions for left shelf
        self.row_position_R = [1.55, 1, 0.45] # row positions for left shelf
        self.found_shelf = False
        self.rotation_flag = False
        self.shelf_side = None
        self.found_row = False
        self.found_ps = False
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
        df['Row'] = df['Shelf'] // 2 + 1
        min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

        # Ensure the first item is from Row 3 with the highest Bay number
        # highest_bay_row_3 = df[(df['Row'] == 3)].sort_values(by='Bay', ascending=False).head(1)
        # remaining_rows = df.drop(highest_bay_row_3.index)

        # Sort by 'Shelf' in descending order
        sorted_min_shelf  = min_shelf_by_height.sort_values(by='Shelf', ascending=False)
        remaining_rows = df.drop(min_shelf_by_height.index)
        sorted_remaining_rows = remaining_rows.sort_values(by='Shelf', ascending=False)
        self.final_df = pd.concat([sorted_min_shelf, sorted_remaining_rows])

        # Redefine the index
        self.final_df = self.final_df.reset_index(drop=True)

		# final_df for Order_1.csv
		# 	 Item Number  Shelf  Bay  Height Item Name  Row
		# 0            2      2    0       1    Bottle    1+1
		# 1            6      1    3       0  Weetbots    0+1
		# 2            1      0    2       2      Ball    0+1
		# 3            4      5    2       2      Bowl    2+1
		# 4            5      4    0       1       Mug    2+1
		# 5            3      3    3       0      Cube    1+1


        max_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmax()]

		# final_df for Order_2.csv
		#    Item Number  Shelf  Bay  Height Item Name  Row
		# 0            2      3    1       1    Bottle    1+1
		# 1            4      2    1       2      Ball    1+1
		# 2            3      0    0       0      Cube    0+1
		# 3            1      5    3       2      Bowl    2+1
		# 4            6      3    0       1       Mug    1+1
		# 5            5      1    2       0  Weetbots    0+1
		
        # Display the result
        print("Optimised pickup order:")
        print(self.final_df)

        self.robot_state = 'INIT'

    def init_state(self):
        # Set initial parameters and switch to the next state
        # self.robot_state = 'SEARCH_FOR_PS'
        self.robot_state = 'ROTATE_TO_EXIT'
        self.holding_item = False

        # Set the target item position
        print(self.current_item)
        # self.target_shelf = self.final_df['Shelf'][self.current_item]
        self.target_shelf = 0
        # self.target_row = self.final_df['Row'][self.current_item]
        self.target_row = 2
        # self.target_bay = self.final_df['Bay'][self.current_item]
        self.target_bay = 1
        # self.target_height = self.final_df['Height'][self.current_item]
        self.target_height = 0

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
        
        # Rotate on the spot
        self.rotate('R', MIN_SPEED)
        if packStationRangeBearing == [] and rowMarkerRangeBearing == []:
            return
        
        self.found_row = False
        if packStationRangeBearing and len(packStationRangeBearing) > 0:
            print("PS is not NONE", packStationRangeBearing[0])
            self.found_ps = True
        else:
            print("PS is NONE or empty", packStationRangeBearing)

        if rowMarkerRangeBearing != None:
            print("Row: ",rowMarkerRangeBearing)
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
            # self.L_dir = 'S'
            # self.R_dir = 'S'
        # Rotate on the spot
        if self.at_ps:
            # self.L_dir = 'S'
            # self.R_dir = 'S'
            self.robot_state = 'SEARCH_FOR_SHELF'

        if self.found_ps:
            self.robot_state = 'MOVE_TO_PS'
            # self.L_dir = 'S'
            # self.R_dir = 'S'
        
        if self.found_row:
            self.robot_state = 'MOVE_TO_ROW'


    def move_to_ps(self, packStationRangeBearing, obstaclesRB):
        self.found_ps = packStationRangeBearing is not None
        print("PS RB: ", packStationRangeBearing)

        if len(packStationRangeBearing) == 0:
            self.robot_state = 'SEARCH_FOR_PS'
            self.stop()
            self.found_ps = False
        else:
            self.goal_position['range'] = packStationRangeBearing[0][0]
            self.goal_position['bearing'] = packStationRangeBearing[0][1]
            print(self.goal_position)

            # Calculate goal velocities
            self.L_dir = '0'
            self.R_dir = '0'
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            ps_distance = [0.65, 0.9, 1.1]
            if self.goal_position['range'] - ps_distance[self.target_row - 1] < 0.05: # Middle of the area
                self.robot_state = 'SEARCH_FOR_SHELF'
                if self.target_row == 3:
                    self.shelf_side = RIGHT # Will turn left to find Right shelf (5)
                    # can rotate to the left faster with time delay
                else:
                    self.shelf_side = LEFT # Will turn right to find Left shelf (0)
                self.stop()

    def search_for_shelf(self, rowMarkerRangeBearing, shelfRangeBearing):
        # Check if the row marker is found
        self.found_row = False
        if rowMarkerRangeBearing is not None:
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
        if self.found_row:
            self.stop()
            self.robot_state = 'MOVE_TO_ROW'

        shelf_right = None
        if shelfRangeBearing is not None and len(shelfRangeBearing) > 0:
            print("Shelf detected: ", shelfRangeBearing)
            shelf_right = shelfRangeBearing[0][1]
        else:
            print("No shelf detecetd")

        # Turn direction based on the shelf side
        if self.shelf_side == LEFT:  # Odd
            print("Turn Right")
            # Turn right
            self.rotate('R', 60)
            if shelf_right is not None:
                self.found_shelf = True
                # LEFT SHELF FOUND
            
        else:
            # Turn left
            print("Turn Left")
            self.rotate('L', 60)
            if shelf_right is not None:
                if shelf_right[2] < 0 and shelf_right[2] > -10:
                    self.found_shelf = True
                    # RIGHT SHELF FOUND


        if self.found_shelf:
            self.stop()
            self.robot_state = 'MOVE_TO_SHELF'

    def move_to_shelf(self, shelfRangeBearing, obstaclesRB):
        self.found_shelf = False
        print("shelf RB: ", shelfRangeBearing)
        if shelfRangeBearing == []:
            self.robot_state = 'SEARCH_FOR_SHELF'
            self.stop()
            return
        if shelfRangeBearing is not None and self.shelf_side == LEFT:
            # if len(shelfRangeBearing[0][0]) >= 2:  # Ensure we have at least [range, bearing]
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[0][0][1]
            self.goal_position['bearing'] = shelfRangeBearing[0][0][2]
            print(self.robot_state, "Going to: LEFT shelf", self.goal_position)

            # Calculate goal velocities
            self.L_dir = '0'
            self.R_dir = '0'
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.row_position_L[self.target_row - 1] < 0.01:
                print("=================Seach For ROW==============")
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()

        elif shelfRangeBearing is not None and self.shelf_side == RIGHT:
            # if len(shelfRangeBearing[1]) >= 2:  # Ensure we have at least [range, bearing]
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[0][-1][1]
            self.goal_position['bearing'] = shelfRangeBearing[0][-1][2]
            print(self.robot_state, "Going to: RIGHT shelf", self.goal_position)

            # Calculate goal velocities
            self.L_dir = '0'
            self.R_dir = '0'
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.row_position_R[self.target_row - 1] < 0.01:
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()
        


        

    def search_for_row(self, rowMarkerRangeBearing):
        print("Marker interested: ", self.target_row)
        if rowMarkerRangeBearing is not None and rowMarkerRangeBearing != []:
            print("Marker Detected, ", rowMarkerRangeBearing)
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
        # Turn right
        self.rotate('R', 70)

        if self.found_row:
            self.robot_state = 'MOVE_TO_ROW'

    def move_to_row(self, rowMarkerRangeBearing, obstaclesRB, shelfRangeBearing):
        
        if rowMarkerRangeBearing != []:
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
        else:

            return
        if self.found_row:
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            self.goal_position['bearing'] = rowMarkerRangeBearing[2]
            print(self.goal_position)

            # Add shelves to obstacles
            # np.append(obstaclesRB, shelfRangeBearing[0])
            # np.append(obstaclesRB, shelfRangeBearing[3])

            # Calculate goal velocities
            self.L_dir = '0'
            self.R_dir = '0'
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)

            if self.goal_position['range'] - self.goal_bay_position[self.target_bay] < 0.01:
                self.robot_state = 'SEARCH_FOR_ITEM'
                self.rotation_flag = True
                self.stop()
        else:
            self.found_row = False
            self.robot_state = 'SEARCH_FOR_ROW'
            self.stop()

    def search_for_item(self, itemsRB):
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        print("Start Rotate")
        if self.rotation_flag:
            if self.target_shelf % 2 == 1:
                self.rotate("R", 70)
            else:
                self.rotate("L", 70)
            
            print("Moving: ", self.L_dir, self.LeftmotorSpeed, self.R_dir, self.RightmotorSpeed)
            self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
            self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
            time.sleep(2) #TBC duration for 90deg
            self.rotation_flag = False
        else:
            print(f"itemsRB: {itemsRB}")
            for item in itemsRB:
                if item is not None:
                    itemRange = itemsRB[0]
                    itemBearing = itemsRB[1]
                    if abs(itemBearing) < 0.05 and itemRange < 0.20:
                        self.robot_state = 'COLLECT_ITEM'
                        self.stop()
    
    def collect_item(self, itemsRB):
        print("Collecting item")
        # self.i2c.grip('open')
        # calibrate the orientation to the item
        # for i in itemsRB:
        #     itemRange = itemsRB[i][0]
        #     itemBearing = itemsRB[i][1]
        #     itemLevel = itemsRB[i][2]
        #     if itemLevel == self.target_height:
        #         if abs(itemBearing) < 1: # 1 deg, TBC - select the right level
        #             # Oriented to the item
        #             # move to range 
        #             if itemRange < 0.20: # TBC - select the right level
                
                
            # self.i2c.grip('close')
        # self.holding_item = True
        # self.robot_state = 'ROTATE_TO_EXIT'
        # Check is the item is collected
        
        # self.i2c.lift(self.target_height)
        self.robot_state = 'ROTATE_TO_EXIT'

    def rotate_to_exit(self, rowMarkerRangeBearing):
        if self.target_shelf % 2 == 1:
            print("Turn LEFT")
            self.rotate("L", MIN_SPEED)
        else:
            print("Turn RIGHT")
            self.rotate("R", MIN_SPEED)
        if rowMarkerRangeBearing:
            print(rowMarkerRangeBearing)    
            if abs(rowMarkerRangeBearing[2]) < 1:
                self.found_row = True

        # Facing to Row marker
        if self.found_row:
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            self.goal_position['bearing'] = rowMarkerRangeBearing[2]
            print(self.goal_position)

            # Add shelves to obstacles
            # np.append(obstaclesRB, shelfRangeBearing[0])
            # np.append(obstaclesRB, shelfRangeBearing[3])

            # Calculate goal velocities
            self.L_dir = '1'
            self.R_dir = '1'
            self.RightmotorSpeed, self.LeftmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstacles=None)
            




    def run_state_machine(self, dataRB):
        self.R_dir = '1'
        self.L_dir = '1'
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = 0
        request = 0
        # order of objects: [Packing bay, Rowmarkers, Shelves, Items,  Obstacles, Wallpoints] 
        # co-responding to the binary number 0b000000
        if dataRB is None:
            return 0b111111
        print(self.robot_state)
        if self.robot_state == 'INIT':
            self.init_state()
            return 0
        elif self.robot_state == 'SEARCH_FOR_PS':
            self.search_for_ps(dataRB[0], dataRB[1])
            request = PACKING_BAY | ROW_MARKERS
        elif self.robot_state == 'MOVE_TO_PS':
            self.move_to_ps(dataRB[0], dataRB[4])
            request = PACKING_BAY | OBSTACLES
        elif self.robot_state == 'SEARCH_FOR_SHELF':
            self.search_for_shelf(dataRB[1], dataRB[2])
            request = ROW_MARKERS | SHELVES
        elif self.robot_state == 'MOVE_TO_SHELF':
            self.move_to_shelf(dataRB[2], dataRB[4])
            request = SHELVES | OBSTACLES
        elif self.robot_state == 'SEARCH_FOR_ROW':
            self.search_for_row(dataRB[1])
            request = ROW_MARKERS
        elif self.robot_state == 'MOVE_TO_ROW':
            self.move_to_row(dataRB[1], dataRB[4], dataRB[2])
            request = ROW_MARKERS | OBSTACLES | SHELVES
        elif self.robot_state == 'SEARCH_FOR_ITEM':
            self.search_for_item(dataRB[3])
            request = ITEMS
        elif self.robot_state == 'COLLECT_ITEM':
            self.collect_item([dataRB[3]])
            request = ITEMS
        elif self.robot_state == 'ROTATE_TO_EXIT':
            self.rotate_to_exit(dataRB[1])
            request = ROW_MARKERS
        # Add other state transitions...
        # print action
        self.LeftmotorSpeed = int(round(self.LeftmotorSpeed))
        self.RightmotorSpeed = int(round(self.RightmotorSpeed))
        print("Moving: ", self.L_dir, self.LeftmotorSpeed, self.R_dir, self.RightmotorSpeed)
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
        return request
        
        

    # Moving function
    def rotate(self, direction, speed):
        # Validate inputs
        if direction == "L":
            self.L_dir = '1'
            self.R_dir = '0'
        elif direction == "R":
            self.L_dir = '0'
            self.R_dir = '1'
        
        self.LeftmotorSpeed = speed
        self.RightmotorSpeed = speed
        return
    
    def stop(self):
        self.L_dir = 'S'
        self.R_dir = 'S'
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = 0
        return

    def __del__(self):
        self.stop()
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
