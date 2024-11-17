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
