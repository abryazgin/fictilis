from .errors import AlreadyExistsError, NotExistsError, InvalidParams, InvalidDeclaration
from .action import Action
from .types import ContextType


class Algorithm(Action):
    """
    Алгоритм - последовательность Действий и набор связей между ними
    """
    def __init__(self, code, in_params, out_params):
        super(Algorithm, self).__init__(code=code, in_params=in_params, out_params=out_params)
        self.steps = None
        self.binds = None
        AlgorithmPool.register(code=code, algorithm=self)

    def set_params(self, steps, binds):
        self.steps = steps
        self.binds = binds

    def validate_graph(self):
        """
        Валидация графа Алгоритма
        Проверяет, что у всех зарегистрированнх Шагов привязаны/"указаны" входные параметры

        :raises: InvalidDeclaration
        """
        for step in self.steps:
            for stepinlet in step.get_inlets().values():
                if stepinlet not in self.binds and stepinlet.inlet.get_type() != ContextType:
                    print(stepinlet.inlet.get_type())
                    print(stepinlet.inlet.get_type() != ContextType)
                    raise InvalidDeclaration(
                        'In algorithm `{}` for step `{}` not registered inlet `{}`'.format(
                            self.code, step, stepinlet.inlet.code))

    def __iter__(self):
        for step in self.steps:
            yield step

    def __str__(self):
        return 'Algorithm: {}\n  steps:\n    {}\n  binds:\n    {}'.format(
            self.code,
            '\n    '.join(str(s) for s in self.steps),
            '\n    '.join(str(fromlet) + ' ---> ' + str(tolet) for tolet, fromlet in self.binds.items()))


class Step:
    """
    Шаг Алгоритма - действие на определенном "шаге" алгоритма

    По сути своей совокупность Действия + Алгоритма + Порядкового номера
    """
    def __init__(self, action, algorithm, number):
        self.action = action
        self.algorithm = algorithm
        self.number = number
        self.step_inlets = {
            code: StepInlet(step=self, inlet=inlet) for code, inlet in self.action.get_inlets().items()}
        self.step_outlets = {
            code: StepOutlet(step=self, outlet=outlet) for code, outlet in self.action.get_outlets().items()}

    def get_inlet(self, code=None, index=None):
        return self._get_let(code, index, 'in')

    def get_outlet(self, code=None, index=None):
        return self._get_let(code, index, 'out')

    def _get_let(self, code, index, t):
        assert code or index is not None
        if index is not None:
            try:
                code = self.action.get_outlets_keys()[index] if t == 'out' else self.action.get_inlets_keys()[index]
            except IndexError:
                raise InvalidParams('Step <{}> does not have {}let with index `{}`'.format(
                    repr(self), t, index))
        try:
            return self.step_outlets[code] if t == 'out' else self.step_inlets[code]
        except KeyError:
            raise InvalidParams('Step <{}> does not have {}let with code `{}`'.format(
                repr(self), t, code))

    def get_inlets(self):
        return self.step_inlets

    def get_outlets(self):
        return self.step_outlets
        
    def __iter__(self):
        for code in self.action.get_outlets_keys():
            yield self.get_outlet(code)

    def __str__(self):
        return '{} step of {}: {}'.format(self.number, self.algorithm.code, self.action.code)

    def __repr__(self):
        return 'Step(action={}, algorithm={}, number={})'.format(
            repr(self.action), repr(self.algorithm), repr(self.number))

    def __getattr__(self, key):
        return self.get_outlet(key)


class StepInlet:
    """
    Ввод для конкретного Шага Алгоритма

    По сути своей совокупность Шага
    """
    def __init__(self, step, inlet):
        self.step = step
        self.inlet = inlet

    def __str__(self):
        return '{} {}'.format(self.step, self.inlet)

    def __repr__(self):
        return 'StepInlet(step=<{}>, inlet=<{}>)'.format(
            repr(self.step), repr(self.inlet))


class StepOutlet:
    """
    Вывод для конкретного Шага Алгоритма
    """
    def __init__(self, step, outlet):
        self.step = step
        self.outlet = outlet

    def __str__(self):
        return '{} {}'.format(self.step, self.outlet)

    def __repr__(self):
        return 'StepOutlet(step=<{}>, outlet=<{}>)'.format(
            repr(self.step), repr(self.outlet))


class AlgorithmPool:
    """
    Пул Алгоритмов

    В этом пуле хранится список задекларированных Алгоритмов
    """
    _pool = dict()

    @staticmethod
    def register(code, algorithm):
        if code in AlgorithmPool._pool:
            raise AlreadyExistsError('Algorithm with code {code} already exists'.format(code=code))
        AlgorithmPool._pool[code] = algorithm

    @staticmethod
    def get(code):
        if code not in AlgorithmPool._pool:
            raise NotExistsError('Algorithm with code {code} does not exists'.format(code=code))
        return AlgorithmPool._pool[code]

    @staticmethod
    def _reset():
        AlgorithmPool._pool = dict()
