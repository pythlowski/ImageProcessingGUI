from skimage import restoration, color
import cv2
import numpy as np


def wiener_original(img, psf, balance):
    if len(img.shape) == 3:
        img = color.rgb2gray(img)
    img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    result = restoration.wiener(img, psf, balance)
    return result * 255
    # return cv2.normalize(result, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)


if __name__ == '__main__':

    image = cv2.imread('../input_images/astro_blurred.png', cv2.IMREAD_GRAYSCALE)
    psf = np.ones((5, 5)) / 25

    result = wiener_original(image, psf, 0.01)
    cv2.imshow('original', image)
    cv2.imshow('algorithm', result)
    cv2.waitKey(0)

