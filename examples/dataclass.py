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
