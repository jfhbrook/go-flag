"""
Go has the concept of "zero values". These are the values assigned to
uninitialized variables by default, or when a struct is created without
inputs.

These values are offered as a convenience for crafting uninitialized
values in Python.
"""

import datetime

from flag.time import Duration

bool_: bool = False
int_: int = 0
string: str = ""
float_: float = 0.0
duration: datetime.timedelta = Duration()
