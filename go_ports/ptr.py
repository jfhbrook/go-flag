"""
A port of go's flag package: https://pkg.go.dev/flag
"""

from typing import Dict


class Ptr:
    """
    A pointer. Go has pointers, Python does not. Python's references will
    often be sufficient, but won't allow for setting the value of a pointer.
    This class is used in those cases.
    """

    _current: int = 0
    _values: Dict[int, object] = {}

    def __init__(self, value: object) -> None:
        self._values[self._current] = value

        self.address: int = self._current

        self._current += 1

    def set(self, value: object) -> None:
        self._values[self.address] = value

    def deref(self) -> object:
        return self._values[self.address]

    def __del__(self) -> None:
        del self._values[self.address]
