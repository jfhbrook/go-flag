from flag.error import Error
import flag.time as time

RangeError = Error.from_string("value out of range")
SyntaxError = Error.from_string("invalid syntax")


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


def parse_int(s: str, base: int = 10) -> int:
    raise NotImplementedError("parse_int")


def format_int(i: int, base: int = 10) -> str:
    raise NotImplementedError("format_int")


def itoa(i: int) -> str:
    return format_int(i, 10)


def parse_float(s: str) -> float:
    raise NotImplementedError("parse_float")


def format_float(f: float, fmt: str, prec: int) -> str:
    raise NotImplementedError("format_float")


def format_duration(delta: time.Duration) -> str:
    raise NotImplementedError("format_duration")
