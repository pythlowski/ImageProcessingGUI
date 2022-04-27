import numpy as np
import cv2
from skimage import color


def my_wiener(img, kernel, K):
    if len(img.shape) == 3:
        img = color.rgb2gray(img)
    img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    kernel /= np.sum(kernel)
    dummy = np.copy(img)
    dummy = np.fft.fft2(dummy)
    kernel = np.fft.fft2(kernel, s=img.shape)
    kernel = np.conj(kernel) / (np.abs(kernel) ** 2 + K)
    dummy = dummy * kernel
    dummy = np.abs(np.fft.ifft2(dummy))
    return dummy * 255


if __name__ == '__main__':

    image = cv2.imread('../input_images/lena_blurred.jpg', cv2.IMREAD_GRAYSCALE)
    psf = np.ones((5, 5)) / 5

    result = my_wiener(image, psf, 0.05)
    cv2.imshow('original', image)
    cv2.imshow('algorithm', result)
    cv2.waitKey(0)