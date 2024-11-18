from typing import cast

import pytest

from flag.panic import Panic
from flag.pointer import AttrRef, KeyRef, Ptr


class Config:
    int_: int = 1


config = {"int": 1}

int_ptr = Ptr(1)
int_attr = AttrRef(Config, "int_")
int_key = KeyRef(config, "int")


@pytest.fixture
def int_values() -> None:
    int_ptr.value = 1
    Config.int_ = 1
    config["int"] = 1


@pytest.fixture
def nil_values() -> None:
    int_ptr.value = cast(int, None)
    Config.int_ = cast(int, None)
    config["int"] = cast(int, None)


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_deref(ptr, int_values) -> None:
    assert ptr.deref() == 1


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_deref_panic(ptr, nil_values) -> None:
    with pytest.raises(Panic):
        ptr.deref()


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_set(ptr, int_values) -> None:
    ptr.set_(2)
    assert ptr.deref() == 2


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_is_nil(ptr, nil_values):
    assert ptr.is_nil()


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_str(ptr, int_values):
    assert str(ptr) == "1"


@pytest.mark.parametrize(
    "ptr,repr_",
    [(int_ptr, "Ptr(1)"), (int_attr, "AttrRef(int_=1)"), (int_key, "KeyRef(int=1)")],
)
def test_repr(ptr, repr_, int_values):
    assert repr(ptr) == repr_


@pytest.mark.parametrize("ptr", [int_ptr, int_attr, int_key])
def test_magic(ptr, int_values) -> None:
    assert ptr + 1 == 2
    assert ptr - 1 == 0
