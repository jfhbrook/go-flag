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

force = flag.bool_("force", False, "force the command to execute")
count = flag.int_("count", 1, "a count")
name = flag.string("name", "Josh", "a name")
threshold = flag.float_("threshold", 1.0, "a threshold")

flag.parse()

print(dict(
    force=force.deref(),
    count=count.deref(),
    name=name.deref(),
    threshold=threshold.deref()
))
```

With no arguments, this will print:

```
$ python examples/simple.py
{'force': False, 'count': 1, 'name': 'Josh', 'threshold': 1.0}
```

With a number of argument, we see:

```
$ python examples/simple.py -count 3 -force=true -name KB -threshold 0.5
{'force': True, 'count': 3, 'name': 'KB', 'threshold': 0.5}
```

With the help flag, this will print:

```
$ python examples/simple.py -h
Usage of examples/simple.py:

  -count int
    	a count (default 1)
  -force
    	force the command to execute
  -name string
    	a name (default Josh)
  -threshold float
    	a threshold (default 1)
```

In this usage, these flags are instances of `flag.Ptr`. But you may want to
be a little more fancy - for instance, using a class and `flag.AttrRef`:

```py
#!/usr/bin/env python

import flag


class Config:
    force: bool = flag.zero.bool_
    count: int = flag.zero.int_
    name: str = flag.zero.string
    threshold: float = flag.zero.float_


force = flag.AttrRef(Config, "force")
count = flag.AttrRef(Config, "count")
name = flag.AttrRef(Config, "name")
threshold = flag.AttrRef(Config, "threshold")

flag.bool_var(force, "force", False, "bool value")
flag.int_var(count, "count", 1, "int value")
flag.string_var(name, "name", "Josh", "string value")
flag.float_var(threshold, "threshold", 1.0, "float value")

flag.parse()

print(
    dict(
        force=Config.force,
        count=Config.count,
        name=Config.name,
        threshold=Config.threshold,
    )
)
```

This outputs:

```
$ python examples/class.py -count 3 -force=true -name KB -threshold 0.5
{'force': True, 'count': 3, 'name': 'KB', 'threshold': 0.5}
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
see if I stick with this stack over time.

Nevertheless, the `justfile` should contain most of what you need - including
`just format`, `just lint`, `just check`, and `just test`. Note that type
checking requires node.js, because I use pyright.

## License

I licensed this under a BSD-3 license, in an attempt to stay compatible with
Go's license.
