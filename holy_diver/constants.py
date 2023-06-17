"""Module for common constants."""

import re


DEEP_KEY_PROPER = re.compile(r"^(?:\w+\.)+\w+$")
DEEP_KEY = re.compile(r"^(?:\w+\.)*\w+$")
DUNDER = re.compile(r"^__.*__$")
PRIVATE = re.compile(r"^_.*$")