import cv2
import numpy as np

# Function to preprocess the image: resize and apply Gaussian blur
def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    # Resize the image
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    
    # Apply Gaussian Blur to smooth the image and reduce noise
    blurred_image = cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)
    
    return blurred_image

# Function to apply color thresholding
def color_threshold(image, lower_hsv, upper_hsv):
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Apply color thresholding
    mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
    
    return mask

# Function to apply erosion followed by dilation on a thresholded image
def apply_morphological_filters(mask):
    # Define a kernel (structuring element)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    # Apply erosion
    eroded_image = cv2.erode(mask, kernel, iterations=1)

    # Apply dilation on the eroded image
    dilated_image = cv2.dilate(eroded_image, kernel, iterations=1)

    return eroded_image, dilated_image

# Function to analyze blobs/contours
def analyze_contours(image, mask):
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw contours on the original image
    contour_image = cv2.drawContours(image.copy(), contours, -1, (0, 255, 0), 2)
    
    # Analyze each contour
    for contour in contours:
        # Calculate area and perimeter
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Get the bounding box coordinates
        x, y, w, h = cv2.boundingRect(contour)
        
        # Draw the bounding box
        cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Display contour properties on the image
        cv2.putText(contour_image, f"Area: {int(area)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(contour_image, f"Perimeter: {int(perimeter)}", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return contour_image

# Predefined color ranges for different categories
color_ranges = {
    'Shelf': (np.array([75, 0, 15]), np.array([130, 255, 230])),
    'Obstacle': (np.array([34, 98, 28]), np.array([75, 255, 225])),
    'Item': (np.array([0, 150, 27]), np.array([14, 255, 255])),
    'Marker': (np.array([0, 80, 20]), np.array([40, 150, 80]))
}

# Function to display images in sequence
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
    image = cv2.imread('captured_image_9.png')
    
    # Preprocess the image with resizing and Gaussian blur
    scale = 0.5  # Adjust this scale factor as needed
    blurred_image = preprocess_image(image, scale)
    
    # Apply color thresholding for each predefined mask
    masks = {}
    for category, (lower_hsv, upper_hsv) in color_ranges.items():
        masks[category] = color_threshold(blurred_image, lower_hsv, upper_hsv)
    
    # Apply morphological filters (erosion followed by dilation) and analyze contours on each mask
    processed_masks = {}
    for category, mask in masks.items():
        eroded_image, dilated_image = apply_morphological_filters(mask)
        contour_image = analyze_contours(blurred_image, dilated_image)
        processed_masks[category] = (mask, eroded_image, dilated_image, contour_image)
    
    # Create a sequence of images to display with descriptive titles
    image_sequence = [blurred_image]
    titles = ['Blurred and Resized Image']
    
    for category, (mask, eroded_image, dilated_image, contour_image) in processed_masks.items():
        image_sequence.extend([mask, eroded_image, dilated_image, contour_image])
        titles.extend([
            f'{category} Thresholded Image',
            f'{category} Eroded Image',
            f'{category} Dilated Image After Erosion',
            f'{category} Contour Analysis'
        ])
    
    # Display the images in a sequence with navigation controls
    display_image_sequence(image_sequence, titles)

if __name__ == "__main__":
    main()
