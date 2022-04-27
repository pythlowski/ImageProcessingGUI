import numpy as np
import cv2
from scipy.signal import convolve2d
from skimage import color


def conv2(x, y, mode='same'):
    return np.rot90(convolve2d(np.rot90(x, 2), np.rot90(y, 2), mode=mode), 2)


def psf2otf(psf, shape):
    if np.all(psf == 0):
        return np.zeros_like(psf)

    inshape = psf.shape

    psf = zero_pad(psf, shape, position='corner')

    for axis, axis_size in enumerate(inshape):
        psf = np.roll(psf, -int(axis_size / 2), axis=axis)

    otf = np.fft.fft2(psf)

    n_ops = np.sum(psf.size * np.log2(psf.shape))
    otf = np.real_if_close(otf, tol=n_ops)

    return otf


def zero_pad(image, shape, position='corner'):
    shape = np.asarray(shape, dtype=int)
    imshape = np.asarray(image.shape, dtype=int)

    if np.alltrue(imshape == shape):
        return image

    if np.any(shape <= 0):
        raise ValueError("ZERO_PAD: null or negative shape given")

    dshape = shape - imshape
    if np.any(dshape < 0):
        raise ValueError("ZERO_PAD: target size smaller than source one")

    pad_img = np.zeros(shape, dtype=image.dtype)

    idx, idy = np.indices(imshape)

    if position == 'center':
        if np.any(dshape % 2 != 0):
            raise ValueError("ZERO_PAD: source and target shapes "
                             "have different parity.")
        offx, offy = dshape // 2
    else:
        offx, offy = (0, 0)

    pad_img[idx + offx, idy + offy] = image

    return pad_img


def my_RL_deconvolution(img, psf, iterations):
    if len(img.shape) == 3:
        img = color.rgb2gray(img)
    img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    latent_est = img.copy()
    latent_est += 0.1
    psf_hat = np.flipud(np.fliplr(psf))  # odwrocenie macierzy pionowo i poziomo

    for i in range(iterations):
        print('iter ' + str(i+1))
        est_conv = conv2(latent_est, psf, 'same').astype(np.uint8)
        relative_blur = img / est_conv
        error_est = conv2(relative_blur, psf_hat, 'same').astype(np.uint8)
        latent_est *= error_est

    return cv2.normalize(latent_est, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)


def my_RL_deconvolution_FFT(img, psf, iterations):
    if len(img.shape) == 3:
        img = color.rgb2gray(img)
    img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

    fn = img.copy()
    otf = psf2otf(psf, img.shape)

    for i in range(iterations):
        print('iter ' + str(i+1))
        ffn = np.fft.fft2(fn)
        Hfn = otf * ffn
        iHfn = np.fft.ifft2(Hfn)
        ratio = img / iHfn
        iratio = np.fft.fft2(ratio)
        res = otf * iratio
        ires = np.fft.ifft2(res)
        fn = ires * fn

    result = np.abs(fn)
    return result * 255
    # return cv2.normalize(result, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)


if __name__ == '__main__':
    image = cv2.imread('../input_images/astro_blurred.png', cv2.IMREAD_GRAYSCALE)
    psf = np.ones((5, 5))

    result = my_RL_deconvolution_FFT(image, psf, 100)
    cv2.imshow('original', image)
    cv2.imshow('algorithm', result)
    cv2.waitKey(0)
