#!/usr/bin/env python

"""Tests for `dot_config` package."""

import json
import os
import warnings
from tempfile import TemporaryDirectory
from typing import Sequence

import pytest
import yaml

from dot_config import ConfigManager

# Test data
TEST_DEFAULTS = {
    "a": 1,
    "b": 2,
    "d": {"e": 3, "f": {"g": 6}, "h": [8, 2, {"i": 5, "j": 9}]},
}
TEST_DICT = {
    "b": 3,
    "i": {"h": 7, "j": -3, "m": {"o": -5, "p": -2, "q": [1, {"r": 6, "s": 7}]}},
    "c": 4,
}
TEST_BAD_KEYS = ["c.d.e", "~3.#$@", "8a", "deep_keys", "convert", "deconvert"]
TEST_DEEP_KEYS = {
    "a",
    "b",
    "d",
    "d.e",
    "d.f",
    "d.f.g",
    "d.h",
    "d.h._0",
    "d.h._1",
    "d.h._2.i",
    "d.h._2.j",
    "i",
    "i.h",
    "i.j",
    "i.m",
    "i.m.o",
    "i.m.p",
    "i.m.q",
    "i.m.q._0",
    "i.m.q._1.r",
    "i.m.q._1.s",
    "c",
}
TEST_REQUIRED_KEYS_FAIL = ["a", "b", "d", "z", "d.e", "d.f.g", "d.z", "d.z.x"]
TEST_REQUIRED_KEYS_MISSING = ["d.z", "d.z.x", "z"]
TEST_REQUIRED_KEYS_PASS = ["a", "b", "d.e", "d.f.g", "d.h"]
TEST_PROTECTED_KEYS_TRUE = [
    "deep_keys",
    "convert",
    "deconvert",
    "__dict__",
    "__setstate__",
    "__mcbonkers__",
]
TEST_PROTECTED_KEYS_FALSE = ["reports", "plotting", "logging", "models", "level_1"]

# Error and warning messages
BAD_KEY_MSG = r"Key '.+' is"
SETITEM_WARNING_MSG = r"Configuration key '[a-z]' set to -?[0-9]+ after initialization!"
MISSING_KEYS_MSG = r"Configuration is missing required keys:"


# Test cases
def test_init_with_defaults():
    cm = ConfigManager(defaults=TEST_DEFAULTS)
    assert cm["a"] == 1
    assert cm["b"] == 2
    assert cm["d"]["e"] == 3
    assert cm["d"]["f"]["g"] == 6
    assert cm["d"]["h"][0] == 8
    assert cm["d"]["h"][1] == 2
    assert cm["d"]["h"][2]["i"] == 5
    assert cm["d"]["h"][2]["j"] == 9


def test_init_with_dict():
    cm = ConfigManager(dict=TEST_DICT)
    assert cm["b"] == 3
    assert cm["i"]["h"] == 7
    assert cm["i"]["j"] == -3
    assert cm["i"]["m"]["o"] == -5
    assert cm["i"]["m"]["p"] == -2
    assert cm["i"]["m"]["q"][0] == 1
    assert cm["i"]["m"]["q"][1]["r"] == 6
    assert cm["i"]["m"]["q"][1]["s"] == 7
    assert cm["c"] == 4


def test_null_values():
    dict = {"a": None, "b": 3, "c": {"d": None, "e": 5}}
    cm = ConfigManager(dict=dict)
    assert cm["a"] is None


def test_init_with_bad_keys():
    for k in TEST_BAD_KEYS:
        with pytest.raises(ValueError, match=BAD_KEY_MSG):
            ConfigManager(dict={k: 0})


def test_init_with_defaults_and_dict():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm["a"] == 1
    assert cm["b"] == 3
    assert cm["d"]["e"] == 3
    assert cm["d"]["f"]["g"] == 6
    assert cm["d"]["h"][0] == 8
    assert cm["d"]["h"][1] == 2
    assert cm["d"]["h"][2]["i"] == 5
    assert cm["d"]["h"][2]["j"] == 9
    assert cm["i"]["h"] == 7
    assert cm["i"]["j"] == -3
    assert cm["i"]["m"]["o"] == -5
    assert cm["i"]["m"]["p"] == -2
    assert cm["i"]["m"]["q"][0] == 1
    assert cm["i"]["m"]["q"][1]["r"] == 6
    assert cm["i"]["m"]["q"][1]["s"] == 7
    assert cm["c"] == 4


def test_getitem():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm["a"] == 1
    assert cm["b"] == 3
    assert cm["d"] == {"e": 3, "f": {"g": 6}, "h": [8, 2, {"i": 5, "j": 9}]}
    assert cm["i"] == {
        "h": 7,
        "j": -3,
        "m": {"o": -5, "p": -2, "q": [1, {"r": 6, "s": 7}]},
    }
    assert cm["c"] == 4


def test_setitem():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        cm["a"] = 5
    assert cm["a"] == 5


def test_getattr():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm.a == 1
    assert cm.b == 3
    assert cm.d == {"e": 3, "f": {"g": 6}, "h": [8, 2, {"i": 5, "j": 9}]}
    assert cm.i == {
        "h": 7,
        "j": -3,
        "m": {"o": -5, "p": -2, "q": [1, {"r": 6, "s": 7}]},
    }
    assert cm.c == 4


