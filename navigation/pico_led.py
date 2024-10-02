import smbus
import time

# Constants
I2C_ADDRESS = 0x08  # I2C address of the slave device

# Create an I2C bus object
bus = smbus.SMBus(0)  # 1 indicates /dev/i2c-1, typically used on Raspberry Pi

# Initialize command array with default values
cmd = [''] * 14  # Adjust the size based on your command structure

def led_on(led):
    """Turn on the specified LED."""
    global cmd
    if led == 1:
        cmd[11] = '1'
    elif led == 2:
        cmd[12] = '1'
    elif led == 3:
        cmd[13] = '1'
    else:
        print("Invalid led")
        return

def led_off(led):
    """Turn off the specified LED."""
    global cmd
    if led == 1:
        cmd[11] = '0'
    elif led == 2:
        cmd[12] = '0'
    elif led == 3:
        cmd[13] = '0'
    else:
        print("Invalid led")
        return
    

def main():
    # Example usage
    led_on(1)
    time.sleep(0.1)  # Wait for 0.1 seconds
    led_on(2)
    time.sleep(0.1)  # Wait for 0.1 seconds
    led_on(3)
    time.sleep(0.1)  # Wait for 0.1 seconds
    led_off(1)
    time.sleep(0.1)  # Wait for 0.1 seconds
    led_off(2)
    time.sleep(0.1)  # Wait for 0.1 seconds
    led_off(3)

if __name__ == "__main__":
    main() 