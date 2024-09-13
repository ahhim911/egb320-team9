#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, request, jsonify
from camera_pi2 import Camera

app = Flask(__name__)

hsv_values = {
    "hMin": 0,
    "sMin": 0,
    "vMin": 0,
    "hMax": 18,
    "sMax": 255,
    "vMax": 255
}


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html', hsv_values=hsv_values)

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen(camera):
    """Video streaming generator function."""
    while True:
        # frame = camera.get_frame()
        frame = camera.get_frame(hsv_values)
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/update_hsv', methods=['POST'])
def update_hsv():
    """Update HSV values from slider input."""
    global hsv_values
    data = request.json
    hsv_values.update(data)
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
