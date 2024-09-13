from machine import Pin
import time

build_in_led = Pin(25, Pin.OUT)
G_led = Pin(4, Pin.OUT)
Y_led = Pin(5, Pin.OUT)
R_led = Pin(6, Pin.OUT)
SW_1 = Pin(28, Pin.IN, Pin.PULL_DOWN) # SW1 - Pin 28 - Pressed = 1, Not Pressed = 0
SW_2 = Pin(27, Pin.IN, Pin.PULL_DOWN)

# Blinking LED
while True:
    R_led.value(0) 
    build_in_led.value(1)
    time.sleep(1)
    build_in_led.value(0) 
    G_led.value(1)
    time.sleep(1)
    G_led.value(0) 
    Y_led.value(1) 
    time.sleep(1)
    Y_led.value(0) 
    R_led.value(1) 
    time.sleep(1)

# Blinking LED with SW
print('Blinking LED Example')
# while True:
#     if SW_1.value() == 1:
#         build_in_led.value(1)
#     else:
#         build_in_led.value(0)
#     if SW_2.value() == 1:
#         G_led.value(1)
#     else:
#         G_led.value(0)


