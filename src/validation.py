import numpy as np
import math
import importlib
import yaml
from src.helpers import ParamType, ErrorType, get_traceback_data


class Validation:
    def __init__(self):
        self.image_to_validate = np.ones((100, 100)).astype(np.uint8) * 128
        self.TYPES = {
            ParamType.INT: {
                'type': int,
                'default': 1
            },
            ParamType.FLOAT: {
                'type': float,
                'default': 1.23
            },
            ParamType.BOOL: {
                'type': bool,
                'default': True
            },
            ParamType.NPARRAY: {
                'type': np.ndarray,
                'default': np.zeros((3, 3))
            }
        }

    def get_algorithms(self, config_file_name):
        algorithms, parsing_errors = self.__parse_algorithms_from_config(config_file_name)

        if len(parsing_errors) > 0:
            return algorithms, ErrorType.PARSING, parsing_errors

        return self.__validate_algorithms(algorithms)

    def validate_image(self, img: np.ndarray):

        if not isinstance(img, np.ndarray):
            return f'Object is {type(img).__name__}. Expected numpy.array.'

        shape = img.shape

        expected_types_string = 'Expected one of: uint8, uint16., float32, float64'

        if len(shape) == 2:
            pixel = img[0][0]

            if self.__validate_pixel_type(pixel):
                return None
            return f'Image pixel type is {type(pixel).__name__}. {expected_types_string}.'

        elif len(shape) == 3 and shape[2] == 3:
            pixel = img[0][0][0]

            if self.__validate_pixel_type(pixel):
                return None
            return f'Image pixel type is {type(pixel).__name__}. {expected_types_string}.'
        else:
            return f'Array has invalid shape {shape}. Expected (m, n) or (m, n, 3).'

    def __validate_pixel_type(self, pixel):
        return isinstance(pixel, np.uint8) or isinstance(pixel, np.uint16) \
               or isinstance(pixel, np.float32) or isinstance(pixel, np.float64)


    def __parse_algorithms_from_config(self, config_file_name):
        errors = []

        try:
            with open(config_file_name, mode="r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                could_not_find_config_key = 'Could not find config key'
                output_algs = []

                if config.get('algorithms', -1) == -1:
                    errors.append({
                        'detail': 'Config file key error:',
                        'errors': [f"{could_not_find_config_key} 'algorithms'."]
                    })
                    return [], errors

                if not isinstance(config.get('algorithms', None), list):
                    errors.append({
                        'detail': 'Config file algorithms error:',
                        'errors': ["Configure key 'algorithms' is not a list."]
                    })
                    return [], errors

                for i, a in enumerate(config['algorithms']):
                    alg_errors = []
                    output_alg = {
                        'name': f'Algorithm #{i + 1}'
                    }
                    if a.get('name', None) is None:
                        alg_errors.append(f"{could_not_find_config_key} 'name'.")
                    else:
                        output_alg['name'] = str(a['name'])

                    if a.get('module', None) is None:
                        alg_errors.append(f"{could_not_find_config_key} 'module'.")
                    else:
                        output_alg['module'] = str(a['module'])

                    if a.get('method', None) is None:
                        alg_errors.append(f"{could_not_find_config_key} 'method'.")
                    else:
                        output_alg['method'] = str(a['method'])

                    if a.get('params', None) is None:
                        output_alg['params'] = []
                    elif not isinstance(a['params'], list):
                        alg_errors.append(f"Configure key 'params' is not a list.")
                    else:
                        output_params = []
                        for j, param in enumerate(a['params']):
                            output_param = {}
                            if isinstance(param, dict):
                                if param.get('name', None) is not None:
                                    output_param['name'] = str(param['name'])
                                else:
                                    output_param['name'] = f'Parameter #{j + 1}'

                                if param.get('type', None) is not None:
                                    if isinstance(param['type'], int):  # param given as int
                                        if ParamType.has_value(param['type']):
                                            output_param['type'] = ParamType(param['type'])
                                        else:
                                            alg_errors.append(
                                                f"Parameter #{j + 1} - Type is not a valid type from integer value.")
                                    else:  # param given as string
                                        output_param_type = {
                                            'int': ParamType.INT,
                                            'float': ParamType.FLOAT,
                                            'bool': ParamType.BOOL,
                                            'array': ParamType.NPARRAY
                                        }.get(str(param['type']), None)
                                        if output_param_type is not None:
                                            output_param['type'] = output_param_type
                                        else:
                                            alg_errors.append(
                                                f"Parameter #{j + 1} - Type is not a valid type from string value.")
                                else:
                                    alg_errors.append(f"Parameter #{j + 1} - {could_not_find_config_key} 'type'.")

                                if param.get('description', None) is not None:
                                    output_param['description'] = str(param['description'])

                                if param.get('default', None) is not None:
                                    if output_param['type'] == ParamType.NPARRAY:
                                        output_param['default'] = f"np.asarray({param['default']})"
                                    else:
                                        output_param['default'] = str(param['default'])

                                output_params.append(output_param)
                            else:
                                alg_errors.append(f"Parameter #{j + 1} is not an object.")


                        output_alg['params'] = output_params

                    if len(alg_errors) == 0:
                        output_algs.append(output_alg)
                    else:
                        errors.append({
                            'detail': output_alg['name'],
                            'errors': alg_errors
                        })

                return output_algs, errors
        except Exception as e:
            errors.append({
                'detail': 'Config file error:',
                'errors': [str(e)]
            })
            return [], errors

    def __validate_algorithms(self, algorithms):
        errors = []
        output_algorithms = []
        for alg in algorithms:
            alg_errors = []
            default_values_validation_erorrs = self.__validate_default_values(alg)
            if default_values_validation_erorrs:
                alg_errors += default_values_validation_erorrs
            else:
                module, method, validate_error = self.__validate_algorithm(alg)
                if validate_error:
                    alg_errors.append(validate_error)

            if len(alg_errors) == 0:
                output_algorithms.append({
                    'name': alg['name'],
                    # 'module': module,
                    'method': method,
                    'params': alg['params']
                })
            else:
                errors.append({
                    'detail': alg['name'],
                    'errors': alg_errors
                })

        return output_algorithms, ErrorType.VALIDATION if errors else None, errors

    def __execute_algorithm(self, module_name: str, method: str, params):
        try:
            module = importlib.import_module(module_name)
            algorithm = getattr(module, method)
            result = algorithm(self.image_to_validate, *params)
            return result, module, algorithm, None
        except ModuleNotFoundError as e:
            return None, None, None, str(e) + '.'   # no module found
        except AttributeError as e:
            return None, None, None, str(e) + '.'   # no method found in given module
        except Exception as e:
            return None, None, None, f'Error while testing algorithm execution with default values:\n' \
                                     f'{get_traceback_data(e, ignore_file=__file__)}'

    def __validate_algorithm(self, algorithm_object):
        alg_params_values = [eval(param['default']) if param.get('default', None)
                             else self.TYPES[param['type']]['default']
                             for param in algorithm_object['params']]

        result, module, method, error = self.__execute_algorithm(algorithm_object['module'], algorithm_object['method'], alg_params_values)
        if error:
            return None, None, error[:-1] + '.'

        error = self.validate_image(result)
        if error is not None:
            return None, None, error
        return module, method, None

    def __validate_default_values(self, algorithm_object):
        errors = []
        for i, param in enumerate(algorithm_object['params']):
            if param.get('default', None) is not None:
                param_details = f"Parameter #{i + 1} ({param['name']})"
                try:
                    value = eval(param['default'])
                    expected_type = self.TYPES[param['type']]['type']

                    if not isinstance(value, expected_type):
                        errors.append(f"{param_details} - Default value type error: expected '{expected_type.__name__}', got '{type(value).__name__}'.")
                except Exception as e:
                    errors.append(f"{param_details} - Default value error ('{param['default']}'): {e}.")
        return errors
