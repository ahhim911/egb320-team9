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

# Function to apply morphological operations on a thresholded image
def apply_morphological_filters(mask, kernel_size=(5, 5)):
    # Define a kernel (structuring element)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)

    # Apply opening to remove noise (erosion followed by dilation)
    opened_image = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Apply closing to close small holes inside the foreground objects
    closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)

    return closed_image

# Function to calculate HOG features manually
def calculate_hog_features(roi):
    cell_size = 8
    h_cells = roi.shape[0] // cell_size
    w_cells = roi.shape[1] // cell_size

    # Check if the ROI is large enough
    if h_cells < 2 or w_cells < 2:
        return np.array([])  # Return an empty array if ROI is too small

    # Calculate gradients along the x and y axis
    gx = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=1)
    gy = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=1)

    # Compute magnitude and direction (angle) of the gradient
    magnitude, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)

    # Quantize angles into 9 bins (0 to 180 degrees)
    bins = np.int32(9 * angle / 180)  # Angles are mapped to [0, 9]

    # Create a histogram for each cell (8x8 pixels)
    histogram = np.zeros((h_cells, w_cells, 9))

    for i in range(h_cells):
        for j in range(w_cells):
            cell_mag = magnitude[i * cell_size:(i + 1) * cell_size, j * cell_size:(j + 1) * cell_size]
            cell_bins = bins[i * cell_size:(i + 1) * cell_size, j * cell_size:(j + 1) * cell_size]
            hist, _ = np.histogram(cell_bins, bins=9, range=(0, 9), weights=cell_mag)
            histogram[i, j, :] = hist

    # Normalize the histograms over blocks (2x2 cells)
    block_size = 2
    blocks = []
    for i in range(h_cells - block_size + 1):
        for j in range(w_cells - block_size + 1):
            block = histogram[i:i + block_size, j:j + block_size, :].flatten()
            norm_block = block / np.linalg.norm(block) if np.linalg.norm(block) != 0 else block
            blocks.append(norm_block)
    
    # Flatten the blocks to create the feature vector
    if blocks:
        hog_features = np.hstack(blocks)
    else:
        hog_features = np.array([])  # Return an empty array if no blocks are available
    
    return hog_features

# Improved contour analysis function with filtering and classification
def analyze_contours(image, mask, min_area=250, min_aspect_ratio=0.2, max_aspect_ratio=5.0):
    # Find contours in the mask
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    contour_image = image.copy()
    
    for contour in contours:
        # Filter contours based on area
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        
        # Approximate the contour to reduce the number of points
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Get the bounding box and calculate aspect ratio
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        
        # Further filter contours based on aspect ratio
        if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
            continue

        # Calculate the solidity (area/convex hull area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Draw the bounding box and convex hull
        cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.drawContours(contour_image, [hull], 0, (0, 255, 0), 2)
        
        # Extract the region of interest (ROI) and compute custom HOG features
        roi = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        hog_features = calculate_hog_features(roi)
        if hog_features.size > 0:
            # Display contour properties on the image
            cv2.putText(contour_image, f"Area: {int(area)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(contour_image, f"Aspect Ratio: {aspect_ratio:.2f}", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(contour_image, f"Solidity: {solidity:.2f}", (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
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
    image = cv2.imread('captured_image_1.png')
    
    # Preprocess the image with resizing and Gaussian blur
    scale = 0.5  # Adjust this scale factor as needed
    blurred_image = preprocess_image(image, scale)
    
    # Apply color thresholding for each predefined mask
    masks = {}
    for category, (lower_hsv, upper_hsv) in color_ranges.items():
        masks[category] = color_threshold(blurred_image, lower_hsv, upper_hsv)
    
    # Apply morphological filters (opening followed by closing) and analyze contours on each mask
    processed_masks = {}
    for category, mask in masks.items():
        processed_mask = apply_morphological_filters(mask)
        contour_image = analyze_contours(blurred_image, processed_mask)
        processed_masks[category] = (mask, processed_mask, contour_image)
    
    # Create a sequence of images to display with descriptive titles
    image_sequence = [blurred_image]
    titles = ['Blurred and Resized Image']
    
    for category, (mask, processed_mask, contour_image) in processed_masks.items():
        image_sequence.extend([mask, processed_mask, contour_image])
        titles.extend([
            f'{category} Thresholded Image',
            f'{category} Morphologically Processed Image',
            f'{category} Contour Analysis with HOG'
        ])
    
    # Display the images in a sequence with navigation controls
    display_image_sequence(image_sequence, titles)

if __name__ == "__main__":
    main()
