from smbus import SMBus
import time

addr = 0x08  # I2C address of the Arduino slave (check this with i2cdetect)
bus = SMBus(0)  # Correct I2C bus for Raspberry Pi (usually 1)

def string_to_ascii_array(input_string):
    # Convert the input string to an array of ASCII values
    return [ord(char) for char in input_string]

while True:
    cmd = input(">>>>   ")  # Get user input
    command = string_to_ascii_array(cmd)
    
    try:
        print(f"Sending command: {command}")
        bus.write_i2c_block_data(addr, 0, command)  # Send data to I2C device
    except IOError as e:
        print(f"Error communicating with I2C device: {e}")
    
    # Optional short delay
    time.sleep(0.1)  # Give some time between commands