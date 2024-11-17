from typing import Any, Dict, List

from flag import (
    bool_,
    int_,
    string,
    float_,
    duration,
    func,
    bool_func,
    Duration,
    Flag,
    visit_all,
    visit,
    set_,
)


def bool_string(s: str) -> str:
    if s == "0":
        return "false"
    return "true"


def is_sorted(xs: List[Any]) -> bool:
    return all(xs[i] <= xs[i+1] for i in range(len(xs) - 1))


def test_everything() -> None:
    bool_("test_bool", False, "bool value")
    int_("test_int", 0, "int value")
    string("test_string", "0", "string value")
    float_("test_float", 0.0, "float value")
    duration("test_duration", Duration(), "Duration value")
    func("test_func", "func value", lambda _: None)
    bool_func("test_boolfunc", "func", lambda _: None)

    m: Dict[str, Flag] = dict()
    desired = "0"
    def visitor(f: Flag) -> None:
        if len(f.name) > 5 and f.name[0:5] == "test_":
            m[f.name] = f
            ok = False
            if str(f.value) == desired:
                ok = True
            elif f.name == "test_bool" and str(f.value) == bool_string(desired):
                ok = True
            elif f.name == "test_duration" and str(f.value) == desired + "s":
                ok = True
            elif f.name == "test_func" and str(f.value) == "":
                ok = True
            elif f.name == "test_boolfunc" and str(f.value) == "":
                ok = True
            assert ok, f"Visit: bad value {str(f.value)} for {f.name}"
    visit_all(visitor)
    assert len(m) == 10, "visit_all does not miss any flags"
    m = dict()
    visit(visitor)
    assert len(m) == 0, "visit does not see unset flags"
    set_("test_bool", "true")
    set_("test_int", "1")
    set_("test_int", "1")
    set_("test_string", "1")
    set_("test_float", "1")
    set_("test_duration", "1s")
    set_("test_func", "1")
    set_("test_boolfunc", "")
    desired = "1"
    visit(visitor)
    assert len(m) == 10, "visit succeeds after set"
    flag_names: List[str] = []
    visit(lambda f: flag_names.append(f.name))
    assert is_sorted(flag_names), f"flag names are sorted: {flag_names}"


def test_get() -> None:
    NotImplemented("test_get")


def _test_parse() -> None:
    NotImplemented("_test_parse")


def test_parse() -> None:
