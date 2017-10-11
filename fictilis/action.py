from collections import defaultdict, OrderedDict
from .errors import AlreadyExistsError, NotExistsError, InvalidParams, InvalidType, InvalidDeclaration
from .parameter import Parameter
from .lets import InLet, OutLet


class Action:
    """
    Действие

    По сути своей абстракция Вводов + Выводов к черному ящику
    Для Действия пишутся реализации - Стратегии
    """
    def __init__(self, code, in_params=None, out_params=None):
        self.code = code
        self.inlets = dict()
        self.outlets = dict()
        self._inlets_indexes = None
        self._outlets_indexes = None
        in_params = in_params or tuple()
        out_params = out_params or tuple()
        self.register_in_params(in_params)
        self.register_out_params(out_params)
        ActionPool.register(code=code, action=self)

    def __str__(self):
        return '{cls} `{code}`({inlets}) -> {outlets}'.format(
            cls=self.__class__.__name__,
            code=self.code,
            inlets=','.join(self.inlets.keys()),
            outlets=','.join(self.outlets.keys()))

    def __repr__(self):
        return 'Action(code={code})'.format(code=self.code)

    def register_in_params(self, in_params):
        assert isinstance(in_params, (list, tuple))
        for i in in_params:
            assert isinstance(i, Parameter)
        self.inlets = {i.name: InLet(action=self, parameter=i) for i in in_params}
        self._inlets_indexes = tuple(i.name for i in in_params)

    def register_out_params(self, out_params):
        assert isinstance(out_params, (list, tuple))
        for o in out_params:
            assert isinstance(o, Parameter)
        self.outlets = {o.name: OutLet(action=self, parameter=o) for o in out_params}
        self._outlets_indexes = tuple(o.name for o in out_params)

    def get_inlets_keys(self):
        """
        Получения списка ключей (названий) Вводов
        Порядок соответствует порядку входных параметров при вызове
        :return: [<Inlet>, ...]
        """
        return self._inlets_indexes

    def get_outlets_keys(self):
        """
        Получения списка ключей (названий) Выходов
        Порядок соответствует порядку результатов при вызове
        :return: [<OutLet>, ...]
        """
        return self._outlets_indexes

    def get_inlet(self, code=None, index=None):
        """
        Получение Ввода по его коду/индексу

        :param code: код Ввода
        :param index: индекс Ввода
        :return: <InLet>
        """
        return self._get_let(code, index, 'in')

    def get_outlet(self, code=None, index=None):
        """
        Получение Выхода по его коду/индексу

        :param code: код Выхода
        :param index: индекс Выхода
        :return: <OutLet>
        """
        return self._get_let(code, index, 'out')

    def _get_let(self, code, index, t):
        assert code or index is not None
        if index is not None:
            try:
                code = self._outlets_indexes[index] if t == 'out' else self._inlets_indexes[index]
            except IndexError:
                raise InvalidParams('Action <{}> does not have {}let with index `{}`'.format(
                    repr(self), t, index))
        try:
            return self.outlets[code] if t == 'out' else self.inlets[code]
        except KeyError:
            raise InvalidParams('Action <{}> does not have {}let with code `{}`'.format(
                repr(self), t, code))

    def get_inlets(self):
        """
        Получение списка Вводов
        :return: <dict(InLet.code=InLet, ...)>
        """
        return self.inlets

    def get_outlets(self):
        """
        Получение списка Выходов
        :return: <dict(OutLet.code=OutLet, ...)>
        """
        return self.outlets

    def validate_inputs(self, kwinputs):
        """
        Валидация входных параметров

        :param kwinputs: <dict> параметры Действия
        :return: <dict> отвалидированные параметры Действия
                        (возможно видоизмененные: например, приведены к типам)
        """
        kwinputs = kwinputs or dict()
        assert isinstance(kwinputs, dict)
        kwinputs = self._validate_values_quantity(kwvalues=kwinputs, t='in')
        kwinputs = self._validate_values_quality(kwvalues=kwinputs, t='in')
        return kwinputs

    def validate_outputs(self, kwoutputs):
        """
        Валидация выходных параметров

        :param kwoutputs: <dict> результаты выполнения Действия
        :return: <dict> отвалидированные параметры Действия
                        (возможно видоизмененные: например, приведены к типам)
        """
        kwoutputs = kwoutputs or dict()
        assert isinstance(kwoutputs, dict)
        kwoutputs = self._validate_values_quantity(kwvalues=kwoutputs, t='out')
        kwoutputs = self._validate_values_quality(kwvalues=kwoutputs, t='out')
        return kwoutputs

    def _validate_values_quality(self, kwvalues, t):
        for code in kwvalues:
            inlet = self.get_inlet(code=code) if t == 'in' else self.get_outlet(code=code)
            try:
                kwvalues[code] = inlet.validate(kwvalues[code])
            except (ValueError, TypeError):
                raise InvalidType(
                    (
                        'Action `{acode}`: Incorrect type of {t}-parameter `{pcode}` (value: `{value}`). '
                        'Expected type: `{tcode}`'
                    ).format(
                        tcode=inlet.get_type().code,
                        pcode=inlet.parameter.name,
                        acode=self.code,
                        value=repr(kwvalues[code]),
                        t=t
                    ),
                )
        return kwvalues

    def _validate_values_quantity(self, kwvalues, t):
        kwkeys = set(kwvalues.keys())
        actionkeys = set(self.get_inlets_keys() if t == 'in' else self.get_outlets_keys())
        if kwkeys != actionkeys:
            unexpected = kwkeys - actionkeys
            notreceived = actionkeys - kwkeys
            if unexpected:
                raise InvalidParams(
                    'Action `{}`: Received some unexpected {}-params: {}'.format(
                        self.code, t, ','.join(unexpected)))
            if notreceived:
                raise InvalidParams(
                    'Action `{}`: Not received some {}-params: {}'.format(
                        self.code, t, ','.join(notreceived)))
        return kwvalues


