import smbus
import time

# Constants
I2C_ADDRESS = 0x08  # I2C address of the slave device

# Create an I2C bus object
bus = smbus.SMBus(0)  # 1 indicates /dev/i2c-1, typically used on Raspberry Pi

# Initialize command array with default values
cmd = [''] * 11  # Adjust the size based on your command structure

def lift(level):
    """Set the lift level in the command array."""
    global cmd
    if level == 1:
        cmd[10] = '1'
    elif level == 2:
        cmd[10] = '2'
    elif level == 3:
        cmd[10] = '3'
    else:
        print("Invalid lift level")
        return

def grip(state):
    """Set the gripper state in the command array."""
    global cmd
    if state == 'open':
        cmd[9] = 'O'
    elif state == 'close':
        cmd[9] = 'C'
    else:
        print("Invalid gripper state")
        return
    
def release_item():
    """Set command to release the item by moving the lift to level 1 and opening the gripper."""
    global cmd
    cmd[10] = '1'
    cmd[9] = 'O'

def main():
    # Example usage
    grip('open')
    time.sleep(5)  # Wait for 5 seconds
    lift(1)
    time.sleep(5)  # Wait for 5 seconds
    lift(2)
    time.sleep(5)  # Wait for 5 seconds
    lift(3)
    time.sleep(5)  # Wait for 5 seconds
    release_item()

if __name__ == "__main__":
    main() 