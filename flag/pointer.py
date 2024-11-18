import datetime
from typing import Any, cast, Dict, Optional, Protocol

from flag.panic import panic

# Methods that I KNOW would be dangerous to proxy/overwrite
FORBIDDEN = {
    "__abstractmethods__",
    "__annotations__",
    "__callable_proto_members_only__",
    "__class__",
    "__class_getitem__",
    "__delattr__",
    "__dict__",
    "__dir__",
    "__doc__",
    "__format__",
    "__getattribute__",
    "__getnewargs__",
    "__getstate__",
    "__init__",
    "__init_subclass__",
    "__module__",
    "__new__",
    "__orig_bases__",
    "__parameters__",
    "__pos__",
    "__protocol_attrs__",
    "__reduce__",
    "__reduce_ex__",
    "__repr__",
    "__setattr__",
    "__sizeof__",
    "__slots__",
    "__str__",
    "__subclasshook__",
    "__trunc__",
    "__type_params__",
    "__weakref__",
    "_abc_impl",
    "_is_protocol",
    "_is_runtime_protocol",
}

# Default methods to attach
DEFAULTS = {
    method
    for method in (
        set(dir(False))
        | set(dir(0))
        | set(dir(""))
        | set(dir(0.0))
        | set(dir(datetime.timedelta()))
    )
    if method not in FORBIDDEN
}


class Pointer[V](Protocol):
    """
    A pointer. Go has pointers, Python does not. This protocol assists in
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


def _magic[T](p: Pointer[T], value: Optional[T]) -> None:
    """
    Proxy methods from the pointer to the underlying value. Extreme
    shenanigans afoot!
    """

    cls = p.__class__
    cls_methods = {method for method in dir(cls) if not method.startswith("_")}

    if value is None:
        methods = DEFAULTS
    else:
        methods = dir(value)
    for method in methods:
        if method in cls_methods or method in FORBIDDEN:
            continue
        setattr(
            p, method, lambda *args, **kwargs: getattr(value, method)(*args, **kwargs)
        )


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
        _magic(self, self.value)

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
        return f"Ptr({self.value})"


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

        _magic(self, getattr(self.obj, self.name, None))

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
        if self.is_nil():
            value = None
        else:
            value = getattr(self.obj, self.name)
        return f"AttrRef({self.name}={value})"


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
        self.dict = dict_
        self.key = key
        _magic(self, getattr(self.dict, self.key, None))

    def set_(self, value: V) -> None:
        """
        Set the value at the key.
        """
        self.dict[self.key] = value

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
        return f"KeyRef({self.key}={self.dict_.get(self.key, None)})"