class Implementation:
    """
    Стратегия действия

    По сути своей является реализацией Действия с помощью определенной Стратегии
    """
    def __init__(self, action, engine, function):
        self.action = action
        self.engine = engine
        self.function = function
        ImplementationPool.register(code=action.code, engine=engine, implementation=self)

    @staticmethod
    def execute(code, engine, kwparams=None):
        """
        Выполнение Стратегии выполнения Действия

        :param code: код Действия
        :param engine: Стратегия
        :param kwparams: Параметры выполнения
        :return: Результат выполнения Стратегии выполнения Действия
        """
        return ImplementationPool.get(code=code, engine=engine).evaluate(kwparams)

    def evaluate(self, kwparams=None):
        """
        Выполнение

        :param kwparams: Параметры выполнения
        :return: Результат выполнения Стратегии выполнения Действия
        """
        try:
            return self.function(**kwparams)
        except TypeError:
            raise InvalidDeclaration(
                'Seems like `function` for {action} have invalid declaration'.format(action=self.action))


class ActionPool:
    """
    Пул Действий

    В этом пуле хранится список задекларированных Действий
    """
    _pool = dict()

    @staticmethod
    def register(code, action):
        """
        Регистрация Действия

        :param code: код Действия
        :param action: Действие
        """
        if not isinstance(action, Action):
            raise InvalidType('Action for ActionPool must be instance of `Action` class|subclass')
        if code in ActionPool._pool:
            raise AlreadyExistsError('Action with code {} already exists'.format(code))
        ActionPool._pool[code] = action

    @staticmethod
    def get(code):
        """
        Получение Действия по коду

        :param code: код Действия
        :return: <Action>
        """
        if code not in ActionPool._pool:
            raise NotExistsError('Action with code {code} does not exists'.format(code=code))
        return ActionPool._pool[code]

    @staticmethod
    def _reset():
        ActionPool._pool = dict()


class ImplementationPool:
    """
    Пул Стратегий выполнения Действий

    В этом пуле хранится список привязанных к Действиям стратегий выполнения
    Стратегией выполнения может быть другое Действие/Алгоритм
    """
    _pool = defaultdict(dict)

    @staticmethod
    def register(code, engine, implementation):
        """
        Регистрация Стратегии выполнения Действия

        :param code: код Действия
        :param engine: Стратегия
        :param implementation: Стратегия выполнения Действия
        """
        isaction = isinstance(implementation, Action)
        isimplementation = isinstance(implementation, Implementation)
        if not (isaction or isimplementation):
            raise InvalidType(
                'Action-engine for ImplementationPool must be function or instance of `Action` class|subclass')
        if code in ImplementationPool._pool and engine in ImplementationPool._pool[code]:
            raise AlreadyExistsError(
                'Action {} with engine {} already exists'.format(code, engine))
        ImplementationPool._pool[code][engine] = implementation

    @staticmethod
    def get(code, engine):
        """
        Получение Стратегии выполнения Действия по коду Действия и Стратегии

        :param code: код Действия
        :param engine: Стратегия
        :return: <Implementation | Action>
        """
        if code not in ImplementationPool._pool:
            raise NotExistsError('Implementation for Action with code {code} does not exists'.format(code=code))
        if engine not in ImplementationPool._pool[code]:
            raise NotExistsError(
                'Action with code {code} and stategy {engine} does not exists'.format(
                    code=code, engine=engine))
        return ImplementationPool._pool[code][engine]

    @staticmethod
    def list(code):
        """
        Получение списка Стратегий выполнения Действий по коду Действия

        :param code: код Действия
        :return: [<Implementation | Action>, ...]
        """
        if code not in ImplementationPool._pool:
            raise NotExistsError('Implementation for Action with code {code} does not exists'.format(code=code))
        return ImplementationPool._pool[code]

    @staticmethod
    def _reset():
        ImplementationPool._pool = defaultdict(dict)

