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

flag.bool_var(force, "force", False, "force the command to execute")
flag.int_var(count, "count", 1, "a count")
flag.string_var(name, "name", "Josh", "a name")
flag.float_var(threshold, "threshold", 1.0, "a threshold")

flag.parse()

print(
    dict(
        force=Config.force,
        count=Config.count,
        name=Config.name,
        threshold=Config.threshold,
    )
)
