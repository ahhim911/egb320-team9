import RPi.GPIO as GPIO 			# Import GPIO module
 
GPIO.setmode(GPIO.BCM)				# Set the GPIO pin naming convention
GPIO.setup(21, GPIO.OUT)			# Set our GPIO pin to output

pwm21 = GPIO.PWM(21, 0.5)			# Initiate the PWM signal in Pin 21, 0.5 Hz
pwm21.start(50)					# Start a PWM signal with duty cycle at 50%

input('Press a key to stop:')		# Kill on keypress

pwm21.stop()					# Stop the PWM signal
GPIO.cleanup()					# Exit the GPIO session cleanly
