from .algorithm import Algorithm, Step
from .action import Action
from .errors import InvalidParams, InvalidDeclaration
from .lets import BaseLet
from .algorithm import StepInlet, StepOutlet
from collections import OrderedDict


class Const:
    def __init__(self, value):
        self.value = value


class AlgorithmBuilder:
    """
    Построитель алгоритмов

    Основной метод AlgorithmBuilder.build(code, in_params, out_params, builder)

        :param code: код нового Алгоритма
        :param in_params: [<Parameter>, ...] Аргументы Алгоритма
        :param out_params: [<Parameter>, ...] Результаты Алгоритма
        :param builder: <func> функция-построитель дерева Алгоритма:
                В качестве первых двух параметров всегда принимает специальные аргументы register и bind,
                использующиеся для регистрации Шагов(register) и описания поток данных(bind), пример:

                ```
                def build_square(bind, register, a):
                    multi = register(MultiA)
                    bind(fromlet=a, tolet=multi.get_inlet('a'))
                    bind(fromlet=a, tolet=multi.get_inlet('b'))
                    return multi.get_outlet('res')
                ```
                register(action=) :return <Step>
                bind(fromlet=, tolet=)
        :return: <Algorithm>

    Пример использования:

        ```
        res = Parameter(name='res', type_=types.Numeric)
        a = Parameter(name='a', type_=types.Numeric)
        b = Parameter(name='b', type_=types.Numeric)

        # actions
        MultiA = Action('Multi', [a, b], [res])  # умножение

        # квадрат числа
        def build_square(bind, register, a):
            multi = register(MultiA)
            bind(fromlet=a, tolet=multi.get_inlet('a'))
            bind(fromlet=a, tolet=multi.get_inlet('b'))
            return multi.get_outlet('res')

        SquareA = AlgorithmBuilder.build('Square', [a], [res], builder=build_square)
        ```
    """

    @classmethod
    def build(cls, code, in_params, out_params, builder):
        """
        Построение Алгоритма
        :return: <Algorithm>
        """
        alg = Algorithm(code=code, in_params=in_params, out_params=out_params)
        steps = list()
        binds = OrderedDict()

        bind, register = cls._get_spec_funcs(alg=alg, binds=binds, steps=steps)

        res = cls._build(builder=builder, params=dict(register=register, bind=bind, **alg.inlets))
        if len(alg.outlets) == 1:
            res = [res]
        if len(alg.outlets) == 0:
            res = tuple()
        if len(alg.outlets) != len(res):
            raise InvalidParams('Length of outlets ({}) of algorithm {} not match length of results ({})'.format(
                len(alg.outlets), code, len(res)))
        for i in range(len(res)):
            bind(cls._outlet_from_step(res[i]), alg.get_outlet(index=i))
        alg.set_params(steps=steps, binds=binds)
        alg.validate_graph()
        return alg

    @classmethod
    def _get_spec_funcs(cls, alg, binds, steps):
        def bind(fromlet, tolet):
            if not isinstance(fromlet, (Const, StepInlet, StepOutlet, BaseLet)):
                fromlet = Const(fromlet)
            binds[tolet] = fromlet

        def register(action):
            step = Step(action=action, algorithm=alg, number=len(steps))
            steps.append(step)
            return step
        return bind, register

    @classmethod
    def _build(cls, builder, params):
        return builder(**params)

    @classmethod
    def _outlet_from_step(cls, outlet):
        if isinstance(outlet, Step):
            if len(outlet.get_outlets()) > 1:
                raise InvalidDeclaration(
                    'Input incorrect: parameter {step} is not Parameter'.format(step=outlet))
            outlet = outlet.get_outlet(index=0)
        return outlet


class MagicAlgorithmBuilder(AlgorithmBuilder):
    """
    Магический Построитель алгоритмов
    Используется перегрузка магических методов для увеличения эффективности функции builder.
    Получается боллее интуитивное использование построения

    Основной метод AlgorithmBuilder.build(code, in_params, out_params, builder)

        :param code: код нового Алгоритма
        :param in_params: [<Parameter>, ...] Аргументы Алгоритма
        :param out_params: [<Parameter>, ...] Результаты Алгоритма
        :param builder: <func> функция-построитель дерева Алгоритма:
                ```
                def magic_build_square(a):
                    return MultiA(a=a, b=a)
                ```
        :return: <Algorithm>

    Пример использования:

        ```
        res = Parameter(name='res', type_=types.Numeric)
        a = Parameter(name='a', type_=types.Numeric)
        b = Parameter(name='b', type_=types.Numeric)

        # actions
        MultiA = Action('Multi', [a, b], [res])  # умножение

        # квадрат числа
        def magic_build_square(a):
            return MultiA(a=a, b=a)

        SquareA = AlgorithmBuilder.build('Square', [a], [res], builder=build_square)
        ```
    """
    @classmethod
    def _build(cls, builder, params):
        bind, register = params.pop('bind'), params.pop('register')

        def __acall__(self, *args, **kwargs):
            step = register(self)

            for i, v in enumerate(args):
                inlet = cls._outlet_from_step(v) if isinstance(v, Step) else v
                bind(inlet, step.get_inlet(index=i))
            for k, v in kwargs.items():
                inlet = cls._outlet_from_step(v) if isinstance(v, Step) else v
                bind(inlet, step.get_inlet(k))
            return step
        
        old_acall = Action.__call__
        Action.__call__ = __acall__
        result = super(MagicAlgorithmBuilder, cls)._build(builder=builder, params=params)
        Action.__call__ = old_acall
        return result
