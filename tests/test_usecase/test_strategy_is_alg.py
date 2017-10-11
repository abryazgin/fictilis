from fictilis.action import Action, Implementation, ImplementationPool as ASP
from fictilis.algbuilder import MagicAlgorithmBuilder
from fictilis.interpreter import BaseInterpreter
from fictilis.parameter import Parameter
from fictilis import types
from fictilis.context import Context


def test_engine_is_algorithm():
    res = Parameter(name='res', type_=types.Numeric)
    a = Parameter(name='a', type_=types.Numeric)
    b = Parameter(name='b', type_=types.Numeric)

    A = Action(code='A', in_params=[a], out_params=[res])
    A1 = Action(code='A1', in_params=[a], out_params=[res])
    A2_sub = Action(code='A2_sub', in_params=[a], out_params=[res])

    engine1 = 1
    engine2 = 2

    A2 = MagicAlgorithmBuilder.build('A2', [a], [res], builder=lambda a: A2_sub(A2_sub(a)))

    Implementation(action=A1, engine=engine1, function=lambda a: a + 2)
    Implementation(action=A2_sub, engine=engine2, function=lambda a: a + 1)
    ASP.register(code=A.code, engine=engine1, implementation=A1)
    ASP.register(code=A.code, engine=engine2, implementation=A2)

    # вычитание
    for engine in engine1, engine2:
        print('------------------------')
        print(engine)
        result = BaseInterpreter.evaluate(A, context=Context(engine=engine), params=dict(a=7))
        print(result)
        assert isinstance(result, dict)
        assert set(result.keys()) == {'res'}
        assert result['res'] == 9
