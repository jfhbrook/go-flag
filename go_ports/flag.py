"""
A port of go's flag package: https://pkg.go.dev/flag
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import inspect
import sys
from typing import Callable, Dict, IO, List, Optional, Tuple, Type

from go_ports.error import Error
from go_ports.fmt import errorf
from go_ports.ptr import Ptr
import go_ports.strconv as strconv
import go_ports.time as time

# HelpError is the error class raised if the -help or -h flag is invoked
# but no such flag is defined.
HelpError = Error.from_string("flag: help requested")

# ParseError is raised by set if a flag's value fails to parse, such as with
# an invalid integer for int. It then gets wrapped through failf to provide
# more information.
ParseError = Error.from_string("parse error")

# RangeError is raised by set if a flag's value is out of range. It then gets
# wrapped through failf to provide more information.
RangeError = Error.from_string("value out of range")


def num_error(exc: Exception) -> Error:
    if isinstance(exc, strconv.SyntaxError):
        raise ParseError() from exc
    raise exc


Func = Callable[[str]]
ValueType = bool | int | str | float | time.Duration | Func


# Value is a class wrapping the dynamic value stored in a flag.
#
# If a Value's is_bool_flag() method returns True, the command-line parser
# makes -name equivalend to -name=true rather than using the next command-line
# argument.
#
# set is called once, in command line order, for each flag present. The flag
# module may call str() with a zero-valued object, such as a nil pointer.
class Value[V](ABC):
    is_bool_flag: bool = False

    def __init__(self, value: V, p: Ptr[V]) -> None:
        p.set(value)
        self.value: Ptr[V] = p

    def get(self) -> V:
        return self.value.deref()

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

    def __str__(self) -> str:
        return strconv.format_bool(self.get())


class IntValue(Value[int]):
    def set(self, string: str) -> None:
        try:
            v: int = strconv.parse_int(string)
        except Error as exc:
            raise num_error(exc) from exc
        else:
            self.value.set(v)

    def __str__(self) -> str:
        return strconv.itoa(self.get())


class StringValue(Value[str]):
    def set(self, string: str) -> None:
        self.value.set(string)

    def __str__(self) -> str:
        return self.get()


class FloatValue(Value[float]):
    def set(self, string: str) -> None:
        v: float = strconv.parse_float(string, 64)
        self.value.set(v)

    def __str__(self) -> str:
        return strconv.format_float(self.get(), "g", -1, 64)


class DurationValue(Value[time.Duration]):
    def set(self, string: str) -> None:
        v: time.Duration = time.parse_duration(string)
        self.value.set(v)

    def __str__(self) -> str:
        return str(self.value.deref())


# NOTE: Go implements a text value type, which can use its
# encoding.TextUnmarshaler interface to apply text encodings to raw bytes.
# This seems like a niche use case, though it's not out of the realm of
# implementing something analogous - Python has byte encodings as well.


class FuncValue(Value[Func]):
    def set(self, string: str) -> None:
        self.get()(string)

    def __str__(self) -> str:
        return ""


class BoolFuncValue(FuncValue):
    def __init__(self, value: Func, p: Ptr[Func]) -> None:
        super().__init__(value, p)
        self.is_bool_flag = True


class ErrorHandling(Enum):
    ContinueOnError = 0
    ExitOnError = 1
    PanicOnError = 2


class FlagSet:
    def __init__(self, name: str, error_handling: ErrorHandling) -> None:
        self.usage: Callable[[]] = usage
        # NOTE: In cases where go has defined private struct members and
        # public getters, I've opted to expose the properties as public.
        self.name: str = name
        self._parsed: bool = False
        self._actual: Dict[str, Flag] = {}
        self._formal: Dict[str, Flag] = {}
        self.args: List[str] = []
        self.error_handling = error_handling
        self._output: Optional[IO] = None
        self._undef: Dict[str, str] = {}

    # NOTE: In go, these methods are defined inline with other functions.
    # Because we need to define them with the class, definitions will be a
    # little out of order as compared to go.

    @property
    def output(self) -> IO:
        if not self._output:
            return sys.stderr
        return self._output

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

            raise errorf(f"No such flag -{name}")
        else:
            flag.value.set(value)
            self._actual[name] = flag

    def print_defaults(self) -> None:
        """
        Prints, to standard error unless configured otherwise, the default
        values of all defined command-line flags in the set. See the
        documentation for the global function print_defaults for more
        information.
        """

        raise NotImplementedError("FlagSet#print_defaults")

    def default_usage(self) -> None:
        if self.name == "":
            print("Usage:\n", file=self.output)
        else:
            print(f"Usage of {self.name}:\n", file=self.output)
        self.print_defaults()

    def n_flag(self) -> int:
        """
        Returns the number of flags that have been set.
        """
        return len(self._actual)

    def arg(self, i: int) -> Optional[str]:
        """
        Returns the i'th argument. flag_set.arg(0) is the first remaining
        argument after flags have been processed. arg returns None if the
        requested element does not exist.
        """
        if i < 0 or i >= len(self.args):
            return None
        return self.args[i]

    def n_arg(self) -> int:
        """
        The number of arguments remaining after flags have been processed.
        """
        return len(self.args)

    def bool_var(self, p: Ptr[bool], name: str, value: bool, usage: str) -> None:
        """
        Defines a bool flag with specified name, default value, and usage
        string. The argument p points to a bool variable in which to store
        the value of the flag.
        """
        self.var(BoolValue(value, p), name, usage)

    def bool(self, name: str, value: bool, usage: str) -> bool:
        """
        Defines a bool flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.bool_var(p, name, value, usage)
        return p.deref()

    def int_var(self, p: Ptr[int], name: str, value: int, usage: str) -> None:
        """
        Defines an int flag with specified name, default value, and usage
        string. The argument p points to an int in which to store the value
        of the flag.
        """
        self.var(IntValue(value, p), name, usage)

    def int(self, name: str, value: int, usage: str) -> int:
        """
        Defines an int flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.int_var(p, name, value, usage)
        return p.deref()

    def string_var(self, p: Ptr, name: str, value: str, usage: str) -> None:
        """
        Defines a string flag with specified name, default value, and usage
        string. The argument p points to a string in which to store the value
        of the flag.
        """

        self.var(StringValue(value, p), name, usage)

    def string(self, name: str, value: str, usage: str) -> str:
        """
        Defines a string flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.string_var(p, name, value, usage)
        return p.deref()

    def float_var(self, p: Ptr[float], name: str, value: float, usage: str) -> None:
        """
        Defines a float flag with specified name, default value, and usage
        float. The argument p points to a float in which to store the value
        of the flag.
        """

        self.var(FloatValue(value, p), name, usage)

    def float(self, name: str, value: float, usage: str) -> float:
        """
        Defines a float flag with specified name, default value, and usage
        float. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.float_var(p, name, value, usage)
        return p.deref()


# BOOKMARK

@dataclass
class Flag:
    """
    Represents the state of a flag.
    """

    name: str
    usage: str
    value: Value
    def_value: str


# Returns the flags as a slice in lexicographical sorted order.
def sort_flags(flags: Dict[str, Flag]) -> List[Flag]:
    result: List[Flag] = list(flags.values())
    result.sort(key=lambda f: f.name)
    return result


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


def is_zero_value(flag: "Flag", value: str) -> bool:
    """
    Determines whether the string represents the zero value for a flag.

    In go, this function uses the reflect package to look up the type of
    the flag's value (which is a normal value with an additional interface),
    construct a zero value for that type, convert it to a string and compare to
    the string value. This package is very specific to go and its data types.

    Instead, we check the instance type of flag.value (which is a subclass
    of Value). This means the function is much less sophisticated. But it
    should suffice for our needs.
    """

    if isinstance(flag.value, BoolValue):
        return value == "false"
    elif isinstance(flag.value, IntValue):
        return value == "0"
    elif isinstance(flag.value, FloatValue):
        return value == "0.0"
    elif isinstance(flag.value, StringValue):
        return value == ""
    elif isinstance(flag.value, DurationValue):
        return value == str(time.Duration())
    else:
        raise errorf("can not construct zero {t} for flag {f}", t=type(flag.value.get()), f=flag.name)


def unquote_usage(flag: "Flag") -> Tuple[str, str]:
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

    fv: Value = flag.value
    if isinstance(fv, BoolValue):
        # TODO: when would this be false?
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


def print_defaults() -> None:
    """
    Prints, to standard error unless configured otherwise, a usage message
    showing the default settings of all defined command-line flags.

    TODO: Fill this out
    """
    command_line.print_defaults()


# NOTE: usage is not just command_line.default_usage() because it serves
# as the example for how to write your own usage function.
def usage() -> None:
    """
    Prints a usage message documenting all defined command-line flags
    to command_line's output, which by default is sys.stderr.
    """

    print(f"Usage of {sys.argv[0]}:\n", file=command_line.output)
    print_defaults()


def n_flag() -> int:
    """
    Returns the number of command-line flags that have been set.
    """

    return len(command_line._actual)


def arg(i: int) -> Optional[str]:
    """
    Returns the i'th command-line argument. arg(0) is the first remaining
    argument after flags have been processed. Returns None if the requested
    element does not exist.
    """
    return command_line.arg(i)


def n_arg() -> int:
    """
    The number of arguments remaining after flags have been processed.
    """
    return len(command_line.args)


def args() -> List[str]:
    """
    Returns the non-flag command-line arguments.
    """
    return command_line.args


def bool_var(p: Ptr[bool], name: str, value: bool, usage: str) -> None:
    """
    Defines a bool flag with specified name, default value, and usage string.
    The argument p points to a bool variable in which to store the value of
    the flag.
    """
    command_line.var(BoolValue(value, p), name, usage)


def bool_(name: str, value: bool, usage: str) -> bool:
    """
    Defines a bool flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.bool(name, value, usage)


