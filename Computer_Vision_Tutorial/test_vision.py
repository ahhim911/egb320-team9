import unittest
import numpy as np
import cv2
from vision import find_contours, calculate_distance

class TestCameraProcessing(unittest.TestCase):

    def test_find_contours(self):
        # Create a test image with a simple rectangle (white on black background)
        test_image = np.zeros((100, 100), dtype="uint8")
        cv2.rectangle(test_image, (25, 25), (75, 75), 255, -1)
        
        # Call find_contours with the test image
        contours = find_contours(test_image, min_area=100)
        
        # Assert that one contour was found and it is of expected size
        self.assertEqual(len(contours), 1)
        self.assertGreater(cv2.contourArea(contours[0]), 100)

    def test_calculate_distance(self):
        # Test with known values
        real_world_width = 0.05  # 5 cm
        focal_length = 1542  # Focal length in pixels
        
        # Pixel width of the object in the image
        pixel_width = 100
        
        # Calculate the expected distance
        expected_distance = (real_world_width * focal_length) / pixel_width
        
        # Call calculate_distance
        distance = calculate_distance(pixel_width, real_world_width, focal_length)
        
        # Assert the calculated distance is as expected
        self.assertEqual(distance, expected_distance)

if __name__ == "__main__":
    unittest.main()
