import numpy as np

# region ValidationTests


def test1(img, x: int):             # correct method
    return np.zeros((3, 3)).astype(np.uint8)


def test2(img, x1: int, x2: int):
    return np.zeros((3, 3)).astype(np.uint8)


def test3(img):             # incorrect return type
    return None


def test4(img):   # internal error
    raise ValueError


def test5(img, a, b, c, d, e, f, g, h):
    return np.zeros((3, 3)).astype(np.uint8)



