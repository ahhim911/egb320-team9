#!/usr/bin/python


# import the packing bot module - this will include math, time, numpy (as np) and CoppeliaSim python modules
from warehousebot_lib import *
import time
import numpy as np
import pandas as pd

#import any other required python modules
import path_planning as navigation
import csv

# SET SCENE PARAMETERS
sceneParameters = SceneParameters()

# Starting contents of the bays [shelf,X,Y]. Set to -1 to leave empty.
sceneParameters.bayContents = np.random.random_integers(0,5,sceneParameters.bayContents.shape)
sceneParameters.bayContents[0,3,1] = warehouseObjects.bowl
sceneParameters.bayContents[1,1,2] = warehouseObjects.mug
sceneParameters.bayContents[2,3,1] = warehouseObjects.bottle
sceneParameters.bayContents[3,1,2] = warehouseObjects.soccer
sceneParameters.bayContents[4,2,0] = warehouseObjects.rubiks
sceneParameters.bayContents[5,0,1] = warehouseObjects.cereal


sceneParameters.obstacle0_StartingPosition = [-0.5,0]  # starting position of obstacle 0 [x, y] (in metres), -1 if want to use current CoppeliaSim position, or none if not wanted in the scene
# sceneParameters.obstacle0_StartingPosition = None  # starting position of obstacle 0 [x, y] (in metres), -1 if want to use current CoppeliaSim position, or none if not wanted in the scene
sceneParameters.obstacle1_StartingPosition = [0.5,-0.5]   # starting position of obstacle 1 [x, y] (in metres), -1 if want to use current CoppeliaSim position, or none if not wanted in the scene
sceneParameters.obstacle2_StartingPosition = -1   # starting position of obstacle 2 [x, y] (in metres), -1 if want to use current CoppeliaSim position, or none if not wanted in the scene


# SET ROBOT PARAMETERS
robotParameters = RobotParameters()

# Drive Parameters
robotParameters.driveType = 'differential'	# specify if using differential or omni drive system
robotParameters.minimumLinearSpeed = 0.0  	# minimum speed at which your robot can move forward in m/s
robotParameters.maximumLinearSpeed = 0.25 	# maximum speed at which your robot can move forward in m/s
robotParameters.driveSystemQuality = 1		# specifies how good your drive system is from 0 to 1 (with 1 being able to drive in a perfectly straight line when told to do so)

# Camera Parameters
robotParameters.cameraOrientation = 'landscape' # specifies the orientation of the camera, either landscape or portrait
robotParameters.cameraDistanceFromRobotCenter = 0.1 # distance between the camera and the center of the robot in the direction of the collector in metres
robotParameters.cameraHeightFromFloor = 0.15 # height of the camera relative to the floor in metres
robotParameters.cameraTilt = 0.0 # tilt of the camera in radians

# Vision Processing Parameters
robotParameters.maxItemDetectionDistance = 1 # the maximum distance away that you can detect the items in metres
robotParameters.maxPackingBayDetectionDistance = 2.5 # the maximum distance away that you can detect the packing bay in metres
robotParameters.maxObstacleDetectionDistance = 1.5 # the maximum distance away that you can detect the obstacles in metres
robotParameters.maxRowMarkerDetectionDistance = 2.5 # the maximum distance away that you can detect the row markers in metres

# Collector Parameters
robotParameters.collectorQuality = 1 # specifies how good your item collector is from 0 to 1.0 (with 1.0 being awesome and 0 being non-existent)
robotParameters.maxCollectDistance = 0.15 #specificies the operating distance of the automatic collector function. Item needs to be less than this distance to the collector

robotParameters.sync = False # This parameter forces the simulation into syncronous mode when True; requiring you to call stepSim() to manually step the simulator in your loop


