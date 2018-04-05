from .errors import UnexpectedError
from .context import Context


class Type:
    """
    Тип

    Имеет валидатор:
        функция, которая принимает значение (value) и в кидает ValueError, TypeError в случае проблем
    """
    def __init__(self, code, validator):
        self.code = code
        self.validator = validator

    def validate(self, value):
        """
        :raises ValueError, TypeError
        :param value:
        :return: validated value
        """
        try:
            return self.validator(value)
        except (ValueError, TypeError):
            raise
        except Exception:
            raise UnexpectedError

    def __repr__(self):
        return 'Type(code={}, validator={})'.format(self.code, self.validator)


Any = Type(code='Any', validator=lambda v: v)
Numeric = Type(code='Numeric', validator=lambda v: v if isinstance(v, (int, float)) else float(v))
String = Type(code='String', validator=lambda s: s if isinstance(s, (str)) else '')


def __context_validator(v):
    if not isinstance(v, Context):
        raise TypeError
    return v


ContextType = Type(code='Context', validator=__context_validator)
