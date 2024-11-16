from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, cast, Dict, Generator, List, Optional, TypeVar
import warnings

from flag.panic import panic, Panic

Fn = TypeVar("Fn", bound=Callable)

DeferFn = Callable[[], None]

FUNCTIONS: List[Callable] = []
DEFERRED: Dict[Callable, List[DeferFn]] = defaultdict(lambda: [])


# Pushes the given function onto the current context
@contextmanager
def ctx(fn) -> Generator[None, Any, None]:
    global FUNCTIONS
    FUNCTIONS.append(fn)
    try:
        yield fn
    finally:
        FUNCTIONS.pop()


# Peek at the currently running function
def peek() -> Callable:
    global FUNCTIONS
    return FUNCTIONS[-1]


# Get deferred actions for a function
def deferred(fn: Callable) -> List[DeferFn]:
    global DEFERRED
    return DEFERRED[fn]


def defer(fn: DeferFn) -> None:
    """
    Defer an action until the end of function execution. The function must be
    decorated with deferring.

    Note that in go, deferred functions may not return an error. However,
    they may panic.
    """

    caller: Callable = peek()

    if not cast(Any, caller)._deferrable:
        panic(f"Function {caller} is not deferrable!")

    deferred(caller).append(fn)


def run(fn: Callable, panic: Optional[Panic] = None) -> None:
    for d in deferred(fn):
        try:
            d()
        except Panic as exc:
            # If any of the deferreds panic, we want to surface that
            # panic. However, under a panic situation we must also
            # run all deferreds. We split the difference by raising
            # the first encountered panic, but warning on any others.
            if panic:
                warnings.warn(str(exc))
            else:
                panic = exc
        except Exception as exc:
            # Go deferred actions may not return an error. However,
            # any function in Python may raise an exception. We split
            # the difference by warning on any raised exceptions.
            warnings.warn(str(exc))
    if panic:
        raise panic


def deferring(fn: Fn) -> Fn:
    """
    Functions decorated with deferring support defer(fn).
    """

    @wraps(fn)
    def with_deferral(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
        with ctx(fn):
            try:
                rv: Any = fn(*args, **kwargs)
            except Panic as p:
                run(fn, p)
            except GoError as exc:
                run(fn)
                raise exc
            else:
                run(fn)
                return rv

    return cast(Fn, with_deferral)
