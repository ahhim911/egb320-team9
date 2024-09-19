import smbus
import time
from pynput import keyboard

# Constants
I2C_ADDRESS = 0x08  # I2C address of the slave device

# Create an I2C bus object
bus = smbus.SMBus(0)

# Function to convert a string into a list of ASCII values
def string_to_ascii_array(input_string):
    ascii_values = []
    for char in input_string:
        ascii_values.append(ord(char))
    return ascii_values


# Function to send command over I2C
def send_i2c_command(cmd):
    command = string_to_ascii_array(cmd)
    try:
        print(f"Sending command: {command} for key '{cmd}'")
        bus.write_i2c_block_data(I2C_ADDRESS, 0, command)
    except IOError as e:
        print(f"Error communicating with I2C device: {e}")


# Handle key presses
def on_press(key):
    try:
        if key.char in ['w', 'a', 's', 'd', 'x']:  # Send specific keys
            send_i2c_command(key.char)
    except AttributeError:
        pass


# Handle key release (optional, can be used to stop robot when key is released)
def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False


# Start listening to keyboard inputs
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()