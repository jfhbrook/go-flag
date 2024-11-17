# go-flag

go-flag is a port of [Go's flag package](https://pkg.go.dev/flag) to Python.

## Why??

Typically, [click](https://click.palletsprojects.com/en/stable/) or
[argparse](https://docs.python.org/3/library/argparse.html) are going to be
more straightforward than using this library. But there are a few motivations
for using go-flag:

1. You want to write a tool in Python, which behaves like a Go program. If
   you are using it alongside other programs that use Go-style flags, it can
   make your tool feel more at home in that ecosystem.
2. You're a Gopher, and want to write some Python. In that case, this library
   may feel more comfortable.
3. You are porting a Go program. This library can help minimize the amount of
   effort involved in translating idioms.

Also, I think this is funny.

## Usage

The simplest usage of this library involves defining some flags and running
a parse:

```py
#!/usr/bin/env python

import flag

bool_flag = flag.bool_("bool", False, "bool value")
int_flag = flag.int_("int", 0, "int value")
string_flag = flag.string("string", "0", "string value")
float_flag = flag.float_("float", 0.0, "float value")

flag.parse()

print("bool", bool_flag.deref())
print("int", int_flag.deref())
print("string", string_flag.deref())
print("float", float_flag.deref())
```

With no arguments, this will print:

```
bool False
int 0
string 0
float 0.0
```

With the help flag, this will print:

```
Usage of simple.py:

  -bool
    	bool value
  -float float
    	float value
  -int int
    	int value
  -string string
    	string value (default 0)
```

In this usage, these flags are instances of `flag.Ptr`. But you may want to
be a little more fancy - for instance, using a dataclass and `flag.AttrRef`:

```py
#!/usr/bin/env python

from dataclasses import dataclass

import flag


@dataclass
class Config:
    bool_: bool = False
    int_: int = 0
    string: str = "0"
    float_: float = 0.0


config = Config()

flag.bool_var(flag.AttrRef(config, "bool_"), "bool", config.bool_, "bool value")
flag.int_var(flag.AttrRef(config, "int_"), "int", config.int_, "int value")
flag.string_var(flag.AttrRef(config, "string"), "string", config.string, "string value")
flag.float_var(flag.AttrRef(config, "string"), "float", config.float_, "float value")

flag.parse()

print(config)
```

With no arguments, this outputs:

```
Config(bool_=False, int_=0, string=0.0, float_=0.0)
```

The `flag.KeyRef` class can implement a similar pattern with dicts.

In general, aside from the need to use classes that fake pointers and a number
of data types not applicable to Python, the API should follow the same general
shape as Go's flag package. For more documentation, read the source - the
docstrings should be *relatively* complete.

## Error Handling

We already saw one strange set of abstractions we needed to pretend to be
Go - the `Pointer` protocol and its implementations. The other way in which
this library emulates Go is in its error handling.

Not to worry - this library raises Exceptions like God intended. But it *does*
have two non-overlapping classes of errors: `flag.Error` and `flag.Panic`. The
former emulates cases where Go would have us return an `error`. The latter is
raised when emulating a Go panic.

While the internal details of how `Error`s are created are unusual, the end
result is very simple error classes. In general, you can except on `flag.Error`
and allow raised instances of `flag.Panic` to crash the program. But if you
wish to have more fine-grained control, you may with to except `flag.Panic` as
well.

## Development

I developed this project using [uv](https://docs.astral.sh/uv/). It is a little
immature, and I honestly can't recommend it yet for production use. We will
see if I stick with this stack when I attempt to publish to PyPI.

Nevertheless, the `justfile` should contain most of what you need - including
`just format`, `just lint`, `just check`, and `just test`. Note that type
checking requires node.js, because I use pyright.

## License

I licensed this under a BSD-3 license, in an attempt to stay compatible with
Go's license.
