
def test_hello_world(capsys):
    import hello
    captured = capsys.readouterr()
    assert captured.out == "Hello, world!\n"

