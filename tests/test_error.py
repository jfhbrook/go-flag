from flag import Error


def test_from_string() -> None:
    MyError = Error.from_string("test error")
    exc = MyError()
    assert isinstance(exc, Error)
    assert isinstance(exc, MyError)


def test_error_str() -> None:
    exc = Error("some error")
    assert str(exc) == "some error"
