"""
A port of go's flag package: https://pkg.go.dev/flag
"""

from typing import cast
from weakref import WeakValueDictionary


# TODO: Add generic type to Ptr - go does support such a type
class Ptr[V]:
    """
    A pointer. Go has pointers, Python does not. Python's references will
    often be sufficient, but won't allow for setting the value of a pointer.
    This class is used in those cases.

    Note that Ptr is not type safe - you will need to inspect or cast its
    value after dereferencing it.
    """

    _current: int = 0
    _values: WeakValueDictionary[int, object] = WeakValueDictionary()

    def __init__(self, value: V) -> None:
        self._values[self._current] = value

        self.address: int = self._current

        self._current += 1

    def set(self, value: V) -> None:
        self._values[self.address] = value

    def deref(self) -> V:
        return cast(V, self._values[self.address])
