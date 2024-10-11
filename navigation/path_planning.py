import numpy as np
import math
import matplotlib.pyplot as plt


MIN_ROBOT_VEL = 35 # duty cycle
MAX_ROBOT_VEL = 70 # duty cycle
GOAL_P = 0.5
ROT_BIAS = 0.5
CAMERA_FOV = 60
WORKER_WIDTH_SCALE = 0.15 #m


def calculate_goal_velocities(goal_position, obstacles, draw=True):
    # Compute bearing to goal 
    goal_deg = goal_position['bearing']
    # Compute both attractive and repulsive field maps
    nav_state = {}
    nav_state['attractive_field'] = compute_attractive_field(goal_deg)
    nav_state['repulsive_field'] = compute_repulsive_field(obstacles)

    # Compute residual map (attractive - repulsive)
    nav_state['residual_field'] = np.maximum(nav_state['attractive_field'] - nav_state['repulsive_field'], 0)

    # Find heading angle by finding the index of the max value in the residual field
    heading_angle = np.argmax(nav_state['residual_field'])

    goal_error = heading_angle #- CAMERA_FOV/2
    print("HA: ",heading_angle, "ERROR: ", goal_error)
    # --------------- PWM Signals -------------------
    """
      float position = (sensorOutput[0] * -2) + (sensorOutput[1] * -1.5) + (sensorOutput[2] * -0.9) + (sensorOutput[3] * -0.9)+ (sensorOutput[4] * 0.9) + (sensorOutput[5] * 0.9) + (sensorOutput[6] * 1.5) + (sensorOutput[7] * 2);
      //Serial.print(sensorOutput[3]);
      // Serial.println();
      int controlSignal = (position * 0.1); // Proportional gain of 0.1, adjust as needed
    
      // Adjust motor speeds based on control signal
      int leftMotorSpeed = baseSpeed + controlSignal;
      int rightMotorSpeed = baseSpeed - controlSignal;

      // Constrain speeds to allowable range
      leftMotorSpeed = constrain(leftMotorSpeed, 0, maxSpeed);
      rightMotorSpeed = constrain(rightMotorSpeed, 0, maxSpeed);

      OCR0A = leftMotorSpeed; //left motor
      OCR0B = rightMotorSpeed; //right motor
    
    """

    # Calculate the control signal
    control_signal = goal_error * 0.75 # Gain

    # Calculate the motor speeds
    left_motor_speed = MIN_ROBOT_VEL + control_signal
    right_motor_speed = MIN_ROBOT_VEL - control_signal

    # Constrain speeds to allowable range
    left_motor_speed = min(MAX_ROBOT_VEL, max(0, left_motor_speed))
    right_motor_speed = min(MAX_ROBOT_VEL, max(0, right_motor_speed))



    # ---------------------Rot and Forward Vel------------------------
    # # Calculate rotational velocity
    # rotational_vel = min(MAX_ROBOT_ROT, max(-MAX_ROBOT_ROT, goal_error * GOAL_P))

    # # Calculate forward velocity based on residual field at the heading angle
    # forward_vel = MAX_ROBOT_VEL * (1.0 - ROT_BIAS * abs(rotational_vel) / MAX_ROBOT_ROT)

    # # Create the action dictionary
    # nav_state['rotational_vel'] = rotational_vel
    # nav_state['forward_vel'] = forward_vel
    #------------------------------------------------

    # If draw is True, update the plot
    if draw:    
        plt.ion()  # Turn on interactive mode
        plt.clf()  # Clear the current figure
        
        # Flip the fields
        nav_state['attractive_field'] = np.flip(nav_state['attractive_field'])
        nav_state['repulsive_field'] = np.flip(nav_state['repulsive_field'])
        nav_state['residual_field'] = np.flip(nav_state['residual_field'])

        plt.plot(nav_state['attractive_field'], label='Attractive Field')
        plt.plot(nav_state['repulsive_field'], label='Repulsive Field')
        plt.plot(nav_state['residual_field'], label='Residual Field')
        # plt.plot(nav_state['heading'], label='Heading', marker='o', markersize=5)
        plt.legend()
        
        plt.pause(0.01)  # Pause briefly to allow the plot to update
        plt.show(block=False)  # Show the plot without blocking

    return left_motor_speed, right_motor_speed
    # return nav_state

def clip_deg_fov(deg, fov):
    # Convert degrees to NumPy array if not already
    deg = np.asarray(deg)
    # Clip the degree to the range of the camera fov
    return np.clip(deg, 0, fov - 1)

def compute_attractive_field(goal_deg):
    angles = np.arange(-CAMERA_FOV//2, CAMERA_FOV//2 + 1) # angles from -30 to 30
    field_indices = clip_deg_fov(goal_deg + angles, CAMERA_FOV) # indices from 0 to 60
    gradient = 1 / 30 # gradient of the field
    attractive_field = np.maximum(1 - gradient * np.abs(angles), 0) # attractive field
    field = np.zeros(CAMERA_FOV + 1) # field of view
    field[field_indices.astype(int)] = attractive_field
    return field
	
def compute_repulsive_field(obstacles):
    repulsive_field = np.zeros(CAMERA_FOV + 1)

    if obstacles:
        for obs in obstacles:
            obs_range, obs_bearing = obs
            if obs_range < 0.8 and obs_range > 0:
                obs_width = WORKER_WIDTH_SCALE
                
                # Calculate the width of the obstacle in degrees
                obs_width_rad = 2 * math.atan(obs_width / obs_range)
                obs_width_deg = int(np.rad2deg(obs_width_rad))
                
                # Calculate the effect of the obstacle on the repulsive field
                obs_effect = max(0, 1 - min(1, obs_range - WORKER_WIDTH_SCALE * 2))
                
                # Update the repulsive field
                repulsive_field[obs_bearing] = obs_effect

                # Update the repulsive field for the obstacle width
                angles = np.arange(-obs_width_deg, obs_width_deg + 1)
                indices = clip_deg_fov(obs_bearing + angles, CAMERA_FOV).astype(int)
                effects = obs_effect * (1 - np.abs(angles) / obs_width_deg)
                np.maximum.at(repulsive_field, indices, effects)

    return repulsive_field




# move function