def test_setattr():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        cm.a = 5
    assert cm["a"] == 5


def test_convert():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    assert isinstance(cm["d"], ConfigManager)
    assert isinstance(cm["d"]["f"], ConfigManager)
    assert isinstance(cm["d"]["h"][2], ConfigManager)
    assert isinstance(cm["i"], ConfigManager)
    assert isinstance(cm["i"]["m"], ConfigManager)
    assert isinstance(cm["i"]["m"]["q"][1], ConfigManager)
    assert isinstance(cm["i"]["m"]["q"], Sequence)
    assert isinstance(cm["d"]["h"], Sequence)


def check_conversion_and_values(cm):
    """Check the recursive conversion and values of a ConfigManager object."""
    assert isinstance(cm.d, ConfigManager)
    assert isinstance(cm.d.f, ConfigManager)
    assert isinstance(cm.d.h[2], ConfigManager)
    assert isinstance(cm.i, ConfigManager)
    assert isinstance(cm.i.m, ConfigManager)
    assert isinstance(cm.i.m.q[1], ConfigManager)
    assert isinstance(cm.i.m.q, Sequence)
    assert isinstance(cm.d.h, Sequence)
    assert cm.a == 1
    assert cm.b == 3
    assert cm.d.e == 3
    assert cm.d.f.g == 6
    assert cm.d.h[0] == 8
    assert cm.d.h[1] == 2
    assert cm.d.h[2].i == 5
    assert cm.d.h[2].j == 9
    assert cm.i.h == 7
    assert cm.i.j == -3
    assert cm.i.m.o == -5
    assert cm.i.m.p == -2
    assert cm.i.m.q[0] == 1
    assert cm.i.m.q[1].r == 6
    assert cm.i.m.q[1].s == 7
    assert cm.c == 4


def test_getattr_nested():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    check_conversion_and_values(cm)


def test_setattr_nested():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        cm.d.f.g = -5
    assert cm.d.f.g == -5
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        cm.d.h[2].i = 3
    assert cm.d.h[2].i == 3
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        cm.i.m.q[1].r *= 2
    assert cm.i.m.q[1].r == 12


def test_deep_keys():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    assert set(cm.deep_keys()) == TEST_DEEP_KEYS


def test_check_required_keys_raise():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
        cm.check_required_keys(TEST_REQUIRED_KEYS_FAIL, if_missing="raise")
    cm.check_required_keys(TEST_REQUIRED_KEYS_PASS, if_missing="raise")


def test_check_required_keys_warn():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
        missing_keys = cm.check_required_keys(
            TEST_REQUIRED_KEYS_FAIL, if_missing="warn"
        )
    assert missing_keys == TEST_REQUIRED_KEYS_MISSING
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        empty = cm.check_required_keys(TEST_REQUIRED_KEYS_PASS, if_missing="warn")
    assert len(empty) == 0


def test_check_required_keys_return():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        missing_keys = cm.check_required_keys(
            TEST_REQUIRED_KEYS_FAIL, if_missing="return"
        )
        empty = cm.check_required_keys(TEST_REQUIRED_KEYS_PASS, if_missing="return")
    assert missing_keys == TEST_REQUIRED_KEYS_MISSING
    assert len(empty) == 0


def test_deconvert():
    cm = ConfigManager(dict=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    dct = cm.deconvert()
    assert isinstance(dct, dict)
    assert isinstance(dct["d"], dict)
    assert isinstance(dct["d"]["f"], dict)
    assert isinstance(dct["d"]["h"][2], dict)
    assert isinstance(dct["i"], dict)
    assert isinstance(dct["i"]["m"], dict)
    assert isinstance(dct["i"]["m"]["q"][1], dict)
    assert isinstance(dct["i"]["m"]["q"], list)
    assert isinstance(dct["d"]["h"], list)


def test_from_dict():
    cm = ConfigManager.from_dict(
        TEST_DICT, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
    )
    check_conversion_and_values(cm)


# Replace "path/to/yaml" and "path/to/json" with the actual paths to your test files
def test_from_yaml():
    with TemporaryDirectory(prefix="test_dot_config_") as d:
        # Prepare a temporary YAML file
        fname = os.path.join(d, "config.yaml")
        with open(fname, "w") as f:
            yaml.dump(TEST_DICT, f)
        # Load the YAML file and trigger error
        with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
            ConfigManager.from_yaml(
                fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="raise",
            )
        # Load the YAML file and trigger warning
        with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
            ConfigManager.from_yaml(
                fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="warn",
            )
        # Load the YAML file for real
        cm = ConfigManager.from_yaml(
            fname, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
        )
    # Check the recursive conversion and loaded values
    check_conversion_and_values(cm)


def test_from_json():
    with TemporaryDirectory(prefix="test_dot_config_") as d:
        # Prepare a temporary JSON file
        fname = os.path.join(d, "config.json")
        with open(fname, "w") as f:
            json.dump(TEST_DICT, f)
        # Load the JSON file and trigger error
        with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
            ConfigManager.from_json(
                fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="raise",
            )
        # Load the JSON file and trigger warning
        with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
            ConfigManager.from_json(
                fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="warn",
            )
        # Load the JSON file for real
        cm = ConfigManager.from_json(
            fname, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
        )
    # Check the recursive conversion and loaded values
    check_conversion_and_values(cm)
