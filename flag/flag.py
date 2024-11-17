"""
A port of go's flag package: https://pkg.go.dev/flag
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import datetime
from enum import Enum
import inspect
import sys
from typing import Any, Callable, Dict, IO, List, NoReturn, Optional, Tuple

from flag.error import Error
from flag.fmt import errorf
from flag.panic import panic, Panic
from flag.pointer import Pointer, Ptr
import flag.strconv as strconv
import flag.time as time

# HelpError is the error class raised if the -help or -h flag is invoked
# but no such flag is defined.
HelpError = Error.from_string("flag: help requested")

# ParseError is raised by set if a flag's value fails to parse, such as with
# an invalid integer for int. It then gets wrapped through failf to provide
# more information.
ParseError = Error.from_string("parse error")

Func = Callable[[str], None]
Visitor = Callable[["Flag"], None]
Usage = Callable[[], None]


def set_value(self: "Value", value: str) -> None:
    """
    Set a value, reifying ValueErrors into flag Errors.
    """
    try:
        self.set(value)
    except ValueError as exc:
        raise ParseError from exc


class Value[T](ABC):
    """
    Value is a class wrapping the dynamic value stored in a flag.

    If a value's is_bool_flag property returns True, the command-line parser
    makes -name equivalent to -name=true rather than using the next
    command-line argument.

    set is called once, in command line order, for each flag present. The
    flag module may call str() with a zero-valued object, such as a nil
    pointer.
    """

    is_bool_flag: bool = False

    def __init__(self, value: T, p: Pointer[T]) -> None:
        p.set(value)
        self.value: Pointer[T] = p

    def get(self) -> T:
        return self.value.deref()

    @abstractmethod
    def set(self, string: str) -> None:
        pass

    def zero(self) -> str:
        panic("can not construct zero")

    def __str__(self) -> str:
        return str(self.get())


class BoolValue(Value[bool]):
    def __init__(self, value: bool, p: Pointer) -> None:
        super().__init__(value, p)
        self.is_bool_flag = True

    def set(self, string: str) -> None:
        v: bool = strconv.parse_bool(string)
        self.value.set(v)

    def zero(self) -> str:
        return "false"

    def __str__(self) -> str:
        return strconv.format_bool(self.get())


class IntValue(Value[int]):
    def set(self, string: str) -> None:
        v: int = int(string)
        self.value.set(v)

    def zero(self) -> str:
        return "0"


class StringValue(Value[str]):
    def set(self, string: str) -> None:
        self.value.set(string)

    def zero(self) -> str:
        return ""


class FloatValue(Value[float]):
    def set(self, string: str) -> None:
        v: float = float(string)
        self.value.set(v)

    def zero(self) -> str:
        return "0"

    def __str__(self) -> str:
        return strconv.format_float(self.get())


class DurationValue(Value[datetime.timedelta]):
    def set(self, string: str) -> None:
        v: datetime.timedelta = time.parse_duration(string)
        self.value.set(v)

    def zero(self) -> str:
        return str(time.Duration())


# NOTE: Go implements a text value type, which can use its
# encoding.TextUnmarshaler interface to apply text encodings to raw bytes.
# This seems like a niche use case, though it's not out of the realm of
# implementing something analogous - Python has byte encodings as well.


class FuncValue(Value[Func]):
    def __init__(self, value: Func) -> None:
        # In go, functions are treated as pointers
        self.value = Ptr(value)

    def set(self, string: str) -> None:
        fn = self.get()
        fn(string)

    def __str__(self) -> str:
        return ""


class BoolFuncValue(FuncValue):
    def __init__(self, value: Func) -> None:
        super().__init__(value)
        self.is_bool_flag = True


class ErrorHandling(Enum):
    RaiseOnError = 0
    ExitOnError = 1
    PanicOnError = 2


class FlagSet:
    def __init__(self, name: str, error_handling: ErrorHandling) -> None:
        self.usage: Usage = usage
        # NOTE: In cases where go has defined private struct members and
        # public getters, I've opted to expose the properties as public.
        self.name: str = name
        self.parsed: bool = False
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
    def output(self, output: IO) -> None:
        self._output = output

    def visit_all(self, fn: Visitor) -> None:
        for flag in sort_flags(self._formal):
            fn(flag)

    def visit(self, fn: Visitor) -> None:
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
            set_value(flag.value, value)
            self._actual[name] = flag

    def print_defaults(self) -> None:
        """
        Prints, to standard error unless configured otherwise, the default
        values of all defined command-line flags in the set. See the
        documentation for the global function print_defaults for more
        information.
        """

        is_zero_value_errs: List[Error] = []

        def visitor(flag: Flag) -> None:
            b: List[str] = []
            b += f"  s{flag.name}"
            name, usage = unquote_usage(flag)
            if name:
                b += " "
                b += name
            # Boolean flags of one ASCII letter are so common we treat them
            # specially, putting their usage on the same line
            if len(b) <= 4:
                # space, '-', 'x'.
                b += "\t"
            else:
                # Four spaces before the tab triggers good alignment for both
                # 4- and 8-space tab stops.
                b += "\n    \t"
            b += usage.replace("\n", "\n    \t")

            # Print the default value only if it differs from the zero value
            # for this flag type.
            try:
                is_zero = is_zero_value(flag, flag.def_value)
            except Error as exc:
                is_zero_value_errs.append(exc)
            else:
                if not is_zero:
                    b += f" (default {flag.def_value}"
            print("".join(b), file=self.output)

        if is_zero_value_errs:
            print("\n", file=self.output)
            for exc in is_zero_value_errs:
                print(str(exc), file=self.output)

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

    def bool_var(self, p: Pointer[bool], name: str, value: bool, usage: str) -> None:
        """
        Defines a bool flag with specified name, default value, and usage
        string. The argument p points to a bool variable in which to store
        the value of the flag.
        """
        self.var(BoolValue(value, p), name, usage)

    def bool_(self, name: str, value: bool, usage: str) -> Pointer[bool]:
        """
        Defines a bool flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.bool_var(p, name, value, usage)
        return p

    def int_var(self, p: Pointer[int], name: str, value: int, usage: str) -> None:
        """
        Defines an int flag with specified name, default value, and usage
        string. The argument p points to an int in which to store the value
        of the flag.
        """
        self.var(IntValue(value, p), name, usage)

    def int(self, name: str, value: int, usage: str) -> Pointer[int]:
        """
        Defines an int flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.int_var(p, name, value, usage)
        return p

    def string_var(self, p: Pointer, name: str, value: str, usage: str) -> None:
        """
        Defines a string flag with specified name, default value, and usage
        string. The argument p points to a string in which to store the value
        of the flag.
        """

        self.var(StringValue(value, p), name, usage)

    def string(self, name: str, value: str, usage: str) -> Pointer[str]:
        """
        Defines a string flag with specified name, default value, and usage
        string. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.string_var(p, name, value, usage)
        return p

    def float_var(self, p: Pointer[float], name: str, value: float, usage: str) -> None:
        """
        Defines a float flag with specified name, default value, and usage
        float. The argument p points to a float in which to store the value
        of the flag.
        """

        self.var(FloatValue(value, p), name, usage)

    def float(self, name: str, value: float, usage: str) -> Pointer[float]:
        """
        Defines a float flag with specified name, default value, and usage
        float. The return value is the value of the flag.
        """
        p = Ptr(value)
        self.float_var(p, name, value, usage)
        return p

    def duration_var(
        self,
        p: Pointer[datetime.timedelta],
        name: str,
        value: datetime.timedelta,
        usage: str,
    ) -> None:
        """
        Defines a duration flag with specified name, default value, and usage
        string. The argument p podurations to a float in which to store the value of
        the flag.
        """

        self.var(DurationValue(value, p), name, usage)

    def duration(
        self, name: str, value: datetime.timedelta, usage: str
    ) -> Pointer[datetime.timedelta]:
        """
        Defines a duration flag with specified name, default value, and usage
        string. The return value is a go_ports.time.Duration, a subclass of
        datetime.timedelta.
        """
        p = Ptr(value)
        self.duration_var(p, name, value, usage)
        return p

    def func(self, name: str, usage: str, fn: Func) -> None:
        """
        Defines a flag with the specified name and usage string. Each time the
        flag is seen, fn is called with the value of the flag. If fn raises
        an exception, it will be treated as a flag value parsing error.
        """
        self.var(FuncValue(fn), name, usage)

    def bool_func(self, name: str, usage: str, fn: Func) -> None:
        """
        Defines a flag with the specified name and usage string without requiring
        values. Each time the flag is seen, fn is called with the value of the
        flag. If fn raises an exception, it will be treated as a flag value parsing
        error.
        """
        self.var(FuncValue(fn), name, usage)

    def var(self, value: Value, name: str, usage: str) -> None:
        """
        Defines a flag with the specified name and usage string. The type and
        value of the flag are represented by the first argument, of type
        Value, which typically holds a user-defined implementation of Value.
        For instance, the caller could create a flag that turns a
        comma-separated string into a list of string by implementing a
        subclass of Value; in particular, Value#set would decompose the
        comma-separated string into the slice.
        """

        # Flag must not begin with "-" or contain "=".
        if name.startswith("-"):
            panic(f"flag {name} begins with -")
        elif "=" in name:
            panic(f"flag {name} contains =")

        flag = Flag(name, usage, value, str(value))
        if name in self._formal:
            if self.name == "":
                msg = f"flag redefined: {name}"
            else:
                msg = f"{self.name} flag redefined: {name}"
            panic(msg)
        pos = self._undef.get(name, "")
        if pos != "":
            panic(f"flag {name} set at {pos} before being defined")
        self._formal[name] = flag

    # Formats the message, prints it to output, and returns it
    def sprintf(self, format_: str, *args: Any, **kwargs: Any) -> str:
        msg = format_.format(*args, **kwargs)
        print(msg, file=self.output)
        return msg

    # Prints to standard error a formatted error and usage message, and
    # raises the error.
    def failf(self, format_: str, *args: Any, **kwargs: Any) -> NoReturn:
        msg = format_.format(*args, **kwargs)
        self.usage()
        raise Error(msg)

    def parse_one(self) -> bool:
        if not self.args:
            return False
        s = self.args[0]
        if len(s) < 2 or s[0] != "-":
            return False
        num_minuses = 1
        if s[1] == "-":
            num_minuses += 1
            if len(s) == 2:
                self.args = self.args[1:]
                return False
        name = s[num_minuses:]
        if not name or name[0] == "-" or name[0] == "=":
            self.failf("bad flag syntax: {arg}", arg=s)
        self.args = self.args[1:]
        has_value = False
        value = ""
        for i in range(len(name)):
            if name[i] == "=":
                value = name[i + 1 :]
                has_value = True
                name = name[0:i]
                break
        if name not in self._formal:
            # special case for nice help message.
            if name == "help" or name == "h":
                self.usage()
                raise HelpError()
            self.failf("flag provided but not defined: -{name}", name=name)

        flag = self._formal[name]

        # special case: doesn't need an arg
        if flag.value.is_bool_flag:
            if has_value:
                try:
                    set_value(flag.value, value)
                except Error as exc:
                    self.failf(
                        "invalid boolean value {value} for -{name}: {exc}",
                        value=value,
                        name=name,
                        exc=exc,
                    )
            else:
                try:
                    set_value(flag.value, "true")
                except Error as exc:
                    self.failf(
                        "invalid boolean flag {name}: {value}", name=name, value=value
                    )
        else:
            # It must have a value, which might be the next argument.
            if not has_value and self.args:
                has_value = True
                value = self.args[0]
                self.args = self.args[1:]
            if not has_value:
                self.failf("flag needs an argument: -{name}", name=name)
            try:
                set_value(flag.value, value)
            except Error as exc:
                self.failf(
                    "invalid value {value} for flag -{name}: {exc}",
                    value=value,
                    name=name,
                    exc=exc,
                )
        self._actual[name] = flag
        return True

    def parse(self, arguments: List[str]) -> None:
        self.parsed = True
        self.args = arguments
        while True:
            try:
                seen: bool = self.parse_one()
                if seen:
                    continue
                break
            except Error as exc:
                if self.error_handling == ErrorHandling.RaiseOnError:
                    raise exc
                elif self.error_handling == ErrorHandling.ExitOnError:
                    if isinstance(exc, HelpError):
                        sys.exit(0)
                    sys.exit(2)
                else:
                    # TODO: Allow panic to take an exception
                    panic(str(exc))


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


