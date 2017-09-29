def test_dbc(dbc):
    assert dbc.connection.execute('SELECT 1').fetchall()[0][0] == 1
