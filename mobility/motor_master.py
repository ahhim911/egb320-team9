<<<<<<< HEAD
    from smbus import SMBus
    import time
    addr = 0x08 # I2C address of the Arduino slave
    bus = SMBus(0) # I2C bus (usually 1 for Raspberry Pi)

    print("Input command for forwards and rotational velocity in percetage of speed required (eg. 100 000):")

=======
from smbus import SMBus
import time
from pynput import keyboard


addr = 0x08 # I2C address of the Arduino slave
bus = SMBus(0) # I2C bus (usually 1 for Raspberry Pi)

>>>>>>> 0e3ab4bf9e7a2fa9b9345344455597813d6779be

    def string_to_ascii_array(input_string):
        # Create an empty list to hold the ASCII values
        ascii_values = []
        # Loop through each character in the input string
        for char in input_string:
            # Append the ASCII value of the character to the list
            ascii_values.append(ord(char))
        
        return ascii_values

    while True:
        cmd = input(">>>>   ")
        command = string_to_ascii_array(cmd)
        try:
                print("Sending command: ", command)
                bus.write_i2c_block_data(addr, 0, command)
        except IOError as e:
                print(f"Error communicating with I2C device: {e}")

<<<<<<< HEAD
        # Optionally add a short delay
        #time.sleep(1)
=======
    # Optionally add a short delay
    time.sleep(1)

# def move(forward_vel, rotational_vel):
#    """
#    The function is used in state_machine.py
#    Please send Commands to the PICO through i2c here
#    """

#    print(forward_vel, rotational_vel)
>>>>>>> 0e3ab4bf9e7a2fa9b9345344455597813d6779be
