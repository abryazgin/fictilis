from . import types
from .types import ContextType


class Parameter:
    """
    Переменная

    Имеет Название и Тип
    """
    def __init__(self, name, type_=types.Any):
        self.type = type_
        self.name = name

    def __repr__(self):
        return 'Var(name={}, type={})'.format(self.name, self.type.code)

    def validate(self, value):
        """
        Отвалидировать значение парметра
        :raises ValueError, TypeError
        :param value: значение
        :return: valid data
        """
        return self.type.validate(value)


context_parameter = Parameter('context', type_=ContextType)
