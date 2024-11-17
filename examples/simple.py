#!/usr/bin/env python

import flag

force = flag.bool_("force", False, "force the command to execute")
count = flag.int_("count", 1, "a count")
name = flag.string("name", "Josh", "a name")
threshold = flag.float_("threshold", 1.0, "a threshold")

flag.parse()

print(
    dict(
        force=force.deref(),
        count=count.deref(),
        name=name.deref(),
        threshold=threshold.deref(),
    )
)
