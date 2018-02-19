from fictilis.action import ActionPool, ImplementationPool
from fictilis.algorithm import AlgorithmPool


def clear():
    ActionPool._reset()
    ImplementationPool._reset()
    AlgorithmPool._reset()
