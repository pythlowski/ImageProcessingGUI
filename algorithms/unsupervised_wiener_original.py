import numpy as np
from skimage import restoration, color
import cv2


def unsupervised_wiener_original(img, psf):
    if len(img.shape) == 3:
        img = color.rgb2gray(img)
    img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    result, _ = restoration.unsupervised_wiener(img, psf)
    return result * 255

if __name__ == '__main__':

    image = cv2.imread('../input_images/astro_blurred.png', cv2.IMREAD_GRAYSCALE)
    psf = np.ones((5, 5)) / 25

    result = unsupervised_wiener_original(image, psf)
    cv2.imshow('original', image)
    cv2.imshow('algorithm', result)
    cv2.waitKey(0)