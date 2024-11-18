from abc import ABC
from typing import Any, cast, Dict, Optional

from flag.panic import panic


class Pointer[V](ABC):
    """
    A pointer. Go has pointers, Python does not. This class assists in
    use cases involving pointers, such as in passing a reference to a
    function which mutates its value.
    """

    def set_(self, value: V) -> None:
        """
        Set the value at a pointer.
        """
        ...

    def deref(self) -> V:
        """
        Dereference the pointer, getting its underlying value.
        """
        ...

    def is_nil(self) -> bool:
        """
        Whether or not the pointer is nil. If the pointer is nil, then
        dereferencing it will cause a panic.
        """
        ...

    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute from the underlying value.
        """
        ...

    def __rrshift__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rrshift__")(*args, **kwargs)

    def __radd__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__radd__")(*args, **kwargs)

    def __rtruediv__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rtruediv__")(*args, **kwargs)

    def __neg__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__neg__")(*args, **kwargs)

    def __mod__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__mod__")(*args, **kwargs)

    def __eq__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__eq__")(*args, **kwargs)

    def __ror__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__ror__")(*args, **kwargs)

    def __invert__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__invert__")(*args, **kwargs)

    def __rfloordiv__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rfloordiv__")(*args, **kwargs)

    def __le__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__le__")(*args, **kwargs)

    def __sub__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__sub__")(*args, **kwargs)

    def __rdivmod__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rdivmod__")(*args, **kwargs)

    def __lshift__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__lshift__")(*args, **kwargs)

    def __floor__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__floor__")(*args, **kwargs)

    def __rshift__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rshift__")(*args, **kwargs)

    def __floordiv__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__floordiv__")(*args, **kwargs)

    def __pow__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__pow__")(*args, **kwargs)

    def __ceil__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__ceil__")(*args, **kwargs)

    def __add__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__add__")(*args, **kwargs)

    def __and__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__and__")(*args, **kwargs)

    def __bool__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__bool__")(*args, **kwargs)

    def __rmod__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rmod__")(*args, **kwargs)

    def __divmod__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__divmod__")(*args, **kwargs)

    def __rlshift__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rlshift__")(*args, **kwargs)

    def __abs__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__abs__")(*args, **kwargs)

    def __rsub__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rsub__")(*args, **kwargs)

    def __ne__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__ne__")(*args, **kwargs)

    def __rxor__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rxor__")(*args, **kwargs)

    def __lt__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__lt__")(*args, **kwargs)

    def __ge__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__ge__")(*args, **kwargs)

    def __int__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__int__")(*args, **kwargs)

    def __rand__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rand__")(*args, **kwargs)

    def __round__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__round__")(*args, **kwargs)

    def __gt__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__gt__")(*args, **kwargs)

    def __or__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__or__")(*args, **kwargs)

    def __float__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__float__")(*args, **kwargs)

    def __xor__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__xor__")(*args, **kwargs)

    def __rpow__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rpow__")(*args, **kwargs)

    def __trunc__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__trunc__")(*args, **kwargs)

    def __truediv__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__truediv__")(*args, **kwargs)

    def __mul__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__mul__")(*args, **kwargs)

    def __rmul__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__rmul__")(*args, **kwargs)

    def __hash__(self, *args, **kwargs) -> Any:
        return self.__getattr__("__hash__")(*args, **kwargs)


class Ptr[V](Pointer):
    """
    A simple pointer. This may be used when an interface expects a
    pointer and you don't otherwise need a reference. For example:

    ```py
    p = Ptr(False)

    set_to_true(p)

    # Value is True
    assert p.deref()
    ```

    Note that this is NOT a true pointer - it won't update the value of a
    wrapped variable. For example:

    ```py
    value = False
    p = Ptr(value)
    p.set_(True)

    # This will fail!
    assert value
    ```

    Instead, you must create the value as a pointer, and use the pointer to set
    the value.
    """

    value: Optional[V]

    def __init__(self, value: Optional[V] = None) -> None:
        self.value = value

    def set_(self, value: V) -> None:
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

    def is_nil(self) -> bool:
        return self.value is None

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Ptr({self.value})"

    def __getattr__(self, name: str) -> Any:
        return getattr(self.value, name)


class AttrRef[V](Pointer):
    """
    A reference to a property on another object. This may be used
    when you want a Pointer that will update an existing attribute on an
    object. For example:

    ```py
    @dataclass
    class Data:
        prop: bool

    data = Data(prop=True)

    p = AttrRef(data, "prop")

    set_to_true(p)

    # Value is True
    assert data.prop
    ```

    Note that this class is not type safe. Since it may reference any object
    and be of any Value, it's not viable to assert typing.
    """

    obj: object
    name: str

    def __init__(self, obj: object, name: str) -> None:
        self.obj = obj
        self.name = name

    def set_(self, value: V) -> None:
        """
        Set the value of the attribute.
        """
        setattr(self.obj, self.name, value)

    def deref(self) -> V:
        """
        Dereference the pointer, getting the value of the underlying attribute.
        """
        if not hasattr(self.obj, self.name):
            panic("nil pointer dereference")
        attr = getattr(self.obj, self.name)
        if attr is not None:
            return cast(V, attr)
        panic("nil pointer dereference")

    def is_nil(self) -> bool:
        if not hasattr(self.obj, self.name):
            return True

        if getattr(self.obj, self.name) is None:
            return True

        return False

    def __str__(self) -> str:
        return str(getattr(self.obj, self.name, None))

    def __repr__(self) -> str:
        value = getattr(self.obj, self.name, None)
        return f"AttrRef({self.name}={value})"

    def __getattr__(self, name: str) -> Any:
        return getattr(getattr(self.obj, self.name), name)


class KeyRef[V](Pointer):
    """
    A reference to a key on a dict. This may be used when you want a Pointer
    that will update an existing value in a dict. For example:

    ```py
    data = dict()

    p = KeyRef(data, "key")

    set_to_true(p)

    # Value is True
    assert data["key"]
    ```

    Note that this class is not type safe. Since it may reference any dict
    and be of any Value, it's not viable to assert typing.
    """

    dict_: Dict[Any, Any]
    key: Any

    def __init__(self, dict_: Dict[Any, Any], key: Any) -> None:
        self.dict_ = dict_
        self.key = key

    def set_(self, value: V) -> None:
        """
        Set the value at the key.
        """
        self.dict_[self.key] = value

    def deref(self) -> V:
        """
        Dereference the pointer, getting the value at the underlying key.
        """
        if self.key not in self.dict_:
            panic("nil pointer dereference")
        value = self.dict_[self.key]
        if value is not None:
            return cast(V, value)
        panic("nil pointer dereference")

    def is_nil(self) -> bool:
        return self.dict_.get(self.key, None) is None

    def __str__(self) -> str:
        return str(self.dict_.get(self.key, None))

    def __repr__(self) -> str:
        return f"KeyRef({self.key}={self.dict_.get(self.key, None)})"

    def __getattr__(self, name: str) -> Any:
        value = self.dict_[self.key]
        return getattr(value, name)
