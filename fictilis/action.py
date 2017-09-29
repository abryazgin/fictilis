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
        return self._inlets_indexes

    def get_outlets_keys(self):
        return self._outlets_indexes

    def get_inlet(self, code=None, index=None):
        return self._get_let(code, index, 'in')

    def get_outlet(self, code=None, index=None):
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
        return self.inlets

    def get_outlets(self):
        return self.outlets

    def validate_inputs(self, kwinputs):
        kwinputs = kwinputs or dict()
        assert isinstance(kwinputs, dict)
        kwinputs = self._validate_values_quantity(kwvalues=kwinputs, t='in')
        return self._validate_values_quality(kwvalues=kwinputs, t='in')

    def validate_outputs(self, kwoutputs):
        kwoutputs = kwoutputs or dict()
        assert isinstance(kwoutputs, dict)
        kwoutputs = self._validate_values_quantity(kwvalues=kwoutputs, t='out')
        return self._validate_values_quality(kwvalues=kwoutputs, t='out')

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


class ActionStratagy:
    """
    Стратегия действия

    По сути своей является реализацией Действия с помощью определенной Стратегии
    """
    def __init__(self, action, strategy, function):
        self.action = action
        self.strategy = strategy
        self.function = function
        ActionStrategyPool.register(action.code, strategy, self)

    @staticmethod
    def execute(code, strategy, kwparams=None):
        return ActionStrategyPool.get(code=code, strategy=strategy).evaluate(kwparams)

    def evaluate(self, kwparams=None):
        try:
            return self.function(**kwparams)
        except TypeError:
            raise InvalidDeclaration(
                'Seems like `function` for {action} have invalid declaration'.format(action=self.action))


class ActionPool:
    _pool = dict()

    @staticmethod
    def register(code, action):
        if code in ActionPool._pool:
            raise AlreadyExistsError('Action with code {} already exists'.format(code))
        ActionPool._pool[code] = action

    @staticmethod
    def get(code):
        if code not in ActionPool._pool:
            raise NotExistsError('Action with code {code} does not exists'.format(code=code))
        return ActionPool._pool[code]


class ActionStrategyPool:
    _pool = defaultdict(dict)

    @staticmethod
    def register(code, strategy, actionstrategy):
        if code in ActionStrategyPool._pool and strategy in ActionStrategyPool._pool[code]:
            raise AlreadyExistsError(
                'Action {} with stratagy {} already exists'.format(code, strategy))
        ActionStrategyPool._pool[code][strategy] = actionstrategy

    @staticmethod
    def get(code, strategy):
        if code not in ActionStrategyPool._pool:
            raise NotExistsError('Action with code {code} does not exists'.format(code=code))
        if strategy not in ActionStrategyPool._pool[code]:
            raise NotExistsError(
                'Action with code {code} and stategy {strategy} does not exists'.format(
                    code=code, strategy=strategy))
        return ActionStrategyPool._pool[code][strategy]

    @staticmethod
    def list(code):
        if code not in ActionStrategyPool._pool:
            raise NotExistsError('Action with code {code} does not exists'.format(code=code))
        return ActionStrategyPool._pool[code]
