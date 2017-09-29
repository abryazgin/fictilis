from fictilis.action import Action, ActionStratagy
from fictilis.algorithm import AlgorithmBuilder
from fictilis.interpreter import BaseInterpreter
from fictilis.parameter import Parameter
from fictilis import types
from fictilis.context import Context


def test_simple_usecases():
    res = Parameter(name='res', type_=types.Numeric)
    context = Parameter(name='context', type_=types.ContextType)
    a = Parameter(name='a', type_=types.Numeric)
    b = Parameter(name='b', type_=types.Numeric)

    # actions
    NegationA = Action('Negation', in_params=[a], out_params=[res])  # отрицание
    SumA = Action('Sum', [a, b], [res])  # сумма
    MultiA = Action('Multi', [a, b], [res])  # умножение
    DivisionA = Action('Division', [a, b], [res])  # деление

    # вычитание
    def build_subtraction(bind, register, a, b):
        neg = register(NegationA)
        bind(fromlet=b, tolet=neg.get_inlet('a'))
        summa = register(SumA)
        bind(fromlet=a, tolet=summa.get_inlet('a'))
        bind(fromlet=neg.get_outlet('res'), tolet=summa.get_inlet('b'))
        return summa.get_outlet('res')

    SubtractionA = AlgorithmBuilder.build('Subtraction', [a, b], [res], builder=build_subtraction)

    # квадрат числа
    def build_square(bind, register, a):
        multi = register(MultiA)
        bind(fromlet=a, tolet=multi.get_inlet('a'))
        bind(fromlet=a, tolet=multi.get_inlet('b'))
        return multi.get_outlet('res')

    SquareA = AlgorithmBuilder.build('Square', [a], [res], builder=build_square)

    # регистрация стратегий в системе
    strategy = 'python'
    ActionStratagy(action=NegationA, strategy=strategy, function=lambda a: -a)
    ActionStratagy(action=SumA, strategy=strategy, function=lambda a, b: a + b)
    ActionStratagy(action=MultiA, strategy=strategy, function=lambda a, b: a * b)
    ActionStratagy(action=DivisionA, strategy=strategy, function=lambda a, b: a / b)

    # вычитание
    print('------------------------')
    print(SubtractionA)
    print('------------------------')
    res = BaseInterpreter.evaluate(SubtractionA, context=Context(), params=dict(a='1', b=2))
    print(res)
    assert isinstance(res, dict)
    assert set(res.keys()) == {'res'}
    assert res['res'] == -1

    # квадрат
    print(SquareA)
    print('------------------------')
    res = BaseInterpreter.evaluate(SquareA, context=Context(), params=dict(a=3))
    print(res)
    assert isinstance(res, dict)
    assert set(res.keys()) == {'res'}
    assert res['res'] == 9
    print('------------------------')
