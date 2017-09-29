from .algorithm import Algorithm, Step
from .action import Action
from .errors import InvalidParams, InvalidDeclaration


class AlgorithmBuilder:
    """
    Построитель алгоритмов
    """

    @classmethod
    def get_spec_funcs(cls, alg, binds, steps):
        def bind(fromlet, tolet):
            binds[tolet] = fromlet

        def register(action):
            step = Step(action=action, algorithm=alg, number=len(steps))
            steps.append(step)
            return step
        return bind, register

    @classmethod
    def build(cls, code, in_params, out_params, builder):
        alg = Algorithm(code=code, in_params=in_params, out_params=out_params)
        steps = list()
        binds = dict()

        bind, register = cls.get_spec_funcs(alg=alg, binds=binds, steps=steps)

        res = cls._build(builder=builder, params=dict(register=register, bind=bind, **alg.inlets))
        if len(alg.outlets) == 1:
            res = [cls._outlet_from_step(res)]
        if len(alg.outlets) != len(res):
            raise InvalidParams('Length of outlets ({}) of algorithm {} not match length of results ({})'.format(
                len(alg.outlets), code, len(res)))
        for i in range(len(res)):
            bind(res[i], alg.get_outlet(index=i))
        alg.set_params(steps=steps, binds=binds)
        alg.validate_graph()
        return alg

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
    Построитель алгоритмов
    """
    @classmethod
    def _build(cls, builder, params):
        bind, register = params.pop('bind'), params.pop('register')

        def __acall__(self, *args, **kwargs):
            step = register(self)

            for i, v in enumerate(args):
                bind(cls._outlet_from_step(v), step.get_inlet(index=i))
            for k, v in kwargs.items():
                bind(cls._outlet_from_step(v), step.get_inlet(k))
            return step

        old_acall = Action.__call__
        Action.__call__ = __acall__
        result = super(MagicAlgorithmBuilder, cls)._build(builder=builder, params=params)
        Action.__call__ = old_acall
        return result
