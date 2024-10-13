import numpy as np
import pandas as pd
from enum import Enum
import time 
import logging
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
# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("state_machine.log", mode='w')
    ]
)
#logging.getLogger('pandas').setLevel(logging.WARNING)  # Only show warnings and errors for picamera2
logger = logging.getLogger(__name__)



LEFT = 0
RIGHT = 1
ON = 1
OFF = 0
MIN_SPEED = 95


class StateMachine():
    """
    StateMachine class for managing the robot's state transitions and actions.
    Attributes:
        goal_bay_position (list): Bay positions in the row.
        row_position_L (list): Entry positions for the left shelf.
        row_position_R (list): Entry positions for the right shelf.
        found_shelf (bool): Flag indicating if the shelf is found.
        rotation_flag (bool): Flag for rotation.
        pickup_distance (float): Distance for picking up items.
        shelf_side (str): Side of the shelf.
        found_row (bool): Flag indicating if the row is found.
        found_ps (bool): Flag indicating if the packing station is found.
        at_ps (bool): Flag indicating if at the packing station.
        action (list): List of actions.
        final_df (dict): Final DataFrame for item order.
        goal_position (dict): Goal position for the robot.
        current_item (int): Index of the current item.
        draw (bool): Flag for drawing.
        holding_item (bool): Flag indicating if holding an item.
        i2c (I2C): I2C communication object.
        vision (object): Vision system object.
        robot_state (str): Current state of the robot.
    Methods:
        __init__(): Initializes the StateMachine with default values and reads the object order file.
        set_vision(vision): Sets the vision system object.
        item_to_size(item_type): Returns the size of the given item type.
        item_pickup_distance(item_type, height): Returns the pickup distance for the given item type and height.
        init_state(): Initializes the state machine and sets the initial parameters.
        search_for_ps(packStationRangeBearing, rowMarkerRangeBearing): Searches for the packing station.
        move_to_ps(packStationRangeBearing, obstaclesRB): Moves to the packing station.
        search_for_shelf(rowMarkerRangeBearing, shelfRangeBearing): Searches for the shelf.
        move_to_shelf(shelfRangeBearing, obstaclesRB): Moves to the shelf.
        search_for_row(rowMarkerRangeBearing): Searches for the row.
        move_to_row(rowMarkerRangeBearing, obstaclesRB, shelfRangeBearing): Moves to the row.
        search_for_item(itemsRB): Searches for the item.
        move_to_item(itemsRB): Moves to the item.
        collect_item(itemsRB): Collects the item.
        check_item(itemsRB): Checks if the item is collected.
        rotate_to_exit(rowMarkerRangeBearing): Rotates to exit.
        move_to_exit(rowMarkerRangeBearing): Moves to the exit.
        run_state_machine(dataRB): Runs the state machine based on the current state and sensor data.
        move(direction, L_speed, R_speed): Moves the robot in the specified direction with given speeds.
        rotate(direction, speed): Rotates the robot in the specified direction with given speed.
        stop(): Stops the robot.
        __del__(): Destructor to stop the robot and clean up.
    """
    #===========================================================================
      #===========================================================================
  # STATE FUNCTIONS

    # INITIALIZATION
    #===========================================================================
    def __init__(self):
        self.goal_bay_position = [0.8, 0.58, 0.32, 0.125] # bay positions in the row
        self.row_position_L = [0.38, 1, 1.55] # Entry positions for left shelf
        self.row_position_R = [1.55, 1, 0.40] # Entry positions for Right shelf
        self.ps_return_distance = [0.10, 0.35]
        self.found_shelf = False
        self.rotation_complete = True
        self.wait_for_shelf_alignment = False
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
        self.i2c = I2C()
        self.vision = None
        self.holding_item = False

        # Read the object order file
        with open("navigation/Order_3.csv", mode="r", encoding='utf-8-sig') as csv_file:
            # Load the CSV into a DataFrame, automatically using the first row as column names
            df = pd.read_csv(csv_file)

        # Group by 'Height' and find the minimum 'Shelf' for each height
        df['Row'] = df['Shelf'] // 2 + 1
        # min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

        # Ensure the first item is from Row 3 with the highest Bay number
        # highest_bay_row_3 = df[(df['Row'] == 3)].sort_values(by='Bay', ascending=False).head(1)
        # remaining_rows = df.drop(highest_bay_row_3.index)

        # Sort by 'Shelf' in descending order
        # sorted_min_shelf  = min_shelf_by_height.sort_values(by='Height', ascending=False)
        # remaining_rows = df.drop(min_shelf_by_height.index)
        # sorted_remaining_rows = remaining_rows.sort_values(by='Shelf', ascending=False)
        # self.final_df = pd.concat([sorted_min_shelf, sorted_remaining_rows])

        # Redefine the index
        self.final_df = df
        # self.final_df = self.final_df.reset_index(drop=True)

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
        logger.debug(f"Final: {self.final_df}")
        

        self.robot_state = 'INIT'

    def set_vision(self, vision):
        self.vision = vision

    #===========================================================================
    # HELPER FUNCTIONS
    #===========================================================================
    def item_to_size(self, item_type):
        if item_type == "Bottle":
            size = 0.02 
        elif item_type == "Ball":
            size = 0.045
        elif item_type == "Cube":
            size = 0.037
        elif item_type == "Bowl":
            size = 0.055
        elif item_type == "Mug":
            size = 0.05
        elif item_type == "Weetbots":
            size = 0.065
        return size
    
    def item_pickup_distance(self, item_type, height):
        Weetbots = [0.17, 0.2, 0.19]
        Bottle = [0.17, 0.19, 0.18]
        Bowls = [0.18, 0.2, 0.2]
        Ball = [0.18, 0.19, 0.19]
        Cube = [0.15, 0.17, 0.17]
        Mug = [0.17, 0.19, 0.26]
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

    #===========================================================================
    # STATE MACHINE
    #===========================================================================
    def init_state(self):
        """
        Initialize the state of the robot.
        This method sets the initial parameters for the robot's state machine and 
        switches to the 'SEARCH_FOR_ITEM' state. It initializes the robot's state 
        variables, sets mockup values for the target item position, and updates 
        the vision system if available. Additionally, it calculates the pickup 
        distance for the target item and sets the subtarget shelf based on the 
        target shelf's parity. Finally, it resets the actuators.
        Attributes:
            robot_state (str): The current state of the robot.
            holding_item (bool): Indicates whether the robot is holding an item.
            target_shelf (int): The shelf number where the target item is located.
            target_row (int): The row number where the target item is located.
            target_bay (int): The bay number where the target item is located.
            target_height (int): The height of the target item.
            target_item (str): The name of the target item.
            subtarget_shelf (int): The shelf number opposite to the target shelf.
            pickup_distance (float): The distance required to pick up the target item.
        Prints:
            Information about the current item being collected.
            Warning if the vision system is not set.
        """
        # Set initial parameters and switch to the next state
        self.robot_state = 'SEARCH_FOR_PS'
        # self.robot_state = 'MOVE_TO_ROW'
        # self.robot_state = 'MOVE_TO_EXIT'
        # self.robot_state = 'COLLECT_ITEM'
        # self.robot_state = 'EXIT_PS'
        # self.holding_item = True

        # Set the target item position
        
        self.target_shelf = self.final_df['Shelf'][self.current_item]
        self.target_row = self.final_df['Row'][self.current_item]
        self.target_bay = self.final_df['Bay'][self.current_item]
        self.target_height = self.final_df['Height'][self.current_item]
        self.target_item= self.final_df['Item Name'][self.current_item]

        # Mockup values
        # self.target_shelf = 2
        # self.target_row = 1
        # self.target_bay = 3
        # self.target_height = 2
        # self.target_item = "Bottle"

        print("Collecting the ", self.current_item + 1, "item : ", self.target_item)
        if self.vision:
            logger.debug(f"Updating item: {self.target_item}")
            self.vision.update_item(item_width=self.item_to_size(self.target_item))
            logger.info("Vision set, item width updated")
        else:
            print("Vision not set")
            logger.warning("Vision not set==================")
        self.pickup_distance = self.item_pickup_distance(self.target_item, self.target_height)
        # Set the subtarget shelf (Opposite side of the target shelf)
        if self.target_shelf % 2 == 1:  # Odd
            self.subtarget_shelf = self.target_shelf - 1
        else:  # Even
            self.subtarget_shelf = self.target_shelf + 1

        # Reset the actuators
        self.i2c.led(1,ON)
        time.sleep(0.05)
        self.i2c.led(2,OFF)
        time.sleep(0.05)
        self.i2c.led(3,OFF)
        time.sleep(0.05)
        self.stop()
        time.sleep(0.05)
        self.i2c.grip(0) # Gripper Open

    def search_for_ps(self, packStationRangeBearing, rowMarkerRangeBearing):
        """
        Searches for the packing station (PS) and row markers, and updates the robot's state accordingly.
        Args:
            packStationRangeBearing (list): A list containing range and bearing information of the packing station.
            rowMarkerRangeBearing (list): A list containing range and bearing information of the row markers.
        Behavior:
            - Rotates the robot on the spot based on whether it is holding an item.
            - If no markers are detected, prints a message and returns.
            - Checks if the packing station is detected and updates the `found_ps` attribute.
            - Checks if the row marker is detected and updates the `found_row` attribute.
            - If the packing station is found and the row marker's bearing is within 5 degrees, updates the robot state to 'MOVE_TO_PS'.
            - If the robot is at the packing station, updates the robot state to 'SEARCH_FOR_SHELF'.
            - If the target row is found and the robot is not holding an item, updates the robot state to 'MOVE_TO_ROW'.
        """
        
        # Rotate on the spot
        if self.holding_item:
            print("Turning right")
            # if found
            self.rotate(RIGHT, MIN_SPEED + 10)
        elif self.found_ps == True:
            self.rotate(RIGHT, MIN_SPEED - 10)
        else:
            print("Turning Right")
            self.rotate(RIGHT, MIN_SPEED + 5)

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
            # self.found_row = rowMarkerRangeBearing[0] == self.target_row and self.target_row != 1
            if self.found_ps and rowMarkerRangeBearing[0] == 0: # PS marker = 0 
                if abs(rowMarkerRangeBearing[2]) < 10: # -10 to 10 deg
                    self.found_ps = False
                    if self.holding_item:
                        self.robot_state = 'MOVE_TO_PS_MARKER'
                    else:
                        self.robot_state = 'MOVE_TO_PS'

        elif self.found_ps: # if it doesnt see the PS marker or the bearing isnt within range
            if abs(packStationRangeBearing[0][1]) < 2: # check PS ramp bearing
                self.found_ps = False
                if self.holding_item:
                    self.robot_state = 'MOVE_TO_PS_MARKER'
                else:
                    self.robot_state = 'MOVE_TO_PS'

        if self.at_ps:
            self.robot_state = 'SEARCH_FOR_SHELF'

        

    def move_to_ps_marker(self, rowMarkerRangeBearing, obstaclesRB):
        if not rowMarkerRangeBearing:
            self.robot_state = 'SEARCH_FOR_PS'
            self.stop()
            time.sleep(1)
            self.found_ps = False
        else:
            print("PS RB: ", rowMarkerRangeBearing[0])
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            self.goal_position['bearing'] = rowMarkerRangeBearing[2] * 2
            print(self.goal_position)

            # Calculate goal velocities
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            if self.holding_item:
                self.LeftmotorSpeed = self.LeftmotorSpeed
                self.RightmotorSpeed = self.RightmotorSpeed
                self.move(0, self.LeftmotorSpeed + 15, self.RightmotorSpeed + 15)
                if self.goal_position['range'] - 0.26 < 0.01:
                # if self.goal_position['range'] - self.ps_return_distance[0] < 0.01:
                    self.stop()
                    time.sleep(0.1)
                    self.i2c.grip(0)
                    time.sleep(1)
                    self.holding_item = False
                    self.current_item += 1
                    self.robot_state = 'EXIT_PS'


    def move_to_ps(self, packStationRangeBearing, obstaclesRB): # Using Ramp to determine the distance
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
                self.LeftmotorSpeed = self.LeftmotorSpeed + 50
                self.RightmotorSpeed = self.RightmotorSpeed + 50
                self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)
                if self.goal_position['range'] - self.ps_return_distance[0] < 0.01:
                    self.stop()
                    time.sleep(0.1)
                    self.i2c.grip(0)
                    time.sleep(5)
                    self.holding_item = False
                    self.robot_state = 'EXIT_PS'
            else:
                ps_distance = [0.65, 0.9, 1]
                if self.goal_position['range'] - ps_distance[self.target_row - 1] < 0.05: # Middle of the area
                    self.robot_state = 'SEARCH_FOR_SHELF'
                    if self.target_row == 3:
                        self.shelf_side = RIGHT # Will turn left to find Right shelf (5)
                        # can rotate to the left faster with time delay (not practical*)
                    else:
                        self.shelf_side = LEFT # Will turn right to find Left shelf (0)
                    self.stop()
                elif self.target_row == 3:
                    self.move(0,MIN_SPEED,MIN_SPEED)
                    

    def search_for_shelf(self, rowMarkerRangeBearing, shelfRangeBearing):
        # Check if the row marker is found
        self.found_row = False
        self.found_shelf = False
        if rowMarkerRangeBearing is not None:
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
        if self.found_row:
            self.stop()
            self.robot_state = 'MOVE_TO_ROW'

        shelf_corner = None
        if self.shelf_side == LEFT:  # Odd
            # Turn right
            print("Turn Right")
            self.rotate(RIGHT, MIN_SPEED + 5)   

            if shelfRangeBearing is not None and len(shelfRangeBearing) > 0:    
                print("Shelf detected(Left): ", shelfRangeBearing[0][0])
                shelf_corner = shelfRangeBearing[0][0]
                if abs(shelf_corner[2]) < 5:
                    self.found_shelf = True
        elif self.shelf_side == RIGHT:  
            print("Turn Left")
            self.rotate(LEFT, MIN_SPEED + 5)

            if shelfRangeBearing is not None and len(shelfRangeBearing) > 0:
                print("Shelf detected(Right): ", shelfRangeBearing[-1][1])
                shelf_corner = shelfRangeBearing[-1][1] # Most right shelf, right corner
                # if shelf_corner[2] < -10 and shelf_corner[2] > -20:
                if -20 < shelf_corner[2] < -10:
                    logger.info("FOUND RIGHT SHELF", shelf_corner[2])
                    self.found_shelf = True
                    # RIGHT SHELF FOUND
        else:
            print("No shelf detecetd")
            

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
            self.goal_position['bearing'] = shelfRangeBearing[0][0][2] - 5 # adding offest to bearing 
            print(self.robot_state, "Going to: LEFT shelf", self.goal_position)

            if self.goal_position['range'] - self.row_position_L[self.target_row - 1] < 0.01:
                print("=================Seach For ROW============== LEFT")
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()
            if self.row_position_L[self.target_row - 1] - self.goal_position['range']  > 0.1: #
                if self.target_row == 1:
                    print("TOO CLOSE - Move Backwards (row 1)")
                    self.move(1, MIN_SPEED - 20, MIN_SPEED - 20)  # Move backward at a slower speed
                else:
                    print("TOO CLOSE - CHANGE TO RIGHT")
                    self.move(1, MIN_SPEED, MIN_SPEED)
                    time.sleep(1)
                    self.robot_state = 'SEARCH_FOR_SHELF'
                    self.shelf_side = RIGHT

        elif shelfRangeBearing is not None and self.shelf_side == RIGHT:
            # if len(shelfRangeBearing[1]) >= 2:  # Ensure we have at least [range, bearing]
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[0][-1][1]
            self.goal_position['bearing'] = shelfRangeBearing[0][-1][2] + 5
            print(self.robot_state, "Going to: RIGHT shelf", self.goal_position)

            if self.goal_position['range'] - self.row_position_R[self.target_row - 1] < 0.01:
                print("=================Seach For ROW============== RIGHT")
                self.robot_state = 'SEARCH_FOR_ROW'
                self.stop()
            if self.row_position_R[self.target_row - 1] - self.goal_position['range']  > 0.1:
                print("TOO CLOSE - CHANGE TO LEFT")
                self.robot_state = 'SEARCH_FOR_SHELF'
                self.shelf_side = LEFT
        
        # Calculate goal velocities
        self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
        self.move(0, self.LeftmotorSpeed + 20, self.RightmotorSpeed + 20)


        

    def search_for_row(self, rowMarkerRangeBearing):
        print("Marker interested: ", self.target_row)
        if rowMarkerRangeBearing:
            print("Marker Detected, ", rowMarkerRangeBearing)
            if rowMarkerRangeBearing[0] == self.target_row and self.rotation_complete:
                self.stop()
                time.sleep(0.5)
                self.rotation_complete = False
            if rowMarkerRangeBearing[0] != 0 and not self.rotation_complete:
                if rowMarkerRangeBearing[2] < -10:
                    self.rotate(LEFT, MIN_SPEED - 15)
                elif rowMarkerRangeBearing[2] > 10:
                    self.rotate(RIGHT, MIN_SPEED - 15)
            


            self.found_row = rowMarkerRangeBearing[0] == self.target_row and abs(rowMarkerRangeBearing[2]) < 10
        # Turn left
        if self.rotation_complete and self.shelf_side == RIGHT:
            self.rotate(LEFT, MIN_SPEED + 5)
        if self.rotation_complete and self.shelf_side == LEFT:
            self.rotate(RIGHT, MIN_SPEED + 5)
        

        if self.found_row:
            self.rotation_complete = True
            self.robot_state = 'MOVE_TO_ROW'

    def move_to_row(self, rowMarkerRangeBearing, obstaclesRB, shelfRangeBearing):
        error_angle = 0
        # Check if shelfRangeBearing has data for left and right shelves
        if shelfRangeBearing and len(shelfRangeBearing) > 1:
            print("SHELF: ", shelfRangeBearing)
            L_angle = shelfRangeBearing[0][1][1]  # Left shelf, right point range
            R_angle = shelfRangeBearing[-1][0][1]  # Right shelf, left point range

            # Calculate the error angle between the left and right shelves
            error_angle = R_angle - L_angle
            print("SHELF ERROR: ", error_angle)

        if rowMarkerRangeBearing:
            self.found_row = rowMarkerRangeBearing[0] == self.target_row
            if rowMarkerRangeBearing[0] != self.target_row and rowMarkerRangeBearing[0] != 0:
                self.robot_state = 'MOVE_TO_EXIT' # TBC Search_for_row???
                self.found_row = False
        else:

            return
        if self.found_row:
            print("Row Found: ", self.target_row, ", ", rowMarkerRangeBearing )
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            # Adjust the goal bearing by including the shelf error angle
            self.goal_position['bearing'] = (rowMarkerRangeBearing[2] * 1.3) + (error_angle * 400)
            # self.goal_position['bearing'] = (error_angle * 600)
            print("GOAL POSITION ANGLE (with shelf correction): ", self.goal_position['bearing'])
            print(self.goal_position)

            # Add shelves to obstacles
            # if shelfRangeBearing is not None and len(shelfRangeBearing) > 1:
            #     np.append(obstaclesRB, shelfRangeBearing[0][2])
            #     np.append(obstaclesRB, shelfRangeBearing[1][1])

            # Calculate goal velocities
            self.L_dir = '0'
            self.R_dir = '0'
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstaclesRB)
            self.move(0, self.LeftmotorSpeed, self.RightmotorSpeed)
            if self.goal_position['range'] - self.goal_bay_position[self.target_bay] < 0.01:
                self.robot_state = 'SEARCH_FOR_ITEM'
                self.rotation_complete = True
                self.wait_for_shelf_alignment = True
                self.stop()
                time.sleep(0.3)
        else:
            self.found_row = False
            self.robot_state = 'SEARCH_FOR_ROW'
            self.stop()

    def search_for_item(self, itemsRB, shelfRangeBearing):
        closest_item = None
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        logger.info(f"search_for_item state started")
        # Rotate to the bay
        if self.rotation_complete:
            logger.info(f"Step 1 Rotation")
            if self.target_shelf % 2 == 1: # shelf is odd
                    print("Start Rotate Right 90deg")
                    # move the right wheel backwards
                    self.move(1, 0, MIN_SPEED+10) # Turn right

                    # Now check for the alignment condition
                    if self.wait_for_shelf_alignment and self.target_bay >= 2 and shelfRangeBearing:
                        left_corner_bearing = shelfRangeBearing[-1][0][2]  # Left corner bearing
                        # Ensure the left corner is aligned within 0 to 15 degrees
                        if 0 <= left_corner_bearing <= 15:
                            print("Shelf aligned :)")
                            self.wait_for_shelf_alignment = False  # Alignment complete, proceed

                    # Return early if still waiting for alignment
                    if self.wait_for_shelf_alignment:
                        print("waiting for shelf alignment")
                        return
                    
                    if shelfRangeBearing:
                        print("SHELF: ", shelfRangeBearing)
                        if shelfRangeBearing[-1][0][1] <= 0.41 and shelfRangeBearing[-1][0][2] <= -33:
                            logger.info(f"EXIT Step 1 ROTATION")
                            self.rotation_complete = False
            else:
                    print("Start Rotate Left 90deg")
                    # move the left wheel backwards
                    self.move(1, MIN_SPEED+10, 0) # Turn left

                    # Now check for the alignment condition
                    if self.wait_for_shelf_alignment and self.target_bay >= 2 and shelfRangeBearing:
                        right_corner_bearing = shelfRangeBearing[0][1][2]  # right corner bearing
                        # Ensure the right corner is aligned within -15 to 0 degrees
                        if -15 <= right_corner_bearing <= 0:
                            print("Shelf aligned :)")
                            self.wait_for_shelf_alignment = False  # Alignment complete, proceed

                    # Return early if still waiting for alignment
                    if self.wait_for_shelf_alignment:
                        print("waiting for shelf alignment")
                        return
                    
                    if shelfRangeBearing:
                        print("SHELF: ", shelfRangeBearing)
                        if shelfRangeBearing[0][1][1] <= 0.41 and shelfRangeBearing[0][1][2] >= 33:
                            logger.info(f"EXIT Step 1 ROTATION")
                            self.rotation_complete = False
        else:
            logger.info(f"Step 2 Rotation")
            print(f"itemsRB: {itemsRB}")
            # Check the closest item bearing is in the middle
            if itemsRB is not None and len(itemsRB) > 0:
                # Find all items at the target height
                target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]

                if target_height_itemRB:
                    # Sort items by range (get the two closest items)
                    closest_items = sorted(target_height_itemRB, key=lambda x: x[0])[:2]  # Get the two closest items by range
                    print("Closest items:", closest_items)

                    if len(closest_items) == 1:
                        # Only one item available, pick it
                        closest_item = closest_items[0]
                    else:
                        # We have two closest items, prioritize based on the bearing
                        if self.target_shelf % 2 == 0:
                            # Even shelf: prioritize smaller bearing
                            closest_item = min(closest_items, key=lambda x: x[1])
                            print(f"Even shelf: Prioritizing smaller bearing: {closest_item}")
                        else:
                            # Odd shelf: prioritize larger bearing
                            closest_item = max(closest_items, key=lambda x: x[1])
                            print(f"Odd shelf: Prioritizing larger bearing: {closest_item}")

                    # Now that we have the correct closest item, check if the bearing is centered
                    if closest_item:
                        if abs(closest_item[1]) < 2:
                            logger.info(f"EXIT Step 2 ROTATION")
                            self.robot_state = 'MOVE_TO_ITEM'
                            self.i2c.led(1,OFF)
                            time.sleep(0.05)
                            self.i2c.led(2,ON)
                            time.sleep(0.05)
                            self.stop()
                            self.rotation_complete = True
                        else:
                            if closest_item[1] < 0:
                                self.rotate(LEFT, MIN_SPEED-5)
                            else:
                                self.rotate(RIGHT, MIN_SPEED-5)                    
                    else:
                        logger.info(f"No Closest item")
                        self.move(0, MIN_SPEED, MIN_SPEED) # Move forward

    def move_to_item(self, itemsRB):
        logger.info(f"MOVE TO ITEM")
        if itemsRB is not None and len(itemsRB) > 0:
            # logger.info(f"item detected: ", itemsRB)

            target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            print("Target height", target_height_itemRB)
            if target_height_itemRB:
                # Sort items by range (get the two closest items)
                closest_items = sorted(target_height_itemRB, key=lambda x: x[0])[:2]  # Get the two closest items by range
                print("Closest items:", closest_items)

                if len(closest_items) == 1:
                    # Only one item available, pick it
                    closest_item = closest_items[0]
                else:
                    # We have two closest items, prioritize based on the bearing
                    closest_item = min(closest_items, key=lambda x: abs(x[1]))
                    print(f"Prioritizing smaller bearing: {closest_item}")

                self.goal_position['range'] = closest_item[0]
                self.goal_position['bearing'] = closest_item[1] * 2.5
                print(self.goal_position)

                 # Calculate motor speeds for moving towards the item
                self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, [])
                self.move(0, self.LeftmotorSpeed - 15, self.RightmotorSpeed - 15)
                
                # Check if robot is close enough to stop and collect the item
                logger.debug(f"Trying to pick up: {self.target_item}, pickup dis: {self.pickup_distance}")
                distance_to_item = self.goal_position['range'] - self.pickup_distance + 0.00
                print(f"Distance to item: {distance_to_item}")

                if distance_to_item <= 0.015:
                    logger.info("Item within range and bearing aligned. Stopping to collect.")
                    self.stop()
                    self.robot_state = 'COLLECT_ITEM'
            else:
                # if self.target_height ==
                logger.info(f"No target height item, try move backward")
                print("No target height item, try move backward")
                self.move(1,MIN_SPEED-20, MIN_SPEED-20)

        else:
            logger.info(f"No ITEM DETECTED in MOVE_TO_ITEM")
            self.robot_state = 'SEARCH_FOR_ITEM'
            return
        

    def collect_item(self, itemsRB):
        logger.info(f"COLLECT ITEM")
        if itemsRB is not None:
            
            self.stop()
            # time.sleep(1)

            print("Collecting item")
            self.i2c.grip(0)
            time.sleep(0.1)
            if self.target_height == 2: # Level 3 Move Forward Longer Duration
                self.i2c.lift(self.target_height + 1)
                print("Lifting")
                time.sleep(4)
                if self.target_item != 'Bottle':
                    self.move(0, MIN_SPEED-20, MIN_SPEED-20) # move forward
                    time.sleep(0.6)
                    self.stop()
            if self.target_height == 1: # Level 2 Move Forward Shorter Duration
                self.i2c.lift(self.target_height + 1)
                time.sleep(3)
                if self.target_item != 'Bottle':
                    self.move(0, MIN_SPEED-20, MIN_SPEED-20) # move forward
                    time.sleep(0.4)
                    self.stop()
            self.i2c.grip(1)
            print("Grip")
            time.sleep(1.6)
            self.move(1, MIN_SPEED-20, MIN_SPEED-20) # move backwards
            if self.target_height == 2: # Level 3 Move Backward Longer Duration
                time.sleep(1.1)
            else:
                time.sleep(0.9)
            self.stop()
            if self.target_height != 0:
                self.i2c.lift(1)
                time.sleep(3)
            self.robot_state = 'CHECK_ITEM'
            # else:
            #     logger.info(f"No ITEM DETECTED in target height in collect_item")
            #     print("No item detected in target height")
            #     self.robot_state = 'SEARCH_FOR_ITEM'
            #     return
        else:
            logger.info(f"No ITEM DETECTED in collect_item")
            print("No item detected")
            self.robot_state = 'SEARCH_FOR_ITEM'
            return
                
    def check_item(self, itemsRB):
        if itemsRB is not None:
            # find the smallest itemsRB[:][0] with the target_height in itemsRB[:][2]
            # target_height_itemRB = [item for item in itemsRB if item[2] == self.target_height + 1]
            # Check is the item is collected
            # if target_height_itemRB == None:
            
            self.i2c.led(2,OFF)
            time.sleep(0.05)
            self.i2c.led(3,ON)
            time.sleep(0.05)
            self.holding_item = True
            self.robot_state = 'ROTATE_TO_EXIT' # should create a retry method if it misses it?
            # call check item inside the rotate_to_exit state
            # should check if item is in level 1 with a bearing between -5 and 5 degrees
            # IF true then proceed to move to exit, but if false initiate search for item again
            # but only retry once, so have a retry flag that is set within the move to row state
            # and cleared once the retry has occurred, so going to the rotate to exit state it should be set to false.


    def rotate_to_exit(self, rowMarkerRangeBearing):
        logger.info(f"ROTATE TO EXIT")
        if rowMarkerRangeBearing:
            logger.info(f"Row Marker Found")
            print("Row Marker Found: ", rowMarkerRangeBearing)    
            if abs(rowMarkerRangeBearing[2]) < 3:
                self.robot_state = "MOVE_TO_EXIT"
            # else: 
            #     if rowMarkerRangeBearing[2] < -1:
            #         self.rotate(LEFT, MIN_SPEED-10)
            #     if rowMarkerRangeBearing[2] > 1:
            #         self.rotate(RIGHT, MIN_SPEED-10)
        else:
            if self.target_shelf % 2 == 1:
                self.rotate(LEFT, MIN_SPEED)
            else:
                self.rotate(RIGHT, MIN_SPEED)


            
    def move_to_exit(self, rowMarkerRangeBearing, shelfRangeBearing):
        # Facing to Row marker
        error_angle = 0
        if shelfRangeBearing and len(shelfRangeBearing) > 1:
            print("SHELF: ", shelfRangeBearing)
            L_angle = shelfRangeBearing[0][1][1] # Left shelf right point, bearing
            R_angle = shelfRangeBearing[-1][0][1]

            error_angle = L_angle - R_angle
            print("SHELF ERROR: ",error_angle)

        if rowMarkerRangeBearing:
            print(rowMarkerRangeBearing)    
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            # self.goal_position['bearing'] =  (error_angle * 500)
            self.goal_position['bearing'] = rowMarkerRangeBearing[2] + (error_angle * 400)
            print("GOAL POSITION ANGLE: ",self.goal_position['bearing'])
            #print(self.goal_position)

            # Add shelves to obstacles
            # np.append(obstaclesRB, shelfRangeBearing[0])
            # np.append(obstaclesRB, shelfRangeBearing[3])

            # flipped the left and right
            self.LeftmotorSpeed, self.RightmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, obstacles=None)
            self.move(1, self.RightmotorSpeed, self.LeftmotorSpeed)
            if self.goal_position['range'] > 1.23:
                self.robot_state = "SEARCH_FOR_PS"
                self.found_ps = False
        else: 
            self.robot_state = "ROTATE_TO_EXIT"
    
    def exit_ps(self, rowMarkerRangeBearing):
        if rowMarkerRangeBearing:
            self.goal_position['range'] = rowMarkerRangeBearing[1]
            self.goal_position['bearing'] = rowMarkerRangeBearing[2]
            print(self.goal_position)
            self.RightmotorSpeed, self.LeftmotorSpeed = navigation.calculate_goal_velocities(self.goal_position, [])
            self.move(1, self.LeftmotorSpeed, self.RightmotorSpeed)
            if 0.62 - self.goal_position['range'] < 0.01:
                self.robot_state = 'INIT'
        else:
            self.move(1, MIN_SPEED, MIN_SPEED)
            # self.robot_state = 'INIT'




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
            self.search_for_item(dataRB[3], dataRB[2])
            request = ITEMS | SHELVES
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
            self.move_to_exit(dataRB[1], dataRB[2])
            request = ROW_MARKERS | SHELVES
        elif self.robot_state == 'MOVE_TO_PS_MARKER':
            self.move_to_ps_marker(dataRB[1], dataRB[4])
            request = ROW_MARKERS | OBSTACLES
        elif self.robot_state == 'EXIT_PS':
            self.exit_ps(dataRB[1])
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
            self.LeftmotorSpeed = speed - 10
            self.RightmotorSpeed = speed - 25
        elif direction == RIGHT:
            self.L_dir = '0'
            self.R_dir = '1'
            self.LeftmotorSpeed = speed - 25
            self.RightmotorSpeed = speed - 10
        
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
        # print("RESET GRIPPER")
        # self.i2c.grip(0)

        return

    def __del__(self):
        self.stop()
        print("RESET GRIPPER")
        self.i2c.grip(0)
        time.sleep(0.01)
        self.i2c.led(1,0)
        time.sleep(0.01)
        self.i2c.led(2,0)
        time.sleep(0.01)
        self.i2c.led(3,0),
