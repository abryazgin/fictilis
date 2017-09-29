class BaseLet:
    """
    Абстракция Ввода/Вывода
    """
    def __init__(self, action, parameter):
        self.action = action
        self.parameter = parameter
        self.code = parameter.name

    def __repr__(self):
        return '{}(action={}, parameter={})'.format(
            self.__class__.__name__, self.action.code, self.parameter)

    def validate(self, data):
        return self.parameter.validate(data)

    def get_type(self):
        return self.parameter.type


class InLet(BaseLet):
    """
    Ввод
    """
    pass


class OutLet(BaseLet):
    """
    Вывод
    """
    pass
