from unittest import TestCase
from src.validation import Validation
from src.helpers import ParamType, ErrorType, format_errors


class ConfigValidationTest(TestCase):

    def set_up_validation(self, config_file):
        v = Validation()
        algorithms, error_type, errors_obj = v.get_algorithms(config_file)
        errors = format_errors('Errors:', errors_obj)

        return algorithms, error_type, errors

    # region parsing tests
    def test_invalid_config_file(self):
        algorithms, error_type, errors = self.set_up_validation('abcdef')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue('No such file or directory' in errors)

    def test_algorithm_key_is_not_a_list(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_no_algorithms_list.yaml')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue("Configure key 'algorithms' is not a list" in errors)

    def test_no_algorithms_key_in_config(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_no_algorithms.yaml')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue("Could not find config key 'algorithms'" in errors)

    def test_no_algorithm_keys(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_no_algorithm_keys.yaml')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue("Could not find config key 'name'" in errors)
        self.assertTrue("Could not find config key 'module'" in errors)
        self.assertTrue("Could not find config key 'method'" in errors)

    def test_invalid_param_types(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_invalid_types.yaml')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue("Type is not a valid type from integer value" in errors)
        self.assertTrue("Type is not a valid type from string value" in errors)
        self.assertTrue("Could not find config key 'type'" in errors)
        self.assertTrue("is not an object" in errors)

    def test_invalid_params_object_type(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_invalid_params_type.yaml')

        self.assertEqual(0, len(algorithms))
        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertTrue("Configure key 'params' is not a list" in errors)
    # endregion

    # region validation tests
    def test_module_not_found(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_module_not_found.yaml')

        self.assertEqual(error_type, ErrorType.VALIDATION)
        self.assertEqual(0, len(algorithms))
        self.assertTrue("No module named" in errors)

    def test_method_not_found(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_method_not_found.yaml')

        self.assertEqual(error_type, ErrorType.VALIDATION)
        self.assertEqual(0, len(algorithms))
        self.assertTrue("module 'algorithms.test_algorithms' has no attribute" in errors)

    def test_valid_types(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_valid_types.yaml')

        self.assertEqual(error_type, None)
        self.assertEqual(2, len(algorithms))
        self.assertEqual(8, len(algorithms[0]['params']))
        self.assertEqual(ParamType.INT, algorithms[0]['params'][0]['type'])
        self.assertEqual(ParamType.INT, algorithms[0]['params'][1]['type'])
        self.assertEqual(ParamType.FLOAT, algorithms[0]['params'][2]['type'])
        self.assertEqual(ParamType.FLOAT, algorithms[0]['params'][3]['type'])
        self.assertEqual(ParamType.BOOL, algorithms[0]['params'][4]['type'])
        self.assertEqual(ParamType.BOOL, algorithms[0]['params'][5]['type'])
        self.assertEqual(ParamType.NPARRAY, algorithms[0]['params'][6]['type'])
        self.assertEqual(ParamType.NPARRAY, algorithms[0]['params'][7]['type'])

    def test_invalid_defaults(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_invalid_default.yaml')

        self.assertEqual(error_type, ErrorType.VALIDATION)
        self.assertEqual(0, len(algorithms))
        self.assertTrue("name 'abc' is not defined" in errors)
        self.assertTrue("Default value type error: expected 'int'" in errors)

    def test_method_evaluation_errors(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_method_evaluation_errors.yaml')

        self.assertEqual(error_type, ErrorType.VALIDATION)
        self.assertEqual(0, len(algorithms))
        self.assertTrue("test5() missing" in errors)
        self.assertTrue("test1() takes 2 positional arguments but" in errors)
    # endregion

    # region general tests
    def test_one_valid_and_one_invalid(self):
        algorithms, error_type, errors = self.set_up_validation('mock_configs/config_one_valid_and_one_invalid.yaml')

        self.assertEqual(error_type, ErrorType.PARSING)
        self.assertEqual(1, len(algorithms))
        self.assertTrue("Could not find config key 'module'" in errors)
    # endregion

