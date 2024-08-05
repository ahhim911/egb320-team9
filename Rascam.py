from picamera2 import Picamera2, Preview
from time import sleep
from libcamera import Transform

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL, transform=Transform(hflip=True))
picam2.start()
picam2.capture_file("/home/team9/Desktop/image2.jpg")
sleep(5)
picam2.close()