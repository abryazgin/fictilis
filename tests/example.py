from fictilis.action import Action, Implementation
from fictilis.algbuilder import MagicAlgorithmBuilder
from fictilis.parameter import Parameter
from fictilis import types
from fictilis.interpreter import BaseInterpreter

a = Parameter(name='a', type_=types.Numeric)
b = Parameter(name='b', type_=types.Numeric)
c = Parameter(name='c', type_=types.Numeric)
d = Parameter(name='d', type_=types.Numeric)
res = Parameter(name='res', type_=types.Numeric)

calc_c = Action('calc_c', in_params=[a, b], out_params=[res])
calc_d = Action('calc_d', in_params=[a, c], out_params=[res])
prepare_result = Action('prepare_result', in_params=[a, b, c, d], out_params=[res])


def builder(a, b):
    c = calc_c(a, b)
    d = calc_d(a, c)
    return prepare_result(a, b, c, d)

calc = MagicAlgorithmBuilder.build(
    'calc', [a, b], [res], builder=builder)  # Вычитание

print(calc)


#  Implementations

engine = 'some_engine'
Implementation(
    action=calc_c, engine=engine, function=lambda a, b: a + b)
Implementation(
    action=calc_d, engine=engine, function=lambda a, c: a * c)
Implementation(
    action=prepare_result, engine=engine,
    function=lambda a, b, c, d: c**a + d**b)


# Run

A = 2
B = 1
result = BaseInterpreter.evaluate(
    calc,
    params=dict(a=A, b=B)
)
print('Result:', result)
assert result['res'] == 15
