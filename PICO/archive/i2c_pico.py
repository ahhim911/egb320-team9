from machine import Pin, I2C
import time

I2C_ADDRESS = 0x08
LED_PIN = 25

# Initialize LED pin
led = Pin(LED_PIN, Pin.OUT)
led.value(0)  # Start with LED off

# Initialize I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)


def receive_event():
    try:
        # Read data from I2C master
        data = i2c.readfrom(I2C_ADDRESS, 100)
        
        # Ensure at least 2 bytes are received
        if len(data) >= 2:
            # Print received command as characters for clarity
            print("Received command:", data.decode('utf-8'))
            
            # Compare received characters
            # if data[1] == ord('O') and data[2] == ord('N'):
            #     led.value(1)  # Turn on LED
            # elif data[1] == ord('O') and data[2] == ord('F'):
            #     led.value(0)  # Turn off LED
    except Exception as e:
        print("Error receiving data:", e)

# Main loop
while True:
    devices = i2c.scan()
    if devices:
        print("I2C devices found:", [hex(device) for device in devices])
        while True:
            receive_event()
            time.sleep(0.1)  # Add some delay to avoid busy-waiting
            # Check if any I2C devices are still connected
            devices = i2c.scan()
            if not devices:
                print("No I2C devices found.")
                break
    else:
        print("No I2C devices found.")
    
    time.sleep(0.1)  # Add some delay to avoid busy-waiting
