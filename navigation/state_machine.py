import numpy as np
import pandas as pd



class StateMachine:
    def __init__(self):
        self.goal_bay_position = [0.875, 0.625, 0.375, 0.125] # bay positions in the row
        self.found_shelf = False
        self.found_row = False
        self.at_ps = False
        self.action = {}
        self.final_df = {}
        self.goal_position = {}
        self.current_item = 0
        self.draw = False

        # Read the object order file
        with open("Order_2.csv", mode="r", encoding='utf-8-sig') as csv_file:
            # Load the CSV into a DataFrame, automatically using the first row as column names
            df = pd.read_csv(csv_file)

        # Group by 'Height' and find the minimum 'Shelf' for each height
        min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

        # Sort by 'Shelf' in descending order
        global final_df
        sorted_min_shelf  = min_shelf_by_height.sort_values(by='Shelf', ascending=False)
        remaining_rows = df.drop(min_shelf_by_height.index)
        sorted_remaining_rows = remaining_rows.sort_values(by='Shelf', ascending=False)
        final_df = pd.concat([sorted_min_shelf, sorted_remaining_rows])

        final_df['Row'] = final_df['Shelf'] // 2
        # Redefine the index
        final_df = final_df.reset_index(drop=True)

        # Display the result
        print("Optimised pickup order:")
        print(final_df)

        self.robot_state = 'INIT'

    def init_state(self):        
        # Set initial parameters and switch to the next state
        self.robot_state = 'SEARCH_FOR_SHELF'
        self.target_shelf = self.final_df['Shelf'][self.current_item]
        self.target_row = self.final_df['Row'][self.current_item]
        self.target_bay = 3  # Example fixed value; change as needed
        self.target_height = self.final_df['Height'][self.current_item]
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = 0

    def search_for_shelf(self, rowMarkerRangeBearing, shelfRangeBearing):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None
        
        if self.target_shelf % 2 == 1:  # Odd
            subtarget_shelf = self.target_shelf - 1
            if shelfRangeBearing[subtarget_shelf] is not None:
                self.found_shelf = True
        else:  # Even
            subtarget_shelf = self.target_shelf + 1
            if shelfRangeBearing[self.target_shelf] is not None:
                self.found_shelf = True

        # Rotate on the spot
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1 if not self.at_ps else 0.1
        print(self.robot_state, "looking for: ", subtarget_shelf, "Found: ", shelfRangeBearing[subtarget_shelf])

        if self.found_row:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'MOVE_TO_ROW'
        elif self.found_shelf:
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0
            self.robot_state = 'MOVE_TO_SHELF'

    def move_to_shelf(self, shelfRangeBearing, obstaclesRB):
        self.found_shelf = False
        
        if shelfRangeBearing.get(self.target_shelf):
            self.found_shelf = True
            self.goal_position['range'] = shelfRangeBearing[self.target_shelf][0]
            self.goal_position['bearing'] = shelfRangeBearing[self.target_shelf][1]
            print(self.robot_state, "Going to: ", self.target_shelf, self.goal_position)

            # Add other shelves to obstacles
            obs = obstaclesRB
            np.append(obs, shelfRangeBearing.get(not self.target_shelf))

            # Calculate goal velocities
            self.action = self.navigation.calculate_goal_velocities(self.goal_position, obs)

        if not self.found_shelf:
            self.robot_state = 'SEARCH_FOR_SHELF'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

        if self.goal_position['range'] - 0.15 < 0.01:
            self.robot_state = 'SEARCH_FOR_ROW'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

    def search_for_row(self, rowMarkerRangeBearing):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        # Rotate on the spot
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1

        if self.found_row:
            self.robot_state = 'MOVE_TO_ROW'

    def move_to_row(self, rowMarkerRangeBearing, obstaclesRB):
        self.found_row = rowMarkerRangeBearing[self.target_row] is not None

        if self.found_row:
            self.goal_position['range'] = rowMarkerRangeBearing[self.target_row][0]
            self.goal_position['bearing'] = rowMarkerRangeBearing[self.target_row][1]
            print(self.goal_position)

            # Add shelves to obstacles
            obs = obstaclesRB
            np.append(obs, shelfRangeBearing[self.target_shelf])

            # Calculate goal velocities
            self.action = self.navigation.calculate_goal_velocities(self.goal_position, obs)

        if self.goal_position['range'] - goal_bay_position[self.target_bay] < 0.01:
            self.robot_state = 'SEARCH_FOR_ITEM'
            self.action['forward_vel'] = 0
            self.action['rotational_vel'] = 0

    def search_for_item(self, itemsRB):
        print(f"Searching for item in bay {self.target_bay} at shelf {self.target_shelf}")
        self.action['forward_vel'] = 0
        self.action['rotational_vel'] = -0.1 if self.target_shelf % 2 == 1 else 0.1

        for itemClass in itemsRB:
            if itemClass is not None:
                for itemRB in itemClass:
                    itemRange = itemRB[0]
                    itemBearing = itemRB[1]
                    if abs(itemBearing) < 0.05 and itemRange < 0.20:
                        self.robot_state = 'COLLECT_ITEM'
                        self.action['forward_vel'] = 0
                        self.action['rotational_vel'] = 0
                        break

    def collect_item(self):
        print("Collecting item")
        self.bot_sim.CollectItem(self.target_height)
        self.robot_state = 'ROTATE_TO_EXIT'

    # Add more methods for other states...

    def run_state_machine(self, itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing):
        if self.robot_state == 'INIT':
            self.init_state()
        elif self.robot_state == 'SEARCH_FOR_SHELF':
            self.search_for_shelf(rowMarkerRangeBearing, shelfRangeBearing)
        elif self.robot_state == 'MOVE_TO_SHELF':
            self.move_to_shelf(shelfRangeBearing, obstaclesRB)
        elif self.robot_state == 'SEARCH_FOR_ROW':
            self.search_for_row(rowMarkerRangeBearing)
        elif self.robot_state == 'MOVE_TO_ROW':
            self.move_to_row(rowMarkerRangeBearing, obstaclesRB)
        elif self.robot_state == 'SEARCH_FOR_ITEM':
            self.search_for_item(itemsRB)
        elif self.robot_state == 'COLLECT_ITEM':
            self.collect_item()
        # Add other state transitions...

        # Set the robot's action in the simulator
        self.bot_sim.SetTargetVelocities(self.action['forward_vel'], self.action['rotational_vel'])