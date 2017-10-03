from contextlib import contextmanager
from timeit import default_timer


@contextmanager
def timeit():
    """
    Менеджер контекста, который занимается засечением выполнения блока
    :return: <callable> "функция", которая при вызове возвращает количество(float) секунд выполнения
    """
    start = default_timer()

    def expired():
        return default_timer() - start

    yield expired

