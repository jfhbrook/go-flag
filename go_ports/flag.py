"""
A port of go's flag package: https://pkg.go.dev/flag
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import inspect
import sys
from typing import Callable, cast, Dict, IO, List, Optional, Tuple, Type, TypeVar

from go_ports.error import GoError
from go_ports.ptr import Ptr
import go_ports.internal.strconv as strconv
import go_ports.time as time

# HelpError is the error class raised if the -help or -h flag is invoked
# but no such flag is defined.
HelpError = GoError.cls("flag: help requested")

# ParseError is raised by set if a flag's value fails to parse, such as with
# an invalid integer for int. It then gets wrapped through failf to provide
# more information.
ParseError = GoError.cls("parse error")

# RangeError is raised by set if a flag's value is out of range. It then gets
# wrapped through failf to provide more information.
RangeError = GoError.cls("value out of range")

OK = bool


def num_error(exc: Exception) -> GoError:
    if isinstance(exc, strconv.SyntaxError):
        raise ParseError() from exc
    raise exc


Func = Callable[[str]]
ValueType = bool | int | str | float | time.Duration | Func


class Value[V](ABC):
    value: Ptr
    is_bool_flag: bool = False

    def __init__(self, value: V, p: Ptr) -> None:
        p.set(value)
        self.value: Ptr = p

    @abstractmethod
    def string(self) -> str:
        pass

    @abstractmethod
    def get(self) -> V:
        pass

    @abstractmethod
    def set(self, string: str) -> None:
        pass


class BoolValue(Value[bool]):
    def __init__(self, value: bool, p: Ptr) -> None:
        super().__init__(value, p)
        self.is_bool_flag = True

    def set(self, string: str) -> None:
        v: bool = strconv.parse_bool(string)
        self.value.set(v)

    def get(self) -> bool:
        return cast(bool, self.value.deref())

    def string(self) -> str:
        return strconv.format_bool(self.get())


class IntValue(Value[int]):
    def set(self, string: str) -> None:
        try:
            v: int = strconv.parse_int(string)
        except FlagError as exc:
            raise num_error(exc) from exc
        else:
            self.value.set(v)

    def get(self) -> int:
        return cast(int, self.value.deref())

    def string(self) -> str:
        return strconv.itoa(self.get())


class StringValue(Value[str]):
    def set(self, string: str) -> None:
        self.value.set(string)

    def get(self) -> str:
        return cast(str, self.value.deref())

    def string(self) -> str:
        return self.get()


class FloatValue(Value[float]):
    def set(self, string: str) -> None:
        v: float = strconv.parse_float(string, 64)
        self.value.set(v)

    def get(self) -> float:
        return cast(float, self.value.deref())

    def string(self) -> str:
        return strconv.format_float(self.get(), "g", -1, 64)


class DurationValue(Value[time.Duration]):
    def set(self, string: str) -> None:
        v: time.Duration = time.parse_duration(string)
        self.value.set(v)

    def get(self) -> time.Duration:
        return cast(time.Duration, self.value.deref())

    def string(self) -> str:
        return self.get().string()


class FuncValue(Value[Func]):
    def set(self, string: str) -> None:
        self.get()(string)

    def get(self) -> Func:
        return cast(Func, self.value.deref())

    def string(self) -> str:
        return ""


class BoolFuncValue(FuncValue):
    def __init__(self, value: Func, p: Ptr) -> None:
        super().__init__(value, p)
        self.is_bool_flag = True


BaseValue = BoolValue | IntValue | StringValue | FloatValue | DurationValue


class ErrorHandling(Enum):
    ContinueOnError = 0
    ExitOnError = 1
    PanicOnError = 2


class FlagSet:
    usage: Callable[[]]

    def __init__(self, name: str, error_handling: ErrorHandling) -> None:
        self.usage: Callable[[]] = usage
        self._name: str = name
        self._parsed: bool = False
        self._actual: Dict[str, Flag] = {}
        self._formal: Dict[str, Flag] = {}
        self._args: List[str] = []
        self._error_handling = error_handling
        self._output: Optional[IO] = None
        self._undef: Dict[str, str] = {}

    @property
    def output(self) -> IO:
        if not self._output:
            return sys.stderr
        return self._output

    def name(self) -> str:
        return self._name

    def error_handling(self) -> ErrorHandling:
        return self._error_handling

    @output.setter
    def set_output(self, output: IO) -> None:
        self._output = output

    def visit_all(self, fn: Callable[["Flag"]]) -> None:
        for flag in sort_flags(self._formal):
            fn(flag)

    def visit(self, fn: Callable[["Flag"]]) -> None:
        for flag in sort_flags(self._actual):
            fn(flag)

    def lookup(self, name: str) -> "Flag":
        return self._formal[name]

    def set(self, name: str, value: str) -> None:
        try:
            flag = self._formal[name]
        except KeyError:
            # Remember that a flag that isn't defined is being set.
            # We raise an exception in this case, but in addition if
            # subsequently that flag is defined, we want to panic
            # at the definition point.
            # This is a problem which occurs if both the definition
            # and the set call are in init code and for whatever
            # reason the init code changes evaluation order.

            # TODO: This index is probably wrong
            info = inspect.stack()[0]
            self._undef[name] = f"{info.filename}:{info.lineno}"

            raise FlagError(f"No such flag -{name}")
        else:
            flag.value.set(value)
            self._actual[name] = flag

    def is_zero_value(self, flag: "Flag", value: str) -> OK:
        # Build a zero value of the flag's Value type, and see if the
        # result of calling its String method equals the value passed in.
        # This works unless the Value type itself is an interface type.

        # TODO: Depends on interface for Value
        pass

    def unquote_usage(self, flag: "Flag") -> Tuple[str, str]:
        """
        Extracts a back-quoted name from the usage string for a flag and
        returns it and the un-quoted usage. Given "a `name` to show" it
        returns ("name", "a name to show"). If there are no back quotes,
        the name is an educated guess of the type of the flag's value, or the
        empty string if the flag is boolean.
        """

        name: str = ""
        usage: str = flag.usage
        for i, u in enumerate(usage):
            if u == "`":
                for j in range(i + 1, len(usage)):
                    if usage[j] == "`":
                        name = usage[i + 1 : j]
                        usage = usage[:i] + name + usage[j + 1]
                        return (name, usage)
                break
        name = "value"

        fv: BaseValue = flag.value
        if isinstance(fv, BoolValue):
            if fv.is_bool_flag:
                name = ""
        elif isinstance(fv, DurationValue):
            name = "duration"
        elif isinstance(fv, FloatValue):
            name = "float"
        elif isinstance(fv, IntValue):
            name = "int"
        elif isinstance(fv, StringValue):
            name = "string"

        return (name, usage)

    def print_defaults(self) -> None:
        """
        Prints, to standard error unless configured otherwise, the default
        values of all defined command-line flags in the set. See the
        documentation for the global function print_defaults for more
        information.
        """

        ...

    def arg(self, i: int) -> str:
        pass

    def args(self) -> List[str]:
        pass


def visit_all(fn: Callable[["Flag"]]) -> None:
    """
    Visits the command-line flags in lexicographical order, calling fn for
    each. It visits all flags, even those not set.
    """

    command_line.visit_all(fn)


def visit(fn: Callable[["Flag"]]) -> None:
    """
    Visits the command-line flags in lexicographical order, calling fn for
    each. It visits only those flags that have been set.
    """

    command_line.visit(fn)


def lookup(name: str) -> Optional["Flag"]:
    """
    Returns the Flag structure of the named command-line flag, returning None
    if none exists.
    """

    return command_line.lookup(name)


def set_(name: str, value: str) -> None:
    """
    Sets the value of the named command-line flag.
    """

    command_line.set(name, value)


B = TypeVar("B", bound=BaseValue)


@dataclass
class Flag[B]:
    """
    Represents the state of a flag.
    """

    name: str
    usage: str
    value: B
    def_value: str


def sort_flags(flags: Dict[str, Flag]) -> List[Flag]:
    result: List[Flag] = list(flags.values())
    result.sort(key=lambda f: f.name)
    return result


command_line = FlagSet(sys.argv[0], ErrorHandling.ExitOnError)


def usage():
    """
    Prints a usage message documenting all defined command-line flags
    to command_line's output, which by default is sys.stderr.
    """

    print(
        f"""Usage of {sys.argv[0]}:
{print_defaults()}""",
        file=command_line.output,
    )


def arg(i: int) -> Optional[str]:
    """
    Returns the i'th command-line argument. arg(0) is the first remaining
    argument after flags have been processed. Returns None if the requested
    element does not exist.
    """
    return None


def args() -> List[str]:
    """
    Returns the non-flag command-line arguments.
    """
    return []


def bool_(name: str, value: bool, usage: str) -> bool:
    """
    Defines a bool flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """


def bool_func(name: str, usage: str, fn: Callable[[str]]) -> None:
    """
    Defines a flag with the specified name and useage string without requiring
    values. Each time the flag is seen, fn is called with the value of the
    flag. If fn raises an exception, it will be treated as a flag value
    parsing error.
    """

    pass


def timedelta(name: str, value: time.Duration, usage: str) -> time.Duration:
    """
    Defines a duration flag with specified name, default value, and usage
    string. The return value is a go_ports.time.Duration, a subclass of
    datetime.timedelta.
    """
    ...


def float_(name: str, value: float, usage: str) -> float:
    """
    Defines a float flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """
    return 1.2


def func(name: str, usage: str, fn: Callable[[str]]) -> None:
    """
    Defines a flag with the specified name and usage string. Each time the
    flag is seen, fn is called with the value of the flag. If fn raises
    an exception, it will be treated as a flag value parsing error.
    """


def int_(name: str, value: int, usage: str) -> int:
    """
    Defines an int flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """


def n_arg() -> int:
    """
    The number of arguments remaining after flags have been processed.
    """


def n_flag() -> int:
    """
    Returns the number of command-line flags that have been set.
    """


def parse() -> bool:
    """
    Parses the command-line flags from sys.argv[1:]. Must be called after all
    flags are defined and before flags are accessed by the program.
    """


def parsed() -> bool:
    """
    Whether the command-line flags have been parsed.
    """


def print_defaults():
    """
    Prints, to standard error unless configured otherwise, a usage message
    showing the default settings of all defined command-line flags.
    """
    pass


def string(name: str, value: str, usage: str) -> str:
    """
    Defines a string flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """


def unquote_usage(flag: Flag) -> Tuple[str, str]:
    """
    Extracts a back-quoted name from the usage string for a flag and returns
    it and the un-quoted usage.
    """


def var(value: Type[Value], name: str, usage: str) -> None:
    """
    Defines a flag with the specified name and usage string. The type and value
    of the flag are represented by the first argument, of type Value, which
    typically holds a user-defined implementation of Value.
    """
