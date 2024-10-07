import smbus
import time

class I2C:
    def __init__(self, addr=0x08, bus=0):
        self.addr = addr
        self.bus = smbus.SMBus(bus)

    def string_to_ascii_array(self, input_string):
        # Convert the input string to an array of ASCII values
        return [ord(char) for char in input_string]
    
    def send_command(self, cmd):
        command = self.string_to_ascii_array(cmd)
        
        # try:
            # print(f"Sending command: {command}")
            # self.bus.write_i2c_block_data(self.addr, 0, command)  # Send data to I2C device
        # except IOError as e:
            # print(f"Error communicating with I2C device: {e}")
        
        # Optional short delay
        time.sleep(0.1)  # Give some time between commands

    def drive(self, forwards:float,rotational:float): # used in the navigvation system to run at the desired 
        forwards_int = round(forwards*100)
        #currently the rotational velocity is in rads/s the line of code below converts the rotational velocity to m/s
        #after both the forwards and rotatiaoanl velocity are in the desired units of m/s it is sent to the pico for furhter calculatiosn 
        rotational_int = round(rotational*100)

        command = f"D{forwards_int} {rotational_int}"
        self.send_command(command)

    def DCWrite(self, number, direction, speed):
        # Validate inputs
        if number not in range(1, 3):  # DC motor numbers start from 1 to 2
            print(f"Invalid DC number: {number}. Please choose between 1 and 2.")
            return

        if speed < 0 or speed > 255:  # Speed range should be between 0 and 255
            print(f"Invalid speed: {speed}. Please choose between 0 and 255.")
            return

        if direction not in ["0", "1", "S"]:  # Accept "0", "1", and "S" for STOP
            print("Invalid direction. Please choose between '0', '1' or 'S' for STOP.")
            return

        if direction == "S":
            command = f"M{number} S"
            # print(f"Sending command to DC motor: {command}")
        else:
            # Prepare the command string
            command = f"M{number} {direction} {speed}"
            # print(f"Sending command to DC motor: {command}")

        self.send_command(command)
        return



    def lift(self, level):
        """Set the lift level in the command array."""
        if level not in [1, 2, 3]:
            print("Invalid lift level")
            return

        command = f"H{level}"
        self.send_command(command)

    def grip(self, state):
        """Set the gripper state in the command array."""
        if state == 'open':
            command = 'G0'
        elif state == 'close':
            command = 'G1'
        else:
            print("Invalid gripper state")
            return

        self.send_command(command)

    def led(self, number, state):
        """Set the LED state in the command array."""
        if number not in [1, 2, 3]:
            print("Invalid LED number")
            return
        if state not in ['on', 'off']:
            print("Invalid LED state")
            return
        # Example: 'L1O' turns on LED 1
        command = f"L{number}{state[0].upper()}" # 'on' -> 'O', 'off' -> 'F'
        self.send_command(command)