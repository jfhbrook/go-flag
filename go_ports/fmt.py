from typing import Any, List, Dict, Type

from go_ports.error import GoError


def errorf(format: str, *args: List[Any], **kwargs: Dict[str, Any]) -> Type[GoError]:
    return GoError.from_string(format.format(*args, **kwargs))
