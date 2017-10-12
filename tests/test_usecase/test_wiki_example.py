from fictilis.action import Action, Implementation
from fictilis.algbuilder import MagicAlgorithmBuilder
from fictilis.interpreter import BaseInterpreter
from fictilis.parameter import Parameter
from fictilis import types


def test_simple_usecases():
    # для удобства заблоговременно регистрируем Параметры - их удобно 
    # переиспользовать, нежели описывать прямо в Действиях и Алгоритмах
    res = Parameter(name='res', type_=types.Numeric)
    a = Parameter(name='a', type_=types.Numeric)
    b = Parameter(name='b', type_=types.Numeric)

    # Регистрируем Действия с описанием входных и выходных параметров 
    NegationA = Action('Negation', in_params=[a], out_params=[res])  # инверсия числа
    SumA = Action('Sum', [a, b], [res])  # сумма
    MultiA = Action('Multi', [a, b], [res])  # умножение
    DivisionA = Action('Division', [a, b], [res])  # деление

    # Регистрируем реализации в системе
    # Для этого декларируем какой-то движок (на самом деле это просто строка,
    # которая "объединяет" реализации
    engine = 'some_string_that_represent_PYTHON_engine'
    Implementation(action=NegationA, engine=engine, function=lambda a: -a)
    Implementation(action=SumA, engine=engine, function=lambda a, b: a + b)
    Implementation(action=MultiA, engine=engine, function=lambda a, b: a * b)
    Implementation(action=DivisionA, engine=engine, function=lambda a, b: a / b)

    # Регистрируем действия в виде Алгоритмов.
    # Обращаем внимание, что никакого выполнения реальных операций ("сложение" и прочее) в этот момент не происходит -
    # это всего лишь интуитивно понятное представление Алгоритма в виде последовательности Действий и потоков данных
    SubtractionA = MagicAlgorithmBuilder.build(
        'SubtractionA', [a, b], [res], builder=lambda a, b: SumA(a=a, b=NegationA(b)))  # Вычитание
    SquareA = MagicAlgorithmBuilder.build(
        'SquareA', [a], [res], builder=lambda a: MultiA(a=a, b=a))  # Квадрат числа

    # А это непосредственно выполнения алгоритма
    assert BaseInterpreter.evaluate(SquareA, params=dict(a=3)) == {'res': 9}
    assert BaseInterpreter.evaluate(SubtractionA, params=dict(a='1', b=2)) == {'res': -1}
