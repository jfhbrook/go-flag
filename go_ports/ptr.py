class Ptr[V]:
    """
    A pointer. Go has pointers, Python does not. In cases where a value needs
    to be updated by reference, this class can help.

    Note that this is NOT a true pointer - it won't update the value of a
    wrapped variable. For example:

    ```py
    value = False
    p = Ptr(value)
    p.set(True)

    # This will fail!
    assert value
    ```

    Instead, create the value as a pointer, and use the pointer to set
    the value:

    ```
    value = Ptr(False)
    p.set(True)

    # This will succeed
    assert value.deref()
    ```
    """

    def __init__(self, value: V) -> None:
        self.value: V = value

    def set(self, value: V) -> None:
        """
        Set the value at a pointer.
        """
        self.value = value

    def deref(self) -> V:
        """
        Dereference the pointer, getting its underlying value.
        """
        return self.value
