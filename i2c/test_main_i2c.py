from main_i2c import I2C
import time



i2c = I2C(addr=0x08, bus=0)


def test_drive():
    print("Testing Drive Command...")
    i2c.drive(forwards=0.01, rotational=0.01)  # Drive forwards at 0.5 m/s and rotate at 0.2 rad/s
    time.sleep(1)
    i2c.drive(forwards=-0.01, rotational=-0.01)  # Drive backwards at 0.3 m/s and rotate at -0.1 rad/s
    time.sleep(1)
    i2c.drive(forwards=0, rotational=0)

def test_lift():
    print("Testing Lift Command...")
    i2c.lift(1)  # Set lift to level 1
    time.sleep(4)
    i2c.lift(2)  # Set lift to level 2
    time.sleep(3)
    i2c.lift(3)  # Set lift to level 3
    time.sleep(6)
    i2c.lift(1)  # Set lift to level 1

def test_grip():
    print("Testing Grip Command...")
    i2c.grip(0)  # Open the gripper
    time.sleep(1)
    i2c.grip(1)  # Close the gripper
    time.sleep(1)

def test_led():
    print("Testing LED Command...")
    i2c.led(1, 'on')  # Turn on LED 1
    time.sleep(1)
    i2c.led(1, 'off')  # Turn off LED 1
    time.sleep(1)
    i2c.led(2, 'on')  # Turn on LED 2
    time.sleep(1)
    i2c.led(2, 'off')  # Turn off LED 2
    time.sleep(1)
    i2c.led(3, 'on')  # Turn on LED 3
    time.sleep(1)
    i2c.led(3, 'off')  # Turn off LED 3
    time.sleep(1)

if __name__ == "__main__":
    # Run tests for all functions
    try:
        # test_drive()
        #test_lift()
        test_grip()
        test_led()
        print("All tests completed successfully.")
    except Exception as e:
        print(f"An error occurred during testing: {e}")
























