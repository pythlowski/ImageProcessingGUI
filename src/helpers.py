from enum import Enum
import traceback


class ParamType(Enum):
    INT = 0
    FLOAT = 1
    BOOL = 2
    NPARRAY = 3

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class ErrorType(Enum):
    PARSING = 0
    VALIDATION = 1

    def __str__(self):
        return {
            ErrorType.PARSING: 'Parsing',
            ErrorType.VALIDATION: 'Validation'
        }.get(self)


def get_traceback_data(e: Exception, ignore_file: str):
    data = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    return ''.join((filter(lambda elem: ignore_file not in elem, data)))


def format_errors(title, errors):
    errors_grouped = []
    for data in errors:
        errors_grouped.append('ALGORITHM: ' + data['detail'] + '\n' + '\n'.join(['- ' + error for error in data['errors']]))

    return title + '\n\n' + '\n\n'.join(errors_grouped)
