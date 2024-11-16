from typing import Any, List, Dict, Type

from go_ports.error import Error


def errorf(format: str, *args: Any, **kwargs: Any) -> Type[Error]:
    return Error.from_string(format.format(*args, **kwargs))
