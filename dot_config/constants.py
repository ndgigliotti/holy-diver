"""Module for common constants."""

import re


DEEP_KEY_STRICT = re.compile(r"^(?:\w+\.)+\w+$")
DEEP_KEY_LAX = re.compile(r"^(?:\w+\.)*\w+$")
DUNDER = re.compile(r"^__.*__$")
PRIVATE = re.compile(r"^_.*$")