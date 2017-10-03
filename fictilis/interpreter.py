from .algorithm import Algorithm
from .action import ActionStrategyPool, Action
from .errors import InvalidParams, InvalidDeclaration
from . import types


class BaseInterpreter:

    @classmethod
    def evaluate(cls, action, context, params):
        # make copy of params
        params = dict(**params)
        return cls._evaluate(action, context, params)

    @classmethod
    def _evaluate(cls, action, context, params):
        cls._add_context_if_needed(action, context, params)
        params = action.validate_inputs(params)
        if isinstance(action, Algorithm):
            result = cls._evaluate_algorithm(action, context, params)
        else:
            result = cls._evaluate_action(action, context, params)
        result = action.validate_outputs(result)
        return result

    @classmethod
    def _evaluate_action(cls, action, context, params):
        actionstrategy = cls._choose_actionstrategy(action, context, params)
        if isinstance(actionstrategy, Action):
            return cls._evaluate(action=actionstrategy, context=context, params=params)
        res = actionstrategy.evaluate(params)
        return cls._result_to_dict(res=res, action=action)

    @classmethod
    def _result_to_dict(cls, res, action):
        action_outlets = action.get_outlets()
        if len(action_outlets) == 0:
            res = []
        if len(action_outlets) == 1:
            res = [res]
        if len(action_outlets) != len(res):
            raise InvalidDeclaration('Length of outlets ({}) of action {} not match length of results ({})'.format(
                len(action_outlets), action.code, len(res)))
        return {action.get_outlet(index=i).code: res[i] for i in range(len(action_outlets))}

    @classmethod
    def _evaluate_algorithm(cls, algorithm, context, params):
        let_values = dict()
        
        def append_step_results(letable, results):
            for code, value in results.items():
                let_values[letable.get_outlet(code=code)] = value

        # register input algorithm
        for code, value in params.items():
            let_values[algorithm.get_inlet(code=code)] = value

        for step in algorithm:
            step_params = cls._prepare_step_params(algorithm, step, let_values, context)
            step_result = cls._evaluate(step.action, context, params=step_params)
            append_step_results(step, step_result)
        results = cls._prepare_alg_results(algorithm, let_values)
        del let_values
        return results

    @classmethod
    def _prepare_step_params(cls, algorithm, step, let_values, context):
        def get_value(stepinlet):
            if stepinlet.inlet.get_type() == types.ContextType:
                return context
            return let_values[algorithm.binds[stepinlet]]
        return {
            stepinlet.inlet.code: get_value(stepinlet) for stepinlet in step.get_inlets().values()}

    @classmethod
    def _prepare_alg_results(cls, algorithm, let_values):
        return {
            outlet.code: let_values[algorithm.binds[outlet]] for outlet in algorithm.get_outlets().values()}

    @classmethod
    def _add_context_if_needed(cls, action, context, params):
        for inlet in action.get_inlets().values():
            if inlet.parameter.type == types.ContextType:
                params[inlet.code] = context
                return

    @classmethod
    def _choose_actionstrategy(cls, action, context, params):
        choices = ActionStrategyPool.list(code=action.code)
        if len(choices) == 0:
            raise InvalidParams('Strategies for action {code} does not exist'.format(code=action.code))
        # if strategy declared in context
        if context.get('strategy') and context.get('strategy') in choices:
            return choices[context.get('strategy')]
        # first choice
        for key in choices:
            return choices[key]
