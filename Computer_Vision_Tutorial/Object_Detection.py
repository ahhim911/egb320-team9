import cv2
import numpy as np

# Function to preprocess the image: resize and apply Gaussian blur
def preprocess_image(image, scale=0.5, blur_ksize=(5, 5), sigmaX=2):
    resized_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    blurred_image = cv2.GaussianBlur(resized_image, blur_ksize, sigmaX)
    return blurred_image

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

# Improved contour analysis function with filtering and classification
def analyze_contours(image, mask, category, min_area=400, min_aspect_ratio=0.3, max_aspect_ratio=3.0):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image = image.copy()
    info_image = image.copy()

    detected_objects = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        
        if not (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio):
            continue

        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        # Calculate the fill ratio (occupancy ratio)
        bounding_box_area = w * h
        fill_ratio = area / bounding_box_area if bounding_box_area > 0 else 0

        cv2.rectangle(contour_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.drawContours(contour_image, [hull], 0, (0, 255, 0), 2)

        cv2.putText(contour_image, f"Area: {int(area)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(contour_image, f"Aspect Ratio: {aspect_ratio:.2f}", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        distance = None
        if category == "Marker":
            distance = estimate_distance(w)  # Only estimate distance for Markers

        tracking_id = len(detected_objects) + 1
        detected_objects.append({
            "type": category,
            "position": (x, y, w, h),
            "distance": distance,
            "confidence": solidity,
            "fill_ratio": fill_ratio,
            "tracking_id": tracking_id,
            "occluded": False
        })

        # Display object information on the info_image
        cv2.putText(info_image, f"ID: {tracking_id} Type: {category}", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(info_image, f"Pos: {x}, {y} Size: {w}x{h}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if distance is not None:
            cv2.putText(info_image, f"Dist: {distance:.2f}m Conf: {solidity:.2f}", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(info_image, f"Fill Ratio: {fill_ratio:.2f}", (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return contour_image, detected_objects, info_image

# Function to estimate distance based on object width (only for markers)
def estimate_distance(object_width, focal_length=1309.29, real_object_width=0.07):
    return (real_object_width * focal_length) / object_width

# Function to classify markers based on fill ratio and number of visible markers
def classify_markers(detected_objects):
    # Count the number of markers detected
    marker_count = sum(1 for obj in detected_objects if obj['type'] == 'Marker')
    
    for obj in detected_objects:
        if obj['type'] == 'Marker':
            fill_ratio = obj['fill_ratio']
            if 0.9 <= fill_ratio <= 1:  # Square marker for packing station
                obj['type'] = 'Packing Station Marker'
            else:
                if marker_count == 1:
                    obj['type'] = 'Row 1 Marker'
                elif marker_count == 2:
                    obj['type'] = 'Row 2 Marker'
                elif marker_count >= 3:
                    obj['type'] = 'Row 3 Marker'
    
    return detected_objects

def detect_occlusion(detected_objects):
    for obj in detected_objects:
        aspect_ratio = obj['position'][2] / obj['position'][3]  # width / height
        if obj['type'] == 'Packing Station Marker' or obj['type'].startswith('Row'):
            # Expecting a square shape, so aspect ratio should be close to 1
            if not (0.9 <= aspect_ratio <= 1.1):
                obj['occluded'] = True
            else:
                obj['occluded'] = False

        elif obj['type'] == 'Obstacle':
            # Expecting a horizontal obstacle with aspect ratio 0.3 to 0.5
            if 0.3 <= aspect_ratio <= 0.5:
                obj['occluded'] = False
            # Expecting a vertical obstacle with aspect ratio 2 to 3
            elif 2 <= aspect_ratio <= 3:
                obj['occluded'] = False
            else:
                obj['occluded'] = True
        else:
            obj['occluded'] = False  # Default to not occluded if no criteria match

    return detected_objects



# Function to generate actionable signals for navigation
def generate_navigation_signals(detected_objects):
    signals = {
        "pick_up_ready": False,
        "avoid_obstacle": False,
        "target_acquired": False
    }

    for obj in detected_objects:
        if obj['type'] == 'Item' and obj['distance'] and obj['distance'] < 0.2:
            signals['pick_up_ready'] = True
        if obj['type'] == 'Item' and obj['distance'] and obj['distance'] < 0.1:
            signals['target_acquired'] = True
        if obj['type'] == 'Obstacle' and obj['distance'] and obj['distance'] < 0.5:
            signals['avoid_obstacle'] = True
    
    return signals

# Predefined color ranges for different categories
color_ranges = {
    'Shelf': (np.array([75, 0, 15]), np.array([130, 255, 230])),
    'Obstacle': (np.array([34, 98, 28]), np.array([75, 255, 225])),
    'Item': (np.array([0, 150, 27]), np.array([14, 255, 255])),
    'Marker': (np.array([4, 68, 50]), np.array([34, 153, 92]))
}

# Function to display images in sequence
def display_image_sequence(image_sequence, titles):
    idx = 0
    while True:
        cv2.imshow(titles[idx], image_sequence[idx])
        key = cv2.waitKey(0) & 0xFF
        if key == ord('d'):
            cv2.destroyWindow(titles[idx])
            idx = (idx + 1) % len(image_sequence)
        elif key == ord('a'):
            cv2.destroyWindow(titles[idx])
            idx = (idx - 1) % len(image_sequence)
        elif key == ord('q'):
            cv2.destroyAllWindows()
            break

def main():
    image = cv2.imread('captured_image_0.png')
    scale = 0.5
    blurred_image = preprocess_image(image, scale)
    
    masks = {}
    processed_masks = {}
    detected_objects = {}
    info_images = {}

    for category, (lower_hsv, upper_hsv) in color_ranges.items():
        masks[category] = color_threshold(blurred_image, lower_hsv, upper_hsv)
        processed_mask = apply_morphological_filters(masks[category])
        contour_image, objects, info_image = analyze_contours(blurred_image, processed_mask, category)
        processed_masks[category] = (masks[category], processed_mask, contour_image)
        detected_objects[category] = objects
        info_images[category] = info_image
    
    # Flatten detected objects from all categories
    all_detected_objects = [obj for objects in detected_objects.values() for obj in objects]

    # Classify markers and check for occlusion
    all_detected_objects = classify_markers(all_detected_objects)
    all_detected_objects = detect_occlusion(all_detected_objects)

    signals = generate_navigation_signals(all_detected_objects)

    print("Detected Objects:", all_detected_objects)
    print("Navigation Signals:", signals)
    
    image_sequence = [blurred_image]
    titles = ['Blurred and Resized Image']
    
    for category, (mask, processed_mask, contour_image) in processed_masks.items():
        image_sequence.extend([mask, processed_mask, contour_image, info_images[category]])
        titles.extend([
            f'{category} Thresholded Image',
            f'{category} Morphologically Processed Image',
            f'{category} Contour Analysis',
            f'{category} Object Information'
        ])
    
    display_image_sequence(image_sequence, titles)

if __name__ == "__main__":
    main()
