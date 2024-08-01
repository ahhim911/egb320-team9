import RPi.GPIO as GPIO			# Import the GPIO module
import time 				# Import the time module
GPIO.setmode(GPIO.BCM)			# Set the GPIO pin naming convention to BCM
GPIO.setup(21,GPIO.OUT)			# Set up GPIO pin 21 as an output
GPIO.output(21,GPIO.HIGH) 		# Set GPIO pin 21 to digital high (on)
time.sleep(5)				# Wait for 5 seconds
GPIO.output(21,GPIO.LOW)		# Set GPIO pin 21 to digital low (off)
GPIO.cleanup()				# Exit the GPIO session cleanly
