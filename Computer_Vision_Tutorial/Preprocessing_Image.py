import cv2
import numpy as np

# Function to preprocess the image: resize and return the resized image
def preprocess_image(image, scale=0.5):
    # Resize the image
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    return resized_image

# Function to apply color thresholding
def color_threshold(image, lower_hsv, upper_hsv):
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Apply color thresholding
    mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
    
    return mask

# Trackbar callback function (no operation)
def nothing(x):
    pass

# Function to create trackbars for adjusting HSV values
def create_trackbars():
    cv2.namedWindow('Threshold Adjustment')
    cv2.createTrackbar('Hue Min', 'Threshold Adjustment', 0, 179, nothing)
    cv2.createTrackbar('Hue Max', 'Threshold Adjustment', 179, 179, nothing)
    cv2.createTrackbar('Sat Min', 'Threshold Adjustment', 0, 255, nothing)
    cv2.createTrackbar('Sat Max', 'Threshold Adjustment', 255, 255, nothing)
    cv2.createTrackbar('Val Min', 'Threshold Adjustment', 0, 255, nothing)
    cv2.createTrackbar('Val Max', 'Threshold Adjustment', 255, 255, nothing)

# Function to read trackbar positions
def get_trackbar_values():
    h_min = cv2.getTrackbarPos('Hue Min', 'Threshold Adjustment')
    h_max = cv2.getTrackbarPos('Hue Max', 'Threshold Adjustment')
    s_min = cv2.getTrackbarPos('Sat Min', 'Threshold Adjustment')
    s_max = cv2.getTrackbarPos('Sat Max', 'Threshold Adjustment')
    v_min = cv2.getTrackbarPos('Val Min', 'Threshold Adjustment')
    v_max = cv2.getTrackbarPos('Val Max', 'Threshold Adjustment')
    return np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])

# Function to apply morphological operations on a thresholded image
def apply_morphological_filters(mask, kernel_size=(5, 5)):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)
    return opened_image, closed_image

def display_image_sequence(image_sequence, titles):
    idx = 0
    while True:
        # Display the current image with a descriptive title
        cv2.imshow(titles[idx], image_sequence[idx])

        # Wait for user input
        key = cv2.waitKey(0) & 0xFF

        # 'd' for next image
        if key == ord('d'):
            cv2.destroyWindow(titles[idx])
            idx = (idx + 1) % len(image_sequence)

        # 'a' for previous image
        elif key == ord('a'):
            cv2.destroyWindow(titles[idx])
            idx = (idx - 1) % len(image_sequence)

        # 'q' to quit and close all images
        elif key == ord('q'):
            cv2.destroyAllWindows()
            break

def main():
    # Load the image
    image = cv2.imread('captured_image_2.png')
    
    # Preprocess the image with resizing
    scale = 0.5  # You can adjust this scale factor
    resized_image = preprocess_image(image, scale)
    
    # Create trackbars for adjusting HSV thresholds
    create_trackbars()

    while True:
        # Get the current positions of the trackbars
        lower_hsv, upper_hsv = get_trackbar_values()
        
        # Apply color thresholding using the current trackbar positions
        thresholded_image = color_threshold(resized_image, lower_hsv, upper_hsv)
        
        # Display the thresholded image
        cv2.imshow('Threshold Adjustment', thresholded_image)

        # Wait for the user to press 'd' to proceed with the morphological filters
        key = cv2.waitKey(1) & 0xFF
        if key == ord('d'):
            break

    # Apply morphological filters (erosion followed by dilation)
    opened_image, closed_image = apply_morphological_filters(thresholded_image)
    
    # Create a sequence of images to display with descriptive titles
    image_sequence = [
        cv2.resize(image, (0, 0), fx=scale, fy=scale),  # Display the resized original image
        thresholded_image,                               # Display the thresholded image
        opened_image,                                    # Display the eroded image
        closed_image                                    # Display the image after dilation (following erosion)
    ]
    
    # Corresponding titles for each image stage
    titles = [
        'Resized Original Image', 
        'Thresholded Image',
        'Eroded Image', 
        'Dilated Image After Erosion'
    ]
    
    # Display the images in a sequence with navigation controls
    display_image_sequence(image_sequence, titles)

if __name__ == "__main__":
    main()
