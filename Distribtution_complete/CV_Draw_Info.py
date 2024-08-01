import cv2

"The below Code is done for you and is designed to draw the information on the page, feel free to play around with the values to your liking"

def draw_information(frame, x_pos, y_pos, width, height, distance):
    #based on the contours and color mask, add information to the orign al frame
    corner_x, corner_y = int(x_pos - width//2), int(y_pos - height//2)

    BOX_COLOR =  (0, 255, 0) #Simple RGB value (B, G, R)
    TXT_COLOR =  (0, 255, 0) #Simple RGB value (B, G, R)
    CIRCLE_RADIUS = 2 #Radius of the center dot
    WIDTH = 3 #Width of the rectangle and circle


    cv2.rectangle(frame, (corner_x, corner_y), (corner_x+width, corner_y+height), BOX_COLOR, WIDTH)
    
    cv2.circle(frame, (x_pos, y_pos), CIRCLE_RADIUS, BOX_COLOR, WIDTH)

    cv2.putText(frame, "D: "+ str(int(distance))+"cm", (corner_x+width+10, y_pos), cv2.FONT_HERSHEY_TRIPLEX, 0.5, TXT_COLOR)
    
    cv2.putText(frame, "P: ({0},{1})".format(x_pos, y_pos), (corner_x+width+10, y_pos+30), cv2.FONT_HERSHEY_TRIPLEX, 0.5, TXT_COLOR)
    
    return frame