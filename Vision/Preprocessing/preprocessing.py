import cv2

class Preprocessing:
    @staticmethod
    def resize(image, size=(640, 480)):
        return cv2.resize(image, size)

    @staticmethod
    def blur(image, ksize=(5, 5), sigmaX=2):
        return cv2.GaussianBlur(image, ksize, sigmaX)

    @staticmethod
    def to_hsv(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    @staticmethod
    def preprocess(image, resize_to=(640, 480), blur_ksize=(5, 5), sigmaX=2):
        resized = Preprocessing.resize(image, resize_to)
        blurred = Preprocessing.blur(resized, blur_ksize, sigmaX)
        hsv_image = Preprocessing.to_hsv(blurred)
        return hsv_image
