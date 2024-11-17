from typing import NoReturn, Optional


class Panic(Exception):
    """
    Panic!
    """

    pass


def panic(message: str, exc: Optional[Exception] = None) -> NoReturn:
    """
    Panic!
    """

    panic = Panic(message)

    if exc:
        raise panic from exc
    raise panic
