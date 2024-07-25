import RPi.GPIO as GPIO
import time

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin connected to the servo signal wire
servo_pin = 23

# Set up the GPIO pin as an output
GPIO.setup(servo_pin, GPIO.OUT)

# Create a PWM object with 50Hz frequency
pwm = GPIO.PWM(servo_pin, 50)

# Start PWM with 0 duty cycle (servo is not moving)
pwm.start(0)

def set_servo_speed(speed):
    # Speed is expected to be between -1 (full reverse) and 1 (full forward)
    duty_cycle = (speed + 1) * 5  # Convert speed to duty cycle (0-10)
    pwm.ChangeDutyCycle(duty_cycle)

try:
    while True:
        # Example usage:
        # Move servo forward at full speed
        set_servo_speed(1)
        time.sleep(2)

        # Stop the servo
        set_servo_speed(0)
        time.sleep(2)

        # Move servo backward at full speed
        set_servo_speed(-1)
        time.sleep(2)

        # Stop the servo
        set_servo_speed(0)
        time.sleep(2)

except KeyboardInterrupt:
    pass

# Clean up
pwm.stop()
GPIO.cleanup()
