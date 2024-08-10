from gpiozero import AngularServo
from time import sleep

servo = AngularServo(21, min_pulse_width=0.0006, max_pulse_width=0.0023)

for i in range(-90, -10, 1):
    servo.angle = i
    print(i)
    sleep(0.1)


