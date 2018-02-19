from fictilis.action import Action, Implementation
from fictilis.algbuilder import AlgorithmBuilder, MagicAlgorithmBuilder
from fictilis.interpreter import BaseInterpreter
from fictilis.parameter import Parameter
from fictilis import types
from fictilis.context import Context

from ..base import clear


def test_simple_usecases(dbc):
    # подготавливаем коонект к БД
    conn = dbc.connection
    # Вводим абтракцию для "обмена" данными о таблицах
    class Table:
        def __init__(self, name):
            self.name = name

    # вводим тип таблицы
    def table_validator(value):
        if not isinstance(value, Table):
            raise TypeError
        return value

    TableType = types.Type(code='Table', validator=table_validator)


    context = Parameter(name='context', type_=types.ContextType)
    table = Parameter(name='table', type_=TableType)
    number = Parameter(name='number', type_=types.Numeric)
    column = Parameter(name='column', type_=types.Any)
    name = Parameter(name='name', type_=types.Any)

    # подготавливаем Действия
    Create = Action('Create', [context, name], [table])
    Drop = Action('Drop', [context, table], [])
    CalcSum = Action('CalcSum', [context, table, column], [number])
    MergeTables = Action(
        'MergeTables',
        [context, table, Parameter('table2', TableType)],
        [table])

    # регистрация реализаций в системе
    engine = 'sql'

    def create(context, name):
        context['conn'].execute('''CREATE TEMPORARY TABLE {table} (COL INT);'''.format(table=name))
        context['conn'].execute('''INSERT INTO {table} VALUES (1),(2),(3),(4),(5);'''.format(table=name))
        return Table(name)

    Implementation(action=Create, engine=engine, function=create)
    Implementation(action=Drop, engine=engine, function=lambda context, table: context['conn'].execute('''
        DROP TEMPORARY TABLE IF EXISTS {table};
        '''.format(table=table.name)))
    Implementation(action=CalcSum, engine=engine, function=lambda context, table, column: context['conn'].execute('''
        SELECT SUM({column}) FROM {table};
        '''.format(table=table.name, column=column)).fetchall()[0][0])

    def merge_tables(context, table, table2):
        result = Table('some_table')
        context['conn'].execute('''
        CREATE TEMPORARY TABLE {res_table} AS
            SELECT T1.COL AS COL1, T2.COL AS COL2
                FROM {table1} T1 JOIN {table2} T2;
        '''.format(res_table=result.name, table1=table.name, table2=table2.name))
        print(result)
        return result
    Implementation(action=MergeTables, engine=engine, function=merge_tables)

    # Регистрация алгоритмов
    def some_alg_with_table_builder(context):
        table1 = Create(context, 'tmp_table1')
        table2 = Create(context, 'tmp_table2')
        merged_table = MergeTables(context, table1, table2)
        Drop(context, table1)
        Drop(context, table2)
        summa = CalcSum(context, merged_table, 'COL2')
        Drop(context, merged_table)
        return summa

    SomeAlgWithTables = MagicAlgorithmBuilder.build(
        'SomeAlgWithTables',
        in_params=[context],
        out_params=[number],
        builder=some_alg_with_table_builder)

    result = BaseInterpreter.evaluate(
        SomeAlgWithTables,
        context=Context(conn=conn),
        params=dict()
    )
    print(result)
    assert result['number'] == 75.0
