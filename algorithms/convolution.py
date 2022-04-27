import numpy as np
import cv2
from skimage import color


def my_convolution(img, kernel):
    kernel_shape = kernel.shape
    if len(kernel_shape) != 2 or kernel_shape[0] != kernel_shape[1]:
        raise ValueError("Kernel is not a square matrix.")

    shape = img.shape
    if len(shape) == 3:
        return np.dstack([my_convolution(img[:, :, z], kernel) for z in range(3)])

    result = img.copy()

    size = kernel_shape[0]
    if size % 2 == 0:
        raise ValueError("Invalid kernel, size should be an odd number.")

    Y, X = shape[0], shape[1]
    offset = int(size / 2)

    for j in range(offset, Y-offset):
        for i in range(offset, X-offset):
            start = i - offset
            end = i + offset
            context = np.array([img[index, start:end + 1] for index in range(j - offset, j + offset + 1)])
            result[j][i] = np.sum(context * kernel)

    return result


if __name__ == '__main__':
    image = cv2.imread('../input_images/lena_color_blurred.jpg', cv2.IMREAD_COLOR)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

    result = my_convolution(image, kernel)
    result = cv2.filter2D(image, -1, kernel)
    cv2.imshow('original', image)
    cv2.imshow('my convolution', result)
    cv2.waitKey(0)
