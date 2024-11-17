from typing import Any, Dict, List

import pytest

from flag import (
    bool_,
    bool_func,
    duration,
    Duration,
    Error,
    ErrorHandling,
    Flag,
    FlagSet,
    float_,
    func,
    int_,
    set_,
    string,
    visit,
    visit_all,
)


def bool_string(s: str) -> str:
    if s == "0":
        return "false"
    return "true"


def is_sorted(xs: List[Any]) -> bool:
    return all(xs[i] <= xs[i + 1] for i in range(len(xs) - 1))


def test_everything(command_line, usage) -> None:
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
    assert len(m) == 7, "visit_all does not miss any flags"
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
    assert len(m) == 7, "visit succeeds after set"
    flag_names: List[str] = []
    visit(lambda f: flag_names.append(f.name))
    assert is_sorted(flag_names), f"flag names are sorted: {flag_names}"


def test_get(command_line, usage) -> None:
    bool_("test_bool", True, "bool value")
    int_("test_int", 1, "int value")
    string("test_string", "5", "string value")
    float_("test_float", 6.0, "float value")
    duration("test_duration", Duration(seconds=7), "Duration value")

    def visitor(f: Flag) -> None:
        if len(f.name) > 5 and f.name[0:5] == "test_":
            v = f.value
            ok: bool = False
            if f.name == "test_bool":
                ok = v.get() == True
            elif f.name == "test_int":
                ok = v.get() == 1
            elif f.name == "test_string":
                ok = v.get() == "5"
            elif f.name == "test_float":
                ok = v.get() == 6.0
            elif f.name == "test_duration":
                ok = v.get() == Duration(seconds=7)
            assert ok, "visit: bad value at {v.get()} for {f.name}"

    visit_all(visitor)


def test_usage(command_line, usage) -> None:
    with pytest.raises(Error):
        command_line.parse(["-x"])
    usage.assert_called_once()


def _test_parse(f: FlagSet) -> None:
    assert not f.parsed, "f.parse should be false before parse"
    # TODO: These need to return pointers laul
    bool_flag = f.bool("bool", False, "bool value")
    bool2_flag = f.bool("bool2", False, "bool2 value")
    int_flag = f.int("int", 0, "int value")
    string_flag = f.string("string", "0", "string value")
    float_flag = f.float("float", 0.0, "float value")
    duration_flag = f.duration("duration", Duration(seconds=5), "time.Duration value")
    extra = "one-extra-argument"
    args: List[str] = [
        "-bool",
        "-bool2=true",
        "--int",
        "22",
        "-string",
        "hello",
        "-float",
        "2718e28",
        "-duration",
        "2m",
        extra,
    ]
    f.parse(args)
    assert f.parsed, "f.parse should be true after parse"
    assert bool_flag.deref() == True, "bool flag should be true"
    assert bool2_flag.deref() == True, "bool2 flag should be true"
    assert int_flag.deref() == 22, "int flag should be 22"
    assert string_flag.deref() == "hello", "string flag should be `hello`"
    assert float_flag.deref() == 2718e28, "float flag should be 2718e28"
    assert duration_flag.deref() == Duration(minutes=2), "duration flag should be 2m"
    assert len(f.args) == 1, "expected one argument"
    assert f.args[0] == extra, f"expected argument {extra}"


@pytest.mark.skip
def test_parse(command_line, usage) -> None:
    usage.side_effect = Error.from_string("bad parse")
    _test_parse(command_line)


def test_flag_set_parse() -> None:
    _test_parse(FlagSet("test", ErrorHandling.ContinueOnError))