def visit_all(fn: Visitor) -> None:
    """
    Visits the command-line flags in lexicographical order, calling fn for
    each. It visits all flags, even those not set.
    """

    command_line.visit_all(fn)


def visit(fn: Visitor) -> None:
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
    the flag's value (which is a pointer to a normal value with an additional
    interface), construct a "zero value" for that type (one that's
    uninitialized), convert it to a string and compare to the value. This
    strategy is very specific to go and its data types.

    Here, we require that the Value type implements a zero() method which
    returns the string representation of a zero value.
    """

    try:
        return value == flag.value.zero()
    except Panic as exc:
        raise errorf(
            "panic constructing zero {typ} for flag {name}",
            typ=type(flag.value),
            name=flag.name,
        ) from exc


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


def bool_var(p: Pointer[bool], name: str, value: bool, usage: str) -> None:
    """
    Defines a bool flag with specified name, default value, and usage string.
    The argument p points to a bool variable in which to store the value of
    the flag.
    """
    command_line.var(BoolValue(value, p), name, usage)


def bool_(name: str, value: bool, usage: str) -> Pointer[bool]:
    """
    Defines a bool flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.bool_(name, value, usage)


def int_var(p: Pointer[int], name: str, value: int, usage: str) -> None:
    """
    Defines an int flag with specified name, default value, and usage
    string. The argument p points to an int in which to store the value of
    the flag.
    """
    command_line.var(IntValue(value, p), name, usage)


