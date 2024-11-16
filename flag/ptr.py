from typing import Optional

from go_ports.panic import panic


class Ptr[V]:
    """
    A pointer. Go has pointers, Python does not. This class assists in
    use cases involving pointers, such as in passing a reference to a
    function which mutates its value:

    ```py
    p = Ptr(False)

    set_to_true(p)

    # This will succeed
    assert p.deref()
    ```

    Note that this is NOT a true pointer - it won't update the value of a
    wrapped variable. For example:

    ```py
    value = False
    p = Ptr(value)
    p.set(True)

    # This will fail!
    assert value
    ```

    Instead, you must create the value as a pointer, and use the pointer to set
    the value:

    ```
    value = Ptr(False)
    p.set(True)

    # This will succeed
    assert value.deref()
    ```
    """

    value: Optional[V]

    def __init__(self, value: Optional[V] = None) -> None:
        self.value = value

    def set(self, value: V) -> None:
        """
        Set the value at a pointer.
        """
        self.value = value

    def deref(self) -> V:
        """
        Dereference the pointer, getting its underlying value.
        """
        if self.value is not None:
            return self.value
        panic("nil pointer dereference")
