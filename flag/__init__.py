# Copyright 2024 Josh Holbrook. Licensed BSD - see the LICENSE file for details
# Go's flag package is copyright 2009 The Go Authors.

"""
A port of go's flag package: https://pkg.go.dev/flag

# Usage

Define flags using flag.string, bool_, int_, etc.

This declares an integer flag, -n, stored in the pointer n_flag, with type *int:

	import flag
    n_flag: flag.Pointer[int] = flag.int_("n", 1234, "help message for flag n")

If you like, you can bind the flag to a variable using the var() functions.

    flag_var: flag.Pointer[int] = Ptr()

    flag.int_var(flag_var, "flagname", 1234, "help message for flagname")

Or you can create custom flags that inherit from the Value base class and
couple them to flag parsing. For instance, given an subclass of Value called
MyValue:

	flag.Var[MyValue](MyValue(flag_val), "name", "help message for flagname")

For such flags, the default value is just the initial value of the variable.

After all flags are defined, call

	flag.parse()

to parse the command line into the defined flags.

Unlike in go, all flag values implement the flag.Pointer protocol. If you're
using the flags themselves, they're instances of flag.Ptr; if you bind to
variables, they may be of any implementation of flag.Pointer, including
flag.AttrRef and flag.KeyRef. For more details, check the relevant docstrings.

After parsing, the arguments following the flags are available by calling
flag.args() or individually as flag.arg(i). The arguments are zero-indexed.

# Command line flag syntax

The following forms are permitted:

	-flag
	--flag   # double dashes are also permitted
	-flag=x
	-flag x  # non-boolean flags only

One or two dashes may be used; they are equivalent. The last form is not
permitted for boolean flags because the meaning of the command

	cmd -x *

where * is a Unix shell wildcard, will change if there is a file called 0,
false, etc. You must use the -flag=false form to turn off a boolean flag.

Flag parsing stops just before the first non-flag argument ("-" is a non-flag
argument) or after the terminator "--".

Integer and float flags accept any value which can be parsed by Python and may
be negative. Boolean flags may be:

	1, 0, t, f, T, F, true, false, TRUE, FALSE, True, False

Duration flags are parsed with flag.parse_duration, which is intended to be
compatible with go's time.ParseDuration. Their values are of type
flag.Duration, a subclass of datetime.timedelta which has str() output
intended to be compatible with time.Duration's String method in go. They
may be converted into vanilla datetime.timedelta objects with the
flag.Duration.to_timedelta function.

The default set of command-line flags is controlled by top-level functions.
The FlagSet class allows one to define independent sets of flags, such as to
implement subcommands in a command-line interface. The methods of FlagSet are
analogous to the top-level functions for the command-line flag set.

This package uses two error types: flag.Error and flag.Panic. These are used
to simulate Go's errors and panics, respectively. Note that errors are in
fact raised in this library - but all expected non-panic exceptions raised by
this library should be instances of flag.Error. flag.Panic does not inherit
from flag.Error and must be excepted separately.
"""

from typing import List

from flag.error import Error
from flag.flag import (
    arg,
    args,
    bool_,
    bool_func,
    bool_var,
    command_line,
    duration,
    duration_var,
    ErrorHandling,
    Flag,
    FlagSet,
    float_,
    float_var,
    Func,
    func,
    int_,
    int_var,
    lookup,
)
from flag.flag import (
    parse,
    parsed,
    print_defaults,
    set_,
    string,
    string_var,
    unquote_usage,
    Usage,
    usage,
    Value,
    var,
    visit,
    visit_all,
    Visitor,
)
from flag.flag import n_arg as _n_arg
from flag.flag import n_flag as _n_flag
from flag.panic import Panic
from flag.pointer import AttrRef, KeyRef, Pointer, Ptr
from flag.time import Duration, parse_duration
import flag.zero as zero


def __getattr__(name: str) -> int:
    if name == "n_flag":
        return _n_flag()
    elif name == "n_arg":
        return _n_arg()
    else:
        raise ImportError(f"cannot import name '{name}' from 'flag' ({__file__})")


__all__: List[str] = [
    # flag.error
    "Error",
    # flag.flag
    "Func",
    "Visitor",
    "Usage",
    "Value",
    "ErrorHandling",
    "FlagSet",
    "Flag",
    "visit_all",
    "visit",
    "lookup",
    "set_",
    "unquote_usage",
    "print_defaults",
    "usage",
    "arg",
    "args",
    "bool_var",
    "bool_",
    "int_var",
    "int_",
    "string_var",
    "string",
    "float_var",
    "float_",
    "duration_var",
    "duration",
    "func",
    "bool_func",
    "var",
    "parse",
    "parsed",
    "command_line",
    # flag.panic
    "Panic",
    # flag.pointer
    "AttrRef",
    "KeyRef",
    "Pointer",
    "Ptr",
    # flag.time
    "Duration",
    "parse_duration",
    # flag.zero
    "zero",
    # properties
    "__getattr__",
]
