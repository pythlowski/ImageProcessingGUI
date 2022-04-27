from unittest import TestCase
import numpy as np
from src.validation import Validation
from src.helpers import ParamType, ErrorType, format_errors


class ImageValidationTest(TestCase):

    # region helpers
    def set_up_validation(self, image):
        v = Validation()
        return v.validate_image(image)

    def get_test_image_int(self, pixel, size):
        return np.asarray([np.asarray([np.asarray(pixel)] * size)] * size)
    # endregion

    def test_invalid_object_type(self):
        error = self.set_up_validation(None)

        self.assertNotEqual(None, error)
        self.assertTrue('Expected numpy.array.' in error)

    def test_3D_valid_uint8(self):
        img = self.get_test_image_int([255, 0, 0], 4).astype(np.uint8)
        error = self.set_up_validation(img)

        self.assertEqual(None, error)

    def test_3D_valid_uint16(self):
        img = self.get_test_image_int([255, 0, 0], 4).astype(np.uint16)
        error = self.set_up_validation(img)

        self.assertEqual(None, error)

    def test_3D_invalid_pixel_type(self):
        img = self.get_test_image_int([255, 0, 0], 4)
        error = self.set_up_validation(img)

        self.assertNotEqual(None, error)
        self.assertTrue('Image pixel type is' in error)

    def test_2D_valid_uint8(self):
        img = self.get_test_image_int(128, 4).astype(np.uint8)
        error = self.set_up_validation(img)

        self.assertEqual(None, error)

    def test_2D_valid_uint16(self):
        img = self.get_test_image_int(128, 4).astype(np.uint16)
        error = self.set_up_validation(img)

        self.assertEqual(None, error)

    def test_2D_invalid_pixel_type(self):
        img = self.get_test_image_int(128, 4)
        error = self.set_up_validation(img)

        self.assertNotEqual(None, error)
        self.assertTrue('Image pixel type is' in error)

    def test_invalid_shape(self):
        img = self.get_test_image_int([0, 0], 16).astype(np.uint8)
        error = self.set_up_validation(img)

        self.assertNotEqual(None, error)
        self.assertTrue('Array has invalid shape (16, 16, 2).' in error)

