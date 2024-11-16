from typing import NoReturn


class Panic(Exception):
    """
    Panic!
    """

    pass


def panic(message: str) -> NoReturn:
    """
    Panic!
    """

    raise Panic(message)
