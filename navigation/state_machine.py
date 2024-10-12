import numpy as np
import pandas as pd
from enum import Enum
import time 

from Vision.main_vision import Vision
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


ps_return_distance = [0.27, 0.35]


LEFT = 0
RIGHT = 1

MIN_SPEED = 60


class StateMachine():
    def __init__(self):
        # item_collection = itemCollection()
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
        self.row_position_L = [0.4, 1, 1.55] # row positions for left shelf
        self.row_position_R = [1.55, 1, 0.4] # row positions for left shelf
        self.found_shelf = False
        self.rotation_flag = False
        self.pickup_distance = 0.2
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
        self.vision = None

        # Read the object order file
        with open("navigation/Order_1.csv", mode="r", encoding='utf-8-sig') as csv_file:
            # Load the CSV into a DataFrame, automatically using the first row as column names
            df = pd.read_csv(csv_file)

        # Group by 'Height' and find the minimum 'Shelf' for each height
        df['Row'] = df['Shelf'] // 2 + 1
        min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

        # Ensure the first item is from Row 3 with the highest Bay number
        # highest_bay_row_3 = df[(df['Row'] == 3)].sort_values(by='Bay', ascending=False).head(1)
        # remaining_rows = df.drop(highest_bay_row_3.index)

        # Sort by 'Shelf' in descending order
        sorted_min_shelf  = min_shelf_by_height.sort_values(by='Height', ascending=False)
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


        # max_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmax()]

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

    def set_vision(self, vision):
        self.vision = vision

    def item_to_size(self, item_type):
        if item_type == "Bottle":
            size = 0.02 # 0.18 PU dis
        elif item_type == "Ball":
            size = 0.045
        elif item_type == "Cube":
            size = 0.04
        elif item_type == "Bowl":
            size = 0.055
        elif item_type == "Mug":
            size = 0.05
        elif item_type == "Weetbots":
            size = 0.065
        return size
    
    def item_pickup_distance(self, item_type, height):
        Weetbots = [0.21, 0.20, 0.18]
        Bottle = [0.23, 0.22, 0.2]
        Bowls = [0.23, 0.22, 0.2]
        Ball = [0.225, 0.215, 0.205]
        Cube = [0.235, 0.225, 0.215]
        Mug = [0.235, 0.225, 0.215]
        if item_type == "Bottle":
            distance = Bottle[height]
        elif item_type == "Ball":
            distance = Ball[height]
        elif item_type == "Cube":
            distance = Cube[height]
        elif item_type == "Bowl":
            distance = Bowls[height]
        elif item_type == "Mug":
            distance = Mug[height]
        elif item_type == "Weetbots":
            distance = Weetbots[height]
        return distance

    def init_state(self):
        # Set initial parameters and switch to the next state
        self.robot_state = 'SEARCH_FOR_ITEM'
        # self.robot_state = 'MOVE_TO_ROW'
        # self.robot_state = 'COLLECT_ITEM'
        self.holding_item = False

        # Set the target item position
        print(self.current_item)
        # self.target_shelf = self.final_df['Shelf'][self.current_item]
        # self.target_row = self.final_df['Row'][self.current_item]
        # self.target_bay = self.final_df['Bay'][self.current_item]
        # self.target_height = self.final_df['Height'][self.current_item]
        # self.target_item= self.final_df['Item Name'][self.current_item]
        self.target_shelf = 3
        self.target_row = 1
        self.target_bay = 1
        self.target_height = 0
        self.target_item = "Bottle"
        print("Collecting: ", self.target_item)
        if self.vision:
            self.vision.update_item(item_width=self.item_to_size(self.target_item))
        else:
            print("Vision not set")
        self.pickup_distance = self.item_pickup_distance(self.target_item, self.target_height)
        # Set the subtarget shelf (Opposite side of the target shelf)
        if self.target_shelf % 2 == 1:  # Odd
            self.subtarget_shelf = self.target_shelf - 1
        else:  # Even
            self.subtarget_shelf = self.target_shelf + 1

        # Reset the actuators
        self.stop()
        self.i2c.grip(0)

    def search_for_ps(self, packStationRangeBearing, rowMarkerRangeBearing):
        
        # Rotate on the spot
        if self.holding_item:
            self.rotate(LEFT, MIN_SPEED)
        else:
            self.rotate(RIGHT, MIN_SPEED)
        if not packStationRangeBearing and not rowMarkerRangeBearing:
            print("No Markers Detected")
            return
        
        self.found_row = False
        if packStationRangeBearing and len(packStationRangeBearing) > 0:
            print("PS is not NONE", packStationRangeBearing[0])
            self.found_ps = True
        else:
            print("PS is NONE or empty", packStationRangeBearing)

        if rowMarkerRangeBearing:
            print("Row: ",rowMarkerRangeBearing)
            self.found_row = rowMarkerRangeBearing[0] == self.target_row and self.target_row != 1
            if self.found_ps:
                if abs(rowMarkerRangeBearing[2]) < 5: # 5 deg
                    self.robot_state = 'MOVE_TO_PS'

        if self.at_ps:
            self.robot_state = 'SEARCH_FOR_SHELF'

        
        if self.found_row and self.holding_item == False:
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
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            if self.holding_item:
                ps_distance = 0.15
                self.LeftmotorSpeed = self.LeftmotorSpeed + 40
                self.RightmotorSpeed = self.RightmotorSpeed + 40
                self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)
                if self.goal_position['range'] - ps_distance < 0.02:
                    self.stop()
                    self.i2c.grip(0)
                    self.holding_item = False
                    self.robot_state = 'INIT'
            else:
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

        shelf_corner = None
        if shelfRangeBearing is not None and len(shelfRangeBearing) > 0:
            if self.shelf_side == LEFT:  # Odd
                print("Shelf detected(Left): ", shelfRangeBearing[0][0])
                shelf_corner = shelfRangeBearing[0][0]
            if self.shelf_side == RIGHT:  
                print("Shelf detected(Right): ", shelfRangeBearing[-1][1])
                shelf_corner = shelfRangeBearing[-1][1] # Most right shelf, right corner
        else:
            print("No shelf detecetd")

        # Turn direction based on the shelf side
        if self.shelf_side == LEFT:  # Odd
            print("Turn Right")
            # Turn right
            self.rotate(RIGHT, MIN_SPEED)            
            if shelf_corner is not None:
                if abs(shelf_corner[2]) < 5:
                    self.found_shelf = True
            
        else:
            # Turn left
            print("Turn Left")
            self.rotate(LEFT, MIN_SPEED)
            if shelf_corner is not None:
                if shelf_corner[2] < 0 and shelf_corner[2] > -10:
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

            if self.goal_position['range'] - self.row_position_R[self.target_row - 1] < 0.01:
                print("=================Seach For ROW==============")
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()
        
        # Calculate goal velocities
        self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
        self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)


        

    def search_for_row(self, rowMarkerRangeBearing):
        print("Marker interested: ", self.target_row)
        if rowMarkerRangeBearing:
            print("Marker Detected, ", rowMarkerRangeBearing)
            self.found_row = rowMarkerRangeBearing[0] == self.target_row and abs(rowMarkerRangeBearing[2]) < 1
        # Turn right
        self.rotate(RIGHT, MIN_SPEED)

        if self.found_row:
            self.robot_state = 'MOVE_TO_ROW'

    def move_to_row(self, rowMarkerRangeBearing, obstaclesRB, shelfRangeBearing):
        
        if rowMarkerRangeBearing:
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
            if rowMarkerRangeBearing[0] != self.target_row and rowMarkerRangeBearing[0] != 0:
                self.robot_state = 'MOVE_TO_EXIT'
                self.found_row = False
        else:

            return
        if self.found_row:
            print("Row Found: ", self.target_row, ", ", rowMarkerRangeBearing )
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
            self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)
            if self.goal_position['range'] - self.goal_bay_position[self.target_bay] < 0.01:
                self.robot_state = 'SEARCH_FOR_ITEM'
                self.rotation_flag = True
                self.stop()
        else:
            self.found_row = False
            self.robot_state = 'SEARCH_FOR_ROW'
            self.stop()

    def search_for_item(self, itemsRB):
        closest_item = None
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        print("Start Rotate")
        # Rotate to the bay
        if self.target_shelf % 2 == 1:
            self.rotate(RIGHT, MIN_SPEED) # Turn right
            # comment: move the right wheel backwards
        else:
            self.rotate(LEFT, MIN_SPEED) # Turn left
            # comment: move the left wheel backwards

        print(f"itemsRB: {itemsRB}")
        # Check the closest item bearing is in the middle
        if itemsRB is not None:
            # find the smallest itemsRB[:][0] with the target_height in itemsRB[:][2]
            target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            closest_item = min(target_height_itemRB, key=lambda x: x[0]) if target_height_itemRB else None
            if closest_item:
                if abs(closest_item[1]) < 0.25:
                    self.robot_state = 'COLLECT_ITEM'
                    self.stop()

    def move_to_item(self, itemsRB):
        if itemsRB is not None:
            # find the smallest itemsRB[:][0] with the target_height in itemsRB[:][2]
            target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            self.goal_position['range'] = target_height_itemRB[0]
            self.goal_position['bearing'] = target_height_itemRB[1]
            print(self.goal_position)
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, [])
            self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)
            if self.goal_position['range'] - self.pickup_distance < 0.01:
                self.robot_state = 'COLLECT_ITEM'
        else:
            self.robot_state = 'SEARCH_FOR_ITEM'
            return
        

    def collect_item(self, itemsRB):
        if itemsRB is not None:
            # find the smallest itemsRB[:][0] with the target_height in itemsRB[:][2]
            target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            if target_height_itemRB:
                if target_height_itemRB[1] > 0.25:
                    self.rotate(LEFT, MIN_SPEED)
                elif target_height_itemRB[1] < -0.25:
                    self.rotate(RIGHT, MIN_SPEED)
                else:
                    self.stop()

                    print("Collecting item")
                    self.i2c.grip(0)
                    time.sleep(2)
                    self.i2c.lift(self.target_height + 1)
                    time.sleep(6)
                    self.i2c.grip(1)
                    time.sleep(2)
                    self.move(1, MIN_SPEED, MIN_SPEED)
                    time.sleep(2)
                    self.stop()
                    self.i2c.lift(1)
                    time.sleep(6)
                    self.robot_state = 'CHECK_ITEM'
            else:
                
                self.robot_state = 'SEARCH_FOR_ITEM'
                return
        else:
            self.robot_state = 'SEARCH_FOR_ITEM'
            return
                
    def check_item(self, itemsRB):
        if itemsRB is not None:
            # find the smallest itemsRB[:][0] with the target_height in itemsRB[:][2]
            target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            # Check is the item is collected
            if target_height_itemRB == None:
                self.holding_item = True
            self.robot_state = 'ROTATE_TO_EXIT'

    def rotate_to_exit(self, rowMarkerRangeBearing):
        if self.target_shelf % 2 == 1:
            self.rotate(LEFT, MIN_SPEED)
        else:
            self.rotate(RIGHT, MIN_SPEED)
        if rowMarkerRangeBearing:
            print(rowMarkerRangeBearing)    
            if abs(rowMarkerRangeBearing[2]) < 1:
                self.robot_state = "MOVE_TO_EXIT"

            
    def move_to_exit(self, rowMarkerRangeBearing):
        # Facing to Row marker
        if rowMarkerRangeBearing:
            print(rowMarkerRangeBearing)    
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            self.goal_position['bearing'] = rowMarkerRangeBearing[2]
            print(self.goal_position)

            # Add shelves to obstacles
            # np.append(obstaclesRB, shelfRangeBearing[0])
            # np.append(obstaclesRB, shelfRangeBearing[3])

            # Calculate goal velocities
            self.L_dir = '1' # Backwards
            self.R_dir = '1'# Backwards
            # flipped the left and right
            self.RightmotorSpeed, self.LeftmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstacles=None)
            if self.goal_position['range'] > 1.2:
                self.robot_state = "SEARCH_FOR_PS"
        else: 
            self.robot_state = "ROTATE_TO_EXIT"



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
        elif self.robot_state == 'MOVE_TO_ITEM':
            self.move_to_item(dataRB[3])
            request = ITEMS
        elif self.robot_state == 'COLLECT_ITEM':
            self.collect_item([dataRB[3]])
            request = ITEMS
        elif self.robot_state == 'CHECK_ITEM':
            self.check_item(dataRB[3])
            request = ITEMS
        elif self.robot_state == 'ROTATE_TO_EXIT':
            self.rotate_to_exit(dataRB[1])
            request = ROW_MARKERS
        elif self.robot_state == 'MOVE_TO_EXIT':
            self.move_to_exit(dataRB[1])
            request = ROW_MARKERS
        # Add other state transitions...
        return request
        

    # Moving function
    def move(self, direction, L_speed, R_speed):
        # Validate inputs
        if direction == 0: #forward
            self.L_dir = '0'
            self.R_dir = '0'
        elif direction == 1: #backward
            self.L_dir = '1'
            self.R_dir = '1'
        
        self.LeftmotorSpeed = int(round(L_speed))
        self.RightmotorSpeed = int(round(R_speed))
        print("Moving: ", self.L_dir, self.LeftmotorSpeed, self.R_dir, self.RightmotorSpeed)
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed)
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right



    def rotate(self, direction, speed):
        # Validate inputs
        if direction == LEFT:
            self.L_dir = '1'
            self.R_dir = '0'
        elif direction == RIGHT:
            self.L_dir = '0'
            self.R_dir = '1'
        
        self.LeftmotorSpeed = speed
        self.RightmotorSpeed = speed
        print("Moving: ", self.L_dir, self.LeftmotorSpeed, self.R_dir, self.RightmotorSpeed)
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
        return
    
    def stop(self):
        self.L_dir = 'S'
        self.R_dir = 'S'
        self.LeftmotorSpeed = 0
        self.RightmotorSpeed = 0
        print("MOTORS STOP")
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
        return

    def __del__(self):
        self.stop()
        self.i2c.DCWrite(1, self.L_dir, self.LeftmotorSpeed) #Left
        self.i2c.DCWrite(2, self.R_dir, self.RightmotorSpeed) #Right
