from pytest import MonkeyPatch

def test_hello_world_input(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "George")
    import hello_input
    captured = capsys.readouterr()
    assert captured.out == "Hello, George!\n"

