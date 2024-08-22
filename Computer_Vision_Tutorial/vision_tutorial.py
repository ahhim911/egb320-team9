import cv2
import picamera2
import numpy as np
import imutils

# Initialize the camera with custom settings
def initialize_camera(frame_height=320*2, frame_width=240*2, format='XRGB8888'):
    picam2 = picamera2.Picamera2()
    config = picam2.create_video_configuration(main={"format": format, "size": (frame_width, frame_height)})
    picam2.configure(config)
    picam2.set_controls({"ColourGains": (1.4, 1.5)}) # Test different colour gains, might be too yellow, auto?
    picam2.start()
    return picam2

# Initialize the camera
picam2 = initialize_camera()

# Define default HSV ranges for blue, green, and orange colors
blue_lower = np.array([80, 100, 100])
blue_upper = np.array([130, 255, 255])

green_lower = np.array([35, 100, 100])
green_upper = np.array([79, 255, 255])

orange_lower = np.array([10, 100, 100])
orange_upper = np.array([25, 255, 255])

# Define the real-world width of the object (in meters) and the camera's focal length (in pixels)
real_world_width = 0.05  # Example: 5 cm object width in the real world
focal_length = 1542  # Example: focal length in pixels

# Define the distance threshold for the alert (e.g., 10 cm)
distance_threshold = 0.1  # in meters

# Initialize a dictionary to store the positions of objects and assign unique IDs
object_id_counter = 1
objects = {}
previous_frame_objects = {}

# Create windows for the masks and contour visualization
cv2.namedWindow('Blue Mask')
cv2.namedWindow('Green Mask')
cv2.namedWindow('Orange Mask')
cv2.namedWindow('Contour Frame')
cv2.namedWindow('Bounding Box and Distance')

# Create trackbars for adjusting the Hue values
def nothing(x):
    pass

cv2.createTrackbar('Blue HMin', 'Blue Mask', 80, 179, nothing)
cv2.createTrackbar('Blue HMax', 'Blue Mask', 130, 179, nothing)

cv2.createTrackbar('Green HMin', 'Green Mask', 35, 179, nothing)
cv2.createTrackbar('Green HMax', 'Green Mask', 79, 179, nothing)

cv2.createTrackbar('Orange HMin', 'Orange Mask', 10, 179, nothing)
cv2.createTrackbar('Orange HMax', 'Orange Mask', 25, 179, nothing)

