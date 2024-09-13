import numpy as np
import math
import matplotlib.pyplot as plt

MAX_ROBOT_VEL = 0.05
MAX_ROBOT_ROT = 0.2
GOAL_P = 0.5
ROT_BIAS = 0.5
CAMERA_FOV = 60
WORKER_WIDTH_SCALE = 0.15 #m

# def draw_field(field):


# rotate to the specified angle
# def rotate_to_angle(angle):


def calculate_goal_velocities(goal_position, obstacles, draw=False):
    # Compute bearing to goal 
    goal_rad = goal_position['bearing']
    goal_deg = int(clip_deg_fov(np.rad2deg(goal_rad) + CAMERA_FOV/2, CAMERA_FOV))

    # Compute both attractive and repulsive field maps
    nav_state = {}
    nav_state['attractive_field'] = compute_attractive_field(goal_deg)
    nav_state['repulsive_field'] = compute_repulsive_field(obstacles)

    # Compute residual map (attractive - repulsive)
    nav_state['residual_field'] = np.maximum(nav_state['attractive_field'] - nav_state['repulsive_field'], 0)

    # Find heading angle by finding the index of the max value in the residual field
    heading_angle = np.argmax(nav_state['residual_field'])

    goal_error = np.deg2rad(heading_angle) - np.deg2rad(CAMERA_FOV/2)
    
    # Calculate rotational velocity
    rotational_vel = min(MAX_ROBOT_ROT, max(-MAX_ROBOT_ROT, goal_error * GOAL_P))

    # Calculate forward velocity based on residual field at the heading angle
    forward_vel = MAX_ROBOT_VEL * (1.0 - ROT_BIAS * abs(rotational_vel) / MAX_ROBOT_ROT)

    # Create the action dictionary
    nav_state['rotational_vel'] = rotational_vel
    nav_state['forward_vel'] = forward_vel

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

    return nav_state

def clip_deg_fov(deg, fov):
     # clip the degree to the range of the camera fov
    return max(0, min(deg, fov - 1))



def compute_attractive_field(goal_deg):
    attractive_field = np.zeros(CAMERA_FOV + 1)
    attractive_field[goal_deg] = 1
    gradient = 1 / 30
    for angle in range(0, int((CAMERA_FOV/2 +1))):
        attractive_field[clip_deg_fov(goal_deg - angle, CAMERA_FOV)] = 1 - gradient * angle
        attractive_field[clip_deg_fov(goal_deg + angle, CAMERA_FOV)] = 1 - gradient * angle
    return attractive_field
	
def compute_repulsive_field(obstacles):
    repulsive_field = np.zeros(CAMERA_FOV + 1)

    if obstacles != None:
        for obs in obstacles:
            obs_range = obs[0]
            obs_bearing = obs[1]
        
            if obs_range < 0.8:
                 obs_width = WORKER_WIDTH_SCALE

                 obs_deg = int(np.rad2deg(obs_bearing) + CAMERA_FOV/2)

                 obs_width_rad = 2*math.atan(obs_width / obs_range)
                 obs_width_deg = int(np.rad2deg(obs_width_rad))

                 obs_effect = max(0, 1- min(1, obs_range - WORKER_WIDTH_SCALE * 2))

                 repulsive_field[obs_deg] = obs_effect

                 for angle in range(1, obs_width_deg + 1):
                    repulsive_field[clip_deg_fov(obs_deg - angle, CAMERA_FOV)] = max(repulsive_field[clip_deg_fov(obs_deg - angle, CAMERA_FOV)], obs_effect * (1 - angle/obs_width_deg))
                    repulsive_field[clip_deg_fov(obs_deg + angle, CAMERA_FOV)] = max(repulsive_field[clip_deg_fov(obs_deg + angle, CAMERA_FOV)], obs_effect * (1 - angle/obs_width_deg))

    return repulsive_field