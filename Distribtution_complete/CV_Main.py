
import cv2

"Comment / Uncomment these lines depending if you are working on a pi or computer"
#import picamera
#with picamera.PiCamera() as camera:
#    camer.resolution = (640, 480)


#import all the relevant functions
from CV_Find_Object import find_object
from CV_Find_Contours import find_contours
from CV_Calculations import caculate_distance, caculate_position
from CV_Focal_Length import caculate_focal_Length
from CV_Draw_Info import draw_information 

"Below is the function that applys all the above imports to process our frame, you wont need to edit this stuff but feel free to have a look"

FOCAL_LENGTH = 320#caculate_focal_Length()


def process_frame(frame):
    #Process a given camera frame

    imageObject = find_object(frame)

    contours, width_List_px = find_contours(imageObject[0])

    item_not_found = width_List_px[0] == -1
    
    if(item_not_found):
        return frame, imageObject, [None]

    box_details = []

    for box_id in range(len(width_List_px)):

        distance = caculate_distance(FOCAL_LENGTH, width_List_px[box_id])
        
        pos_x, pos_y, height_px, width_px = caculate_position(contours[box_id])

        updated_frame = draw_information(frame, pos_x, pos_y, width_px, height_px, distance)

        box_details.append({"dist" : distance, "x" : pos_x, "y" : pos_y})

    return updated_frame, imageObject, box_details



"*** DO NOT EDIT THIS CODE ***"
"*** The below code creates the website to view the camera Feed, and is easily broken ***"

import cv2
import threading
from flask import Flask, Response, render_template

app = Flask(__name__)

cap = cv2.VideoCapture(0)
cap.set(3, 240)  # Width
cap.set(4, 240)  # Height

capture_frames = True 

#Main function to process the frames
def generate_frames(stream_index):

    while capture_frames:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            prsdFrame, imageOut, boxInfo = process_frame(frame)
            if stream_index == 0:
                _, buffer = cv2.imencode('.jpg', prsdFrame)
            else:
                _, buffer = cv2.imencode('.jpg', imageOut[stream_index - 1])

        frame_data = buffer.tobytes()
            
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')


#Localised  HTML for all video streams
@app.route('/')
def index():
    return render_template('index.html', num_streams=2)


#Each video stream is out putted to a specific page
@app.route('/video_feed/<int:stream_index>')
def video_feed(stream_index):
    return Response(generate_frames(stream_index), mimetype='multipart/x-mixed-replace; boundary=frame')


#Start the web page and the threading to improve efficency
if __name__ == '__main__':
    capture_thread = threading.Thread(target=generate_frames)
    capture_thread.start()
    app.run(debug=True)
    capture_frames = False  # Stop capturing frames when the app exits
    capture_thread.join()  # Wait for the capture thread to finish