def find_contours(filtered_image, min_area=500):
    contours = cv2.findContours(filtered_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    return filtered_contours

def calculate_distance(pixel_width, real_world_width, focal_length):
    return (real_world_width * focal_length) / pixel_width

def assign_object_id(centroid, objects, object_id_counter):
    min_distance = float("inf")
    assigned_id = None

    for obj_id, data in objects.items():
        dist = np.linalg.norm(np.array(data['centroid']) - np.array(centroid))
        if dist < min_distance:
            min_distance = dist
            assigned_id = obj_id

    # If the object is close to a known object, reuse the ID
    if min_distance < 50:  # Adjust the threshold as needed
        objects[assigned_id]['centroid'] = centroid
        return assigned_id, objects, object_id_counter
    else:
        # Assign a new ID
        objects[object_id_counter] = {'centroid': centroid}
        object_id_counter += 1
        return object_id_counter - 1, objects, object_id_counter

try:
    while True:
        # Capture an image
        frame = picam2.capture_array()

        # Pre-processing: Resize, rotate, flip, and convert to HSV
        frame = cv2.resize(frame, (320, 240))
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame = cv2.flip(frame, 1)  # Flip the image horizontally

        # Apply Gaussian Blur to reduce noise and smooth the image
        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)

        # Get current positions of the trackbars for Hue values
        blue_h_min = cv2.getTrackbarPos('Blue HMin', 'Blue Mask')
        blue_h_max = cv2.getTrackbarPos('Blue HMax', 'Blue Mask')
        green_h_min = cv2.getTrackbarPos('Green HMin', 'Green Mask')
        green_h_max = cv2.getTrackbarPos('Green HMax', 'Green Mask')
        orange_h_min = cv2.getTrackbarPos('Orange HMin', 'Orange Mask')
        orange_h_max = cv2.getTrackbarPos('Orange HMax', 'Orange Mask')

        # Update the HSV ranges for each color based on trackbar positions
        blue_lower = np.array([blue_h_min, 100, 100])
        blue_upper = np.array([blue_h_max, 255, 255])
        green_lower = np.array([green_h_min, 100, 100])
        green_upper = np.array([green_h_max, 255, 255])
        orange_lower = np.array([orange_h_min, 100, 100])
        orange_upper = np.array([orange_h_max, 255, 255])

        # Create masks for blue, green, and orange colors
        blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper)
        green_mask = cv2.inRange(hsv_frame, green_lower, green_upper)
        orange_mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)

        # Find contours for each mask, filtering out small contours
        blue_contours = find_contours(blue_mask, min_area=500)
        green_contours = find_contours(green_mask, min_area=500)
        orange_contours = find_contours(orange_mask, min_area=500)

        # Track object IDs in the current frame
        current_frame_objects = {}

        # Draw contours on the original frame for each color
        contour_frame = frame.copy()
        cv2.drawContours(contour_frame, blue_contours, -1, (255, 0, 0), 2)   # Blue contours
        cv2.drawContours(contour_frame, green_contours, -1, (0, 255, 0), 2)  # Green contours
        cv2.drawContours(contour_frame, orange_contours, -1, (0, 165, 255), 2)  # Orange contours

        # Create a new frame to draw bounding boxes, display distances, and color labels
        bbox_frame = frame.copy()
        
        # Process blue contours
        for contour in blue_contours:
            x, y, w, h = cv2.boundingRect(contour)
            distance = calculate_distance(w, real_world_width, focal_length)
            color_label = "Blue"

            # Check if the object is too close
            if distance < distance_threshold:
                print(f"Alert: {color_label} object is too close!")

            # Calculate the centroid
            centroid = (x + w // 2, y + h // 2)
            object_id, objects, object_id_counter = assign_object_id(centroid, objects, object_id_counter)

            # Record the object ID and color for the current frame
            current_frame_objects[object_id] = {'centroid': centroid, 'color': color_label}

            # Draw the bounding box, display the distance and color label
            cv2.rectangle(bbox_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(bbox_frame, f"ID: {object_id} {color_label} Dist: {distance:.2f}m", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Process green contours
        for contour in green_contours:
            x, y, w, h = cv2.boundingRect(contour)
            distance = calculate_distance(w, real_world_width, focal_length)
            color_label = "Green"

            # Check if the object is too close
            if distance < distance_threshold:
                print(f"Alert: {color_label} object is too close!")

            # Calculate the centroid
            centroid = (x + w // 2, y + h // 2)
            object_id, objects, object_id_counter = assign_object_id(centroid, objects, object_id_counter)

            # Record the object ID and color for the current frame
            current_frame_objects[object_id] = {'centroid': centroid, 'color': color_label}

            # Draw the bounding box, display the distance and color label
            cv2.rectangle(bbox_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(bbox_frame, f"ID: {object_id} {color_label} Dist: {distance:.2f}m", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Process orange contours
        for contour in orange_contours:
            x, y, w, h = cv2.boundingRect(contour)
            distance = calculate_distance(w, real_world_width, focal_length)
            color_label = "Orange"

            # Check if the object is too close
            if distance < distance_threshold:
                print(f"Alert: {color_label} object is too close!")

            # Calculate the centroid
            centroid = (x + w // 2, y + h // 2)
            object_id, objects, object_id_counter = assign_object_id(centroid, objects, object_id_counter)

            # Record the object ID and color for the current frame
            current_frame_objects[object_id] = {'centroid': centroid, 'color': color_label}

            # Draw the bounding box, display the distance and color label
            cv2.rectangle(bbox_frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
            cv2.putText(bbox_frame, f"ID: {object_id} {color_label} Dist: {distance:.2f}m", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        # Detect objects that have moved out of the frame
        for obj_id in list(objects.keys()):
            if obj_id not in current_frame_objects:
                print(f"Alert: Object ID {obj_id} has moved out of frame.")
                del objects[obj_id]  # Optionally remove the object from tracking

        # Update previous frame objects
        previous_frame_objects = current_frame_objects

        # Display the original frame with contours
        cv2.imshow('Contour Frame', contour_frame)

        # Display the bounding boxes, distances, and color labels in a separate window
        cv2.imshow('Bounding Box and Distance', bbox_frame)

        # Display the masks in separate windows
        cv2.imshow('Blue Mask', cv2.bitwise_and(frame, frame, mask=blue_mask))
        cv2.imshow('Green Mask', cv2.bitwise_and(frame, frame, mask=green_mask))
        cv2.imshow('Orange Mask', cv2.bitwise_and(frame, frame, mask=orange_mask))

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.close()
    cv2.destroyAllWindows()
