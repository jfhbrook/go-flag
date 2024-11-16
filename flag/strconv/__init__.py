import datetime

from go_ports.error import GoError

RangeError = GoError.cls("value out of range")
SyntaxError = GoError.cls("invalid syntax")


def parse_bool(string: str) -> bool:
    if string in {"1", "t", "T", "TRUE", "true", "True"}:
        return True
    elif string in {"0", "f", "F", "FALSE", "false", "False"}:
        return False

    raise SyntaxError()


def format_bool(b: bool) -> str:
    if b:
        return "true"
    return "false"


def parse_int(s: str, base: int, bit_size: int) -> int:
    pass


def format_int(i: int, base: int) -> str:
    pass


def itoa(i: int) -> str:
    return format_int(i, 10)


def parse_float(s: str, bit_size: int) -> float:
    pass


def format_float(f: float, fmt: str, prec: int, bit_size: int) -> str:
    pass


def format_timedelta(delta: datetime.timedelta) -> str:
    """
    Format a timedelta like go's time.Duration#String
    """
    pass
