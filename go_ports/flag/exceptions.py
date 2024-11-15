class FlagError(Exception):
    """
    A generic flag error.
    """


class FlagParseError(FlagError):
    """
    Parse error
    """

    def __init__(self) -> None:
        super().__init__("parse error")


class FlagSyntaxError(FlagError):
    """
    Invalid syntax
    """

    def __init__(self) -> None:
        super().__init__("invalid syntax")


class FlagRangeError(FlagError):
    """
    Value out of range
    """

    def __init__(self) -> None:
        super().__init__("value out of range")
