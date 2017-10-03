from fictilis.action import Action, ActionStrategy, ActionStrategyPool as ASP
from fictilis.algbuilder import MagicAlgorithmBuilder
from fictilis.interpreter import BaseInterpreter
from fictilis.parameter import Parameter
from fictilis import types
from fictilis.context import Context


def test_strategy_is_algorithm():
    res = Parameter(name='res', type_=types.Numeric)
    a = Parameter(name='a', type_=types.Numeric)
    b = Parameter(name='b', type_=types.Numeric)

    A = Action(code='A', in_params=[a], out_params=[res])
    A1 = Action(code='A1', in_params=[a], out_params=[res])
    A2_sub = Action(code='A2_sub', in_params=[a], out_params=[res])

    strategy1 = 1
    strategy2 = 2

    A2 = MagicAlgorithmBuilder.build('A2', [a], [res], builder=lambda a: A2_sub(A2_sub(a)))

    ActionStrategy(action=A1, strategy=strategy1, function=lambda a: a + 2)
    ActionStrategy(action=A2_sub, strategy=strategy2, function=lambda a: a + 1)
    ASP.register(code=A.code, strategy=strategy1, actionstrategy=A1)
    ASP.register(code=A.code, strategy=strategy2, actionstrategy=A2)

    # вычитание
    for strategy in strategy1, strategy2:
        print('------------------------')
        print(strategy)
        result = BaseInterpreter.evaluate(A, context=Context(strategy=strategy), params=dict(a=7))
        print(result)
        assert isinstance(result, dict)
        assert set(result.keys()) == {'res'}
        assert result['res'] == 9