# MAIN SCRIPT
if __name__ == '__main__':

	# Wrap everything in a try except case that catches KeyboardInterrupts. 
	# In the exception catch code attempt to Stop the CoppeliaSim so don't have to Stop it manually when pressing CTRL+C
	try:

		# Create CoppeliaSim PackerBot object - this will attempt to open a connection to CoppeliaSim. Make sure CoppeliaSim is running.
		warehouseBotSim = COPPELIA_WarehouseRobot('127.0.0.1', robotParameters, sceneParameters)
		# warehouseBotSim.SetScene()
		warehouseBotSim.StartSimulator()

		goal_bay_position = [0.875, 0.625, 0.375, 0.1] # bay positions in the row
		found_shelf = False
		found_row = False
		at_ps = False
		action = {}
		goal_position = {}
		
		current_item = 0
		draw = False

		# Read the object order file
		with open("Order_2.csv", mode="r", encoding='utf-8-sig') as csv_file:
			# Load the CSV into a DataFrame, automatically using the first row as column names
			df = pd.read_csv(csv_file)

		# Group by 'Height' and find the minimum 'Shelf' for each height
		min_shelf_by_height = df.loc[df.groupby('Height')['Shelf'].idxmin()]

		# Sort by 'Shelf' in descending order
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
		
		
		
		robot_state = 'INIT'
		

		#We recommended changing this to a controlled rate loop (fixed frequency) to get more reliable control behaviour
		while True:
			
			# Get Detected Objects
			itemsRB, packingBayRB, obstaclesRB, rowMarkerRangeBearing, shelfRangeBearing = warehouseBotSim.GetDetectedObjects(
				[
					warehouseObjects.items,
     				warehouseObjects.shelves,
					warehouseObjects.row_markers,
					warehouseObjects.obstacles,
					warehouseObjects.packingBay,
				]
			)
		# ---------------------------------------------
		# STATE MACHINE
		# ---------------------------------------------

		# ---------INIT----------
			if robot_state == 'INIT':
				# INIT
				

				robot_state = 'SEARCH_FOR_SHELF'
				target_shelf = final_df['Shelf'][current_item]
				target_row = final_df['Row'][current_item]
				# target_bay = final_df['Bay'][current_item]
				target_bay = 3
				target_height = final_df['Height'][current_item]

				action['forward_vel'] = 0
				action['rotational_vel'] = 0
				
		# ---------SEARCH_FOR_SHELF----------	
			elif robot_state == 'SEARCH_FOR_SHELF':
				if rowMarkerRangeBearing[target_row] != None:
					found_row = True

				if target_shelf % 2 == 1: # odd
					subtarget_shelf = target_shelf - 1
					if shelfRangeBearing[subtarget_shelf] != None:
						found_shelf = True
				else: # even
					subtarget_shelf = target_shelf + 1
					if shelfRangeBearing[target_shelf] != None:
						found_shelf = True
					
				# rotate on the spot
				action['forward_vel'] = 0
				if not at_ps:
					action['rotational_vel'] = -0.1
				else:
					action['rotational_vel'] = 0.1
				print(robot_state, "looking for: ", subtarget_shelf, "Found: ", shelfRangeBearing[subtarget_shelf])
				
				if found_row:
					action['forward_vel'] = 0
					action['rotational_vel'] = 0
					robot_state = 'MOVE_TO_ROW'
				if found_shelf:
					action['forward_vel'] = 0
					action['rotational_vel'] = 0
					robot_state = 'MOVE_TO_SHELF'	

		# ---------MOVE_TO_SHELF----------
			elif robot_state == 'MOVE_TO_SHELF':
				found_shelf = False
				
				if rowMarkerRangeBearing[target_row] != None:
					found_row = True
				if found_row:
					action['forward_vel'] = 0
					action['rotational_vel'] = 0
					robot_state = 'MOVE_TO_ROW'

				if shelfRangeBearing[subtarget_shelf] != None:
					found_shelf = True
					goal_position['range'] = shelfRangeBearing[subtarget_shelf][0]
					goal_position['bearing'] = shelfRangeBearing[subtarget_shelf][1]
					print(robot_state, "Going to: ", subtarget_shelf, goal_position)
				if found_shelf == True:
					# add the other shelf to the obstacles
					obs = obstaclesRB
					np.append(obs, shelfRangeBearing[not subtarget_shelf])
					# print(obs)

					action = navigation.calculate_goal_velocities(goal_position, obs, draw)
					print(action['forward_vel'], action['rotational_vel'])
				else:
					robot_state = 'SEARCH_FOR_SHELF'
					action['forward_vel'] = 0
					action['rotational_vel'] = 0

				if goal_position['range'] - 0.15 < 0.01:
					robot_state = 'SEARCH_FOR_ROW'
					action['forward_vel'] = 0
					action['rotational_vel'] = 0

		# ---------SEARCH_FOR_ROW----------
			elif robot_state == 'SEARCH_FOR_ROW':
				if rowMarkerRangeBearing[target_row] != None:
					found_row = True
				# rotate on the spot
				action['forward_vel'] = 0
				action['rotational_vel'] = -0.1

				if found_row:
					robot_state = 'MOVE_TO_ROW'

		# ---------MOVE_TO_ROW----------
			elif robot_state == 'MOVE_TO_ROW':
				found_row = False
						
				if rowMarkerRangeBearing[target_row] != None:
					found_row = True
					goal_position['range'] = rowMarkerRangeBearing[target_row][0]
					goal_position['bearing'] = rowMarkerRangeBearing[target_row][1]
					print(goal_position)
				if found_row == True:
					# add the the shelf to the obstacles
					obs = obstaclesRB
					np.append(obs, shelfRangeBearing[target_shelf])
					action = navigation.calculate_goal_velocities(goal_position, obs, draw)
					print(action['forward_vel'], action['rotational_vel'])
				else:
					robot_state = 'SEARCH_FOR_ROW'
					action['forward_vel'] = 0
					action['rotational_vel'] = 0

				if goal_position['range'] - goal_bay_position[target_bay] < 0.01:
					robot_state = 'SEARCH_FOR_ITEM'
					action['forward_vel'] = 0
					action['rotational_vel'] = 0
			
		# ---------SEARCH_FOR_ITEM----------
			elif robot_state == 'SEARCH_FOR_ITEM':
				print("Searching for item in bay ", target_bay, "at shelf ", target_shelf)
				# rotate on the spot
				action['forward_vel'] = 0
				if target_shelf % 2 == 1: # odd - right
					print("Shelf on the Right, turning right")
					action['rotational_vel'] = -0.1
				else: # even - left
					print("Shelf on the Left, turning left")
					action['rotational_vel'] = 0.1
				print(itemsRB)
				#Check to see if an item is within the camera's FOV
				for itemClass in itemsRB:
					if itemClass != None:
						# action['rotational_vel'] = action['rotational_vel'] / 2
						# loop through each item detected using Pythonian way
						for itemRB in itemClass:
							itemRange = itemRB[0]
							itemBearing = itemRB[1]
							if np.abs(itemBearing) < 0.05 and itemRange < 0.20:
								# robot_state = 'COLLECT_ITEM' # for milestone 2 -----------------
								action['forward_vel'] = 0
								action['rotational_vel'] = 0
								break
				
					
		# ---------COLLECT_ITEM----------
			elif robot_state == 'COLLECT_ITEM':
				print("Collecting item")
				# For Simulation
				warehouseBotSim.CollectItem(target_height)

				# For Real Robot
				# ENTER THE CODE HERE
				count = 0
				robot_state = 'ROTATE_TO_EXIT'

		# ---------ROTATE_TO_EXIT----------
			elif robot_state == 'ROTATE_TO_EXIT':
				# rotate on the spot
				count += 1
				action['forward_vel'] = 0
				if target_shelf % 2 == 1: # odd - right
					print("Exit on the Right, turning right, count: ", count)
					action['rotational_vel'] = -0.1
				else: # even - left
					print("Exit on the Left, turning left, count: ", count)
					action['rotational_vel'] = 0.1
				if count > 90 or (shelfRangeBearing[target_shelf] and shelfRangeBearing[subtarget_shelf]):
					robot_state = 'MOVE_TO_EXIT'
					count = 0

		# ---------MOVE_TO_EXIT----------
			elif robot_state == 'MOVE_TO_EXIT':
				print("Moving to exit")
				if (shelfRangeBearing[target_shelf] and shelfRangeBearing[subtarget_shelf]) != None:
					# Calculate bearing perpendicular to the wall
					goal_position['range'] = np.arccos(0.5 / wallPoints[1][0])
					# goal_position['bearing'] = 0
					goal_position['bearing'] = (shelfRangeBearing[target_shelf][1] + shelfRangeBearing[subtarget_shelf][1]) / 2
					print(goal_position)
					
					# add the other shelf to the obstacles
					obs = obstaclesRB
					np.append(obs, shelfRangeBearing[target_shelf])
					np.append(obs, shelfRangeBearing[subtarget_shelf])

					action = navigation.calculate_goal_velocities(goal_position, obs, draw)
					print(action['forward_vel'], action['rotational_vel'])

					if goal_position['range'] - 0.8 < 0.01:
						robot_state = 'SEARCH_FOR_PS'


		# ---------SEARCH_FOR_PS----------
			elif robot_state == 'SEARCH_FOR_PS':
				print("Searching for Packing Station")
				# rotate on the spot
				action['forward_vel'] = 0
				action['rotational_vel'] = -0.1 # rotate right
				if packingBayRB != None:
					robot_state = 'MOVE_TO_PS'

		# ---------MOVE_TO_PS----------
			elif robot_state == 'MOVE_TO_PS':
				print("Moving to Packing Station")
				if packingBayRB == None:
					robot_state = 'SEARCH_FOR_PS'
				else:
					# Calculate bearing to the packing station
					goal_position['range'] = packingBayRB[0]
					goal_position['bearing'] = packingBayRB[1]
					print(goal_position)

					obs = obstaclesRB
					np.append(obs, shelfRangeBearing)
					# np.append(obs, shelfRangeBearing[subtarget_shelf])

					action = navigation.calculate_goal_velocities(goal_position, obs, draw)
					print(action['forward_vel'], action['rotational_vel'])

					if goal_position['range'] - 0.4 < 0.01:
						robot_state = 'DROP_ITEM'

		# ---------DROP_ITEM----------
			elif robot_state == 'DROP_ITEM':
				print("Dropping item")
				# For Simulation
				warehouseBotSim.Dropitem()
				current_item += 1
				count = 0
				at_ps = True
				robot_state = 'EXIT_PS'


		# ---------EXIT_PS----------
			elif robot_state == 'EXIT_PS':
				count += 1
				print("Exiting Packing Station, count: ", count)
				# rotate on the spot
				action['forward_vel'] = -0.05
				action['rotational_vel'] = 0
				if count > 20:
					robot_state = 'SEARCH_FOR_SHELF'
					count = 0
					at_ps = True







			else:
				pass


			# ---------------------------------------------
			# END STATE MACHINE
			# ---------------------------------------------

			# Set the robot's action
			warehouseBotSim.SetTargetVelocities(action['forward_vel'],action['rotational_vel'])






			# warehouseBotSim.Dropitem()

			# Check to see if any obstacles are within the camera's FOV
			if obstaclesRB != None:
				# loop through each obstacle detected using Pythonian way
				for obstacle in obstaclesRB:
					obstacleRange = obstacle[0]
					obstacleBearing = obstacle[1]

			# Get Detected Wall Points
			wallPoints = warehouseBotSim.GetDetectedWallPoints()
			if wallPoints == None:
				print("To close to the wall")
			# else:
			# 	print("\nDetected Wall Points")
			# 	# print the range and bearing to each wall point in the list
			# 	for point in wallPoints:
			# 		print("\tWall Point (range, bearing): %0.4f, %0.4f"%(point[0], point[1]))


			# Update object Positions
			warehouseBotSim.UpdateObjectPositions()

			if robotParameters.sync:
				warehouseBotSim.stepSim()

	except KeyboardInterrupt as e:
		# attempt to stop simulator so it restarts and don't have to manually press the Stop button in CoppeliaSim 
		warehouseBotSim.StopSimulator()



