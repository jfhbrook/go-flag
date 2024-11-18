import pytest

from flag import panic, Panic


def test_panic_raises() -> None:
    with pytest.raises(Panic):
        panic("oops")


def test_panic_str() -> None:
    exc = Panic("oops")
    assert str(exc) == "panic: oops"
