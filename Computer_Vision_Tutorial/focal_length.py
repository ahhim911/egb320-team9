import cv2
import numpy as np

# Known parameters
real_world_width = 0.07  # 7 cm object width in meters
distance_to_object = 1.1  # 110 cm distance to the object in meters

# Function to preprocess the image: resize, rotate, flip, and blur
def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    #blurred_image = cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)
    return resized_image

# Function to apply color thresholding
def color_threshold(image, lower_hsv, upper_hsv):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
    return mask

# Function to apply morphological operations on a thresholded image
def apply_morphological_filters(mask, kernel_size=(5, 5)):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)
    return closed_image

# Function to calculate focal length
def calculate_focal_length(object_width_in_pixels, real_world_width, distance_to_object):
    focal_length = (object_width_in_pixels * distance_to_object) / real_world_width
    return focal_length

# Load the image
frame = cv2.imread('/home/edmond/egb320-team9/Computer_Vision_Tutorial/test_image.png')

# Pre-process the image
preprocessed_image = preprocess_image(frame)

# Define the HSV range for the 'Marker' color
marker_lower = np.array([0,0,0])
marker_upper = np.array([175,100,80])
#0,0,0,175,100,80

# Apply color segmentation
marker_mask = color_threshold(preprocessed_image, marker_lower, marker_upper)

# Apply morphological filtering
#filtered_mask = apply_morphological_filters(marker_mask)

# Find contours in the mask
contours, _ = cv2.findContours(marker_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Check if any contour was found
if len(contours) == 0:
    print("Error: No marker object detected.")
    exit()

detected_markers = []

for contour in contours:
    area = cv2.contourArea(contour)
    if area < 60:
        continue
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        continue
    circularity = 4 * np.pi * (area / (perimeter ** 2)) # type: ignore
    # Classify shape
    if circularity >= 0.8:
        shape = "Circle"
    else:
        continue
    detected_markers.append({
                "contour": contour,
                "shape": shape,
            })


# Get the bounding box around the object
x, y, w, h = cv2.boundingRect(contour)

# Calculate focal length
focal_length = calculate_focal_length(w, real_world_width, distance_to_object)
print(f"Calculated Focal Length: {focal_length:.2f} pixels")

# Draw the contours on the image
cv2.drawContours(preprocessed_image, contours, -1, (0, 0, 255), 2)

# Draw the bounding box on the image
cv2.rectangle(preprocessed_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Display focal length and width information on the image
cv2.putText(preprocessed_image, f"Focal Length: {focal_length:.2f} pixels", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
cv2.putText(preprocessed_image, f"Width: {w} pixels", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

# Show the final image with contours and bounding box
cv2.imshow("Detected Marker Object", preprocessed_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
