import smbus
import time

# Define the I2C bus (1 is for Pi 3B+ and later models)
bus = smbus.SMBus(0)

# I2C address of the Pico
PICO_I2C_ADDRESS = 0x08  # Change if needed

def send_velocity(forward, rotational):
    # Convert the velocities to a byte array
    forward_byte = int(forward).to_bytes(1, 'little', signed=True)
    rotational_byte = int(rotational).to_bytes(1, 'little', signed=True)
    
    # Send both velocities as a two-byte message
    bus.write_i2c_block_data(PICO_I2C_ADDRESS, 0x00, [forward_byte[0], rotational_byte[0]])

while True:
    try:
        # Get user input for forward and rotational velocity
        forward_velocity = int(input("Enter forward velocity (-100 to 100): "))
        rotational_velocity = int(input("Enter rotational velocity (-100 to 100): "))
        
        # Send velocity data to Pico
        send_velocity(forward_velocity, rotational_velocity)
        
        time.sleep(0.1)  # Short delay between transmissions
    
    except KeyboardInterrupt:
        print("Exiting...")
        break