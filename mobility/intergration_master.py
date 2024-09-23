from smbus import SMBus
import time
from pynput import keyboard


addr = 0x08 # I2C address of the Arduino slave
bus = SMBus(0) # I2C bus (usually 1 for Raspberry Pi)


#maximum rotational velocity
def drive(forwards:float,rotational:float): # used in the navigvation system to run at the desired 
    forwards_int = forwards*100
    #currently the rotational velocity is in rads/s the line of code below converts the rotational velocity to m/s
    #after both the forwards and rotatiaoanl velocity are in the desired units of m/s it is sent to the pico for furhter calculatiosn 
    rotational_int = rotational*100

    command = [forwards, rotational]
    try:
        print("Sending command: ", command)
        bus.write_i2c_block_data(addr, 0, command)
            # Optionally add a short delay
    except OSError as e:
        print(f"error communicating with I2C device:{e}")
    time.sleep(1)