def int_var(p: Ptr[int], name: str, value: int, usage: str) -> None:
    """
    Defines an int flag with specified name, default value, and usage
    string. The argument p points to an int in which to store the value of
    the flag.
    """
    command_line.var(IntValue(value, p), name, usage)


def int_(name: str, value: int, usage: str) -> bool:
    """
    Defines an int flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.int(name, value, usage)

def string_var(p: Ptr[str], name: str, value: str, usage: str) -> None:
    """
    Defines a string flag with specified name, default value, and usage
    string. The argument p points to a string in which to store the value of
    the flag.
    """
    command_line.var(StringValue(value, p), name, usage)

def string(name: str, value: str, usage: str) -> str:
    """
    Defines a string flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """
    return command_line.string(name, value, usage)


def float_var(p: Ptr[float], name: str, value: float, usage: str) -> None:
    """
    Defines a float flag with specified name, default value, and usage
    string. The argument p pofloats to a float in which to store the value of
    the flag.
    """
    command_line.var(IntValue(value, p), name, usage)


def float_(name: str, value: float, usage: str) -> float:
    """
    Defines a float flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.float(name, value, usage)


# BOOKMARK

def duration(name: str, value: time.Duration, usage: str) -> time.Duration:
    """
    Defines a duration flag with specified name, default value, and usage
    string. The return value is a go_ports.time.Duration, a subclass of
    datetime.timedelta.
    """
    ...





command_line = FlagSet(sys.argv[0], ErrorHandling.ExitOnError)




def bool_func(name: str, usage: str, fn: Callable[[str]]) -> None:
    """
    Defines a flag with the specified name and useage string without requiring
    values. Each time the flag is seen, fn is called with the value of the
    flag. If fn raises an exception, it will be treated as a flag value
    parsing error.
    """

    pass


def func(name: str, usage: str, fn: Callable[[str]]) -> None:
    """
    Defines a flag with the specified name and usage string. Each time the
    flag is seen, fn is called with the value of the flag. If fn raises
    an exception, it will be treated as a flag value parsing error.
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


def var(value: Type[Value], name: str, usage: str) -> None:
    """
    Defines a flag with the specified name and usage string. The type and value
    of the flag are represented by the first argument, of type Value, which
    typically holds a user-defined implementation of Value.
    """
