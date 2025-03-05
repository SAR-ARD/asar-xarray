from asar_xarray import main


def test__get_greeting():
    assert "Hello World!" == main.get_greeting()
