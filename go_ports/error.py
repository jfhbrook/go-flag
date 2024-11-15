from typing import Type


class GoError(Exception):
    """
    A generic go error.
    """

    @classmethod
    def from_string(cls: Type["GoError"], string: str) -> Type["GoError"]:
        def __init__(self: "GoError") -> None:
            super().__init__(string)

        return type("GoError", (cls,), dict(__init__=__init__))
