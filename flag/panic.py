from typing import NoReturn, Optional


class Panic(Exception):
    """
    Panic!
    """

    def __init__(self, message: str) -> None:
        super().__init__(f"panic: {message}")


def panic(message: str, exc: Optional[Exception] = None) -> NoReturn:
    """
    Panic!
    """

    panic = Panic(message)

    if exc:
        raise panic from exc
    raise panic
