class Panic(Exception):
    """
    Raised when panicking.
    """
    pass


def panic(message: str) -> None:
    """
    Panic. Raises a Panic exception.
    """

    raise Panic(message)
