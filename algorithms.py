import numpy as np
import cv2
import time


def process_image(image):
    time.sleep(2)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)


