from typing import Any, Type

from flag.error import Error


def errorf(format: str, *args: Any, **kwargs: Any) -> Type[Error]:
    return Error.from_string(format.format(*args, **kwargs))
