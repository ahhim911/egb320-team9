from machine import I2C, Pin

# Configure I2C0 on GPIO 0 (SDA) and GPIO 1 (SCL)
i2c_slave = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
led = Pin(25, Pin.OUT)
# Set the slave address (example: 0x08)
slave_address = 0x08

# Function to simulate a slave receiving data
def i2c_slave_callback(i2c, addr, data):
    print(f"Received from address {hex(addr)}: {data}")
    return b"OK"  # Send back an acknowledgment or any other response

# Infinite loop to keep the Pico active
while True:
    try:
        devices = i2c_slave.scan()
        if slave_address in devices:
            data = i2c_slave.readfrom(slave_address, 10)
            print(f"Received data: {data}")
        else:
            print("No device found")


    except OSError as e:
        print(f"Error: {e}")

