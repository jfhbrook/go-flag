from typing import Type


class GoError(Exception):
    """
    A generic go error.
    """

    @classmethod
    def cls(cls: Type["GoError"], message: str) -> Type["GoError"]:
        def __init__(self: "GoError") -> None:
            super().__init__(message)

        return type("GoError", (cls,), dict(__init__=__init__))
