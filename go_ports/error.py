from typing import Type


class Error(Exception):
    """
    A generic go error.
    """

    @classmethod
    def from_string(cls: Type["Error"], string: str) -> Type["Error"]:
        """
        Create a go error from a string.

        In go, the error *is* a string, but with the error interface applied
        to it. This error can be created once, and then returned whenever
        that error is needed.

        In Python, we dynamically create an Error subclass, which may then
        be called at the time of raising.
        """

        def __init__(_self: "Error") -> None:
            super().__init__(string)

        return type("Error", (cls,), dict(__init__=__init__))
