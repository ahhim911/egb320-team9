import smbus
import time
from pynput import keyboard
from mobility.intergration_master import drive



# Constants
I2C_ADDRESS = 0x08  # I2C address of the slave device

class WASDMotion:
    def __init__(self) -> None:

        # Create an I2C bus object
        self.bus = smbus.SMBus(0)  # 1 indicates /dev/i2c-1, typically used on Raspberry Pi
        
    # Function to convert a string into a list of ASCII values
    def string_to_ascii_array(self, input_string):
        ascii_values = []
        for char in input_string:
            ascii_values.append(ord(char))
        return ascii_values


    # Function to send command over I2C
    def send_i2c_command(self, cmd):
        command = self.string_to_ascii_array(cmd)
        try:
            print(f"Sending command: {command} for key '{cmd}'")
            self.bus.write_i2c_block_data(I2C_ADDRESS, 0, command)
        except IOError as e:
            print(f"Error communicating with I2C device: {e}")


    # Handle key presses
    def on_press(self, key):
        try:
            if key.char in ['w', 'a', 's', 'd', 'x']:  # Send specific keys
                if key.char == 'w':
                    drive(0.1, 0)
                elif key.char == 'a':
                    drive(0, 0.1)
                elif key.char == 's':
                    drive(-0.1, 0)
                elif key.char == 'd':
                    drive(0, -0.1)
                elif key.char == 'x':
                    drive(0, 0)
        except AttributeError:
            pass


    # Handle key release (optional, can be used to stop robot when key is released)
    def on_release(self, key):
        if key == keyboard.Key.esc:
            # Stop listener
            return False

    def start(self):
        # Start listening to keyboard inputs
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def stop(self):
        # Stop the robot
        drive(0, 0)