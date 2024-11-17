import re

import flag.time as time


def parse_bool(string: str) -> bool:
    if string in {"1", "t", "T", "TRUE", "true", "True"}:
        return True
    elif string in {"0", "f", "F", "FALSE", "false", "False"}:
        return False

    raise ValueError("invalid syntax")


def format_bool(b: bool) -> str:
    if b:
        return "true"
    return "false"


def format_float(f: float) -> str:
    return re.sub(r"\.0*$", "", str(f))


def format_duration(delta: time.Duration) -> str:
    raise NotImplementedError("format_duration")