def int_(name: str, value: int, usage: str) -> Pointer[int]:
    """
    Defines an int flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.int(name, value, usage)


def string_var(p: Pointer[str], name: str, value: str, usage: str) -> None:
    """
    Defines a string flag with specified name, default value, and usage
    string. The argument p points to a string in which to store the value of
    the flag.
    """
    command_line.var(StringValue(value, p), name, usage)


def string(name: str, value: str, usage: str) -> Pointer[str]:
    """
    Defines a string flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """
    return command_line.string(name, value, usage)


def float_var(p: Pointer[float], name: str, value: float, usage: str) -> None:
    """
    Defines a float flag with specified name, default value, and usage
    string. The argument p pofloats to a float in which to store the value of
    the flag.
    """
    command_line.var(FloatValue(value, p), name, usage)


def float_(name: str, value: float, usage: str) -> Pointer[float]:
    """
    Defines a float flag with the specified name, default value, and usage
    string. The return value is the value of the flag.
    """

    return command_line.float(name, value, usage)


def duration_var(
    p: Pointer[datetime.timedelta], name: str, value: datetime.timedelta, usage: str
) -> None:
    """
    Defines a duration flag with specified name, default value, and usage
    string. The argument p podurations to a float in which to store the value of
    the flag.
    """
    command_line.var(DurationValue(value, p), name, usage)


def duration(
    name: str, value: datetime.timedelta, usage: str
) -> Pointer[datetime.timedelta]:
    """
    Defines a duration flag with specified name, default value, and usage
    string. The return value is pointer to a datetime.timedelta.
    """
    return command_line.duration(name, value, usage)


def func(name: str, usage: str, fn: Func) -> None:
    """
    Defines a flag with the specified name and usage string. Each time the
    flag is seen, fn is called with the value of the flag. If fn raises
    an exception, it will be treated as a flag value parsing error.
    """
    return command_line.func(name, usage, fn)


def bool_func(name: str, usage: str, fn: Func) -> None:
    """
    Defines a flag with the specified name and usage string without requiring
    values. Each time the flag is seen, fn is called with the value of the
    flag. If fn raises an exception, it will be treated as a flag value parsing
    error.
    """
    return command_line.bool_func(name, usage, fn)


# TODO: generic type
def var(value: Value, name: str, usage: str) -> None:
    """
    Defines a flag with the specified name and usage string. The type and value
    of the flag are represented by the first argument, of type Value, which
    typically holds a user-defined implementation of Value.
    """
    command_line.var(value, name, usage)


def parse() -> None:
    """
    Parses the command-line flags from sys.argv[1:]. Must be called after all
    flags are defined and before flags are accessed by the program.
    """
    command_line.parse(sys.argv[1:])


def parsed() -> bool:
    """
    Whether the command-line flags have been parsed.
    """
    raise NotImplementedError("parsed")


command_line = FlagSet(sys.argv[0], ErrorHandling.ExitOnError)


def init() -> None:
    global command_line
    if not sys.argv:
        command_line = FlagSet("", ErrorHandling.ExitOnError)
    else:
        command_line = FlagSet(sys.argv[0], ErrorHandling.ExitOnError)
    command_line.usage = command_line_usage


command_line_usage = usage
