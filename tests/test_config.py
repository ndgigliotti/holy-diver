#!/usr/bin/env python

"""Tests for `holy_diver` package."""

import json
import os
import string
import warnings
from tempfile import TemporaryDirectory

import pytest
import toml
import yaml

from holy_diver import ConfigList, Config

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
    "d": {"f": {"w": 4}},
}
TEST_FLAT_DICT = {k: ord(k) for k in string.ascii_lowercase}
TEST_SECTIONS = {"section_1": {"a": 1, "b": 2}, "section_2": {"c": 3, "d": 4}}
TEST_LIST = [1, 2, {"a": 3}, [4, {"b": 5}]]
TEST_BAD_KEYS = ["c.d.e", "~3.#$@", "8a", "deep_keys", "convert", "deconvert"]
TEST_DEEP_KEYS = {
    "a",
    "b",
    "d",
    "d.e",
    "d.f",
    "d.f.g",
    "d.f.w",
    "d.h",
    "d.h._0",
    "d.h._1",
    "d.h._2",
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
    "i.m.q._1",
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
MISSING_KEYS_MSG = "Configuration is missing required keys:"
LOAD_WRONG_TYPE_MSG = "must encode a dict, not a list"


# Test cases
def test_init_with_defaults():
    cm = Config(defaults=TEST_DEFAULTS)
    assert cm["a"] == 1
    assert cm["b"] == 2
    assert cm["d"]["e"] == 3
    assert cm["d"]["f"]["g"] == 6
    assert cm["d"]["h"][0] == 8
    assert cm["d"]["h"][1] == 2
    assert cm["d"]["h"][2]["i"] == 5
    assert cm["d"]["h"][2]["j"] == 9


def test_init_with_dict():
    cm = Config(data=TEST_DICT)
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
    cm = Config(data=dict)
    assert cm["a"] is None


def test_init_with_bad_keys():
    for k in TEST_BAD_KEYS:
        with pytest.raises(ValueError, match=BAD_KEY_MSG):
            Config(data={k: 0})


def test_init_with_defaults_and_dict():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
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
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm["a"] == 1
    assert cm["b"] == 3
    assert cm["d"] == {"e": 3, "f": {"g": 6, "w": 4}, "h": [8, 2, {"i": 5, "j": 9}]}
    assert cm["i"] == {
        "h": 7,
        "j": -3,
        "m": {"o": -5, "p": -2, "q": [1, {"r": 6, "s": 7}]},
    }
    assert cm["c"] == 4


def test_setitem():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    # with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
    cm["a"] = 5
    assert cm["a"] == 5


def test_getattr():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm.a == 1
    assert cm.b == 3
    assert cm.d == {"e": 3, "f": {"g": 6, "w": 4}, "h": [8, 2, {"i": 5, "j": 9}]}
    assert cm.i == {
        "h": 7,
        "j": -3,
        "m": {"o": -5, "p": -2, "q": [1, {"r": 6, "s": 7}]},
    }
    assert cm.c == 4


def test_setattr():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    # with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
    cm.a = 5
    assert cm["a"] == 5


def test_convert():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    assert isinstance(cm["d"], Config)
    assert isinstance(cm["d"]["f"], Config)
    assert isinstance(cm["d"]["h"][2], Config)
    assert isinstance(cm["i"], Config)
    assert isinstance(cm["i"]["m"], Config)
    assert isinstance(cm["i"]["m"]["q"][1], Config)
    assert isinstance(cm["i"]["m"]["q"], ConfigList)
    assert isinstance(cm["d"]["h"], ConfigList)


def check_conversion_and_values(cm):
    """Check the recursive conversion and values of a Config object."""
    assert isinstance(cm.d, Config)
    assert isinstance(cm.d.f, Config)
    assert isinstance(cm.d.h[2], Config)
    assert isinstance(cm.i, Config)
    assert isinstance(cm.i.m, Config)
    assert isinstance(cm.i.m.q[1], Config)
    assert isinstance(cm.i.m.q, ConfigList)
    assert isinstance(cm.d.h, ConfigList)
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
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    check_conversion_and_values(cm)


def test_setattr_nested():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    # with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
    cm.d.f.g = -5
    assert cm.d.f.g == -5
    # with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
    cm.d.h[2].i = 3
    assert cm.d.h[2].i == 3
    # with pytest.warns(UserWarning, mget_deep_keyatch=SETITEM_WARNING_MSG):
    cm.i.m.q[1].r *= 2
    assert cm.i.m.q[1].r == 12


def test_deep_keys():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    assert set(cm.deep_keys()) == TEST_DEEP_KEYS


def test_deep_get():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm.deep_get("d.f.g") == 6
    assert cm.deep_get("d.h._0") == 8
    assert cm.deep_get("d.h._1") == 2
    assert cm.deep_get("d.h._2.i") == 5
    assert cm.deep_get("i.m.q._1.r") == 6
    assert cm.deep_get("i.m.q._1.s") == 7
    assert isinstance(cm.deep_get("d"), Config)
    assert isinstance(cm.deep_get("d.f"), Config)
    assert isinstance(cm.deep_get("d.h._2"), Config)
    assert isinstance(cm.deep_get("i"), Config)
    assert isinstance(cm.deep_get("i.m"), Config)
    assert isinstance(cm.deep_get("i.m.q._1"), Config)
    assert isinstance(cm.deep_get("i.m.q"), ConfigList)
    assert isinstance(cm.deep_get("d.h"), ConfigList)
    # Without underscores
    assert cm.deep_get("d.h.0") == 8
    assert cm.deep_get("d.h.1") == 2
    assert cm.deep_get("d.h.2.i") == 5
    assert cm.deep_get("i.m.q.1.r") == 6
    assert cm.deep_get("i.m.q.1.s") == 7
    assert isinstance(cm.deep_get("d.h.2"), Config)
    assert isinstance(cm.deep_get("i.m.q.1"), Config)


def test_deep_lookup():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    assert cm["d.f.g"] == 6
    assert cm["d.h._0"] == 8
    assert cm["d.h._1"] == 2
    assert cm["d.h._2.i"] == 5
    assert cm["i.m.q._1.r"] == 6
    assert cm["i.m.q._1.s"] == 7
    assert isinstance(cm["d"], Config)
    assert isinstance(cm["d.f"], Config)
    assert isinstance(cm["d.h._2"], Config)
    assert isinstance(cm["i"], Config)
    assert isinstance(cm["i.m"], Config)
    assert isinstance(cm["i.m.q._1"], Config)
    assert isinstance(cm["i.m.q"], ConfigList)
    assert isinstance(cm["d.h"], ConfigList)
    # Without underscores
    assert cm["d.h.0"] == 8
    assert cm["d.h.1"] == 2
    assert cm["d.h.2.i"] == 5
    assert cm["i.m.q.1.r"] == 6
    assert cm["i.m.q.1.s"] == 7
    assert isinstance(cm["d.h.2"], Config)
    assert isinstance(cm["i.m.q.1"], Config)


def test_deep_keys_evaluable():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    for key in cm.deep_keys():
        assert eval(f"cm.{key}") == cm.deep_get(key)


def test_depth():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
    assert cm.depth == 4


def test_search_no_regex():
    test_data = {"a": {"a": {"a": 1}}, "b": {"b": {"b": 2}}}
    cm = Config(data=test_data).convert()
    assert cm.search("a") == {"a": {"a": {"a": 1}}, "a.a": {"a": 1}, "a.a.a": 1}
    assert cm.search("b") == {"b": {"b": {"b": 2}}, "b.b": {"b": 2}, "b.b.b": 2}
    assert cm.search("a", return_values=True) == [{"a": {"a": 1}}, {"a": 1}, 1]
    assert cm.search("b", return_values=True) == [{"b": {"b": 2}}, {"b": 2}, 2]


def test_search_regex():
    test_data = {"a": {"a": {"a": 1}}, "b": {"b": {"b": 2}}}
    cm = Config(data=test_data).convert()
    assert cm.search("a", regex=True) == {
        "a": {"a": {"a": 1}},
        "a.a": {"a": 1},
        "a.a.a": 1,
    }
    assert cm.search("b", regex=True) == {
        "b": {"b": {"b": 2}},
        "b.b": {"b": 2},
        "b.b.b": 2,
    }
    assert cm.search("a", regex=True, return_values=True) == [
        {"a": {"a": 1}},
        {"a": 1},
        1,
    ]
    assert cm.search("b", regex=True, return_values=True) == [
        {"b": {"b": 2}},
        {"b": 2},
        2,
    ]
    assert cm.search(r"[ab]", regex=True) == {
        "a": {"a": {"a": 1}},
        "a.a": {"a": 1},
        "a.a.a": 1,
        "b": {"b": {"b": 2}},
        "b.b": {"b": 2},
        "b.b.b": 2,
    }
    assert cm.search(r"[ab]", regex=True, return_values=True) == [
        {"a": {"a": 1}},
        {"a": 1},
        1,
        {"b": {"b": 2}},
        {"b": 2},
        2,
    ]


def test_check_required_keys_raise():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
        cm.check_required_keys(TEST_REQUIRED_KEYS_FAIL, if_missing="raise")
    cm.check_required_keys(TEST_REQUIRED_KEYS_PASS, if_missing="raise")


def test_check_required_keys_warn():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
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
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        missing_keys = cm.check_required_keys(
            TEST_REQUIRED_KEYS_FAIL, if_missing="return"
        )
        empty = cm.check_required_keys(TEST_REQUIRED_KEYS_PASS, if_missing="return")
    assert missing_keys == TEST_REQUIRED_KEYS_MISSING
    assert len(empty) == 0


def test_deconvert():
    cm = Config(data=TEST_DICT, defaults=TEST_DEFAULTS).convert()
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


def test_shallow_update():
    cm = Config(TEST_DICT).convert()
    test_dict_update = {"b": 1, "i": 2, "c": 3}
    cm.update(test_dict_update, deep=False)
    assert cm["b"] == 1
    assert cm["i"] == 2
    assert cm["c"] == 3


def test_deep_update():
    cm = Config({"a": {"b": {"c": 5}, "h": {"x": 2}}}).convert()
    cm.update({"w": 7, "a": {"b": {"d": 10}, "h": {"x": -1}}}, deep=True)
    assert cm["w"] == 7
    assert cm["a"]["b"]["c"] == 5
    assert cm["a"]["b"]["d"] == 10
    assert cm["a"]["h"]["x"] == -1
    assert isinstance(cm["a"]["b"], Config)
    assert isinstance(cm["a"]["b"], Config)
    assert isinstance(cm["a"]["h"], Config)


def test_from_dict():
    cm = Config.from_dict(
        TEST_DICT, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
    )
    check_conversion_and_values(cm)


# Replace "path/to/yaml" and "path/to/json" with the actual paths to your test files
def test_from_yaml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary YAML file
        good_fname = os.path.join(d, "config.yaml")
        bad_fname = os.path.join(d, "bad_config.yaml")
        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            yaml.dump(TEST_DICT, f)
            yaml.dump(TEST_LIST, g)

        # Load the listlike YAML file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            Config.from_yaml(
                bad_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_PASS,
                if_missing="raise",
            )

        # Load the correct YAML file and trigger error
        with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
            Config.from_yaml(
                good_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="raise",
            )
        # Load the correct YAML file and trigger warning
        with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
            Config.from_yaml(
                good_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="warn",
            )
        # Load the correct YAML file for real
        cm = Config.from_yaml(
            good_fname, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
        )
    # Check the recursive conversion and loaded values
    check_conversion_and_values(cm)


def test_from_json():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary JSON file
        good_fname = os.path.join(d, "config.json")
        bad_fname = os.path.join(d, "bad_config.json")
        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            json.dump(TEST_DICT, f)
            json.dump(TEST_LIST, g)

        # Load the listlike JSON file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            Config.from_json(
                bad_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_PASS,
                if_missing="raise",
            )
        # Load the correct JSON file and trigger error
        with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
            Config.from_json(
                good_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="raise",
            )
        # Load the correct JSON file and trigger warning
        with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
            Config.from_json(
                good_fname,
                defaults=TEST_DEFAULTS,
                required_keys=TEST_REQUIRED_KEYS_FAIL,
                if_missing="warn",
            )
        # Load the correct JSON file for real
        cm = Config.from_json(
            good_fname, defaults=TEST_DEFAULTS, required_keys=TEST_REQUIRED_KEYS_PASS
        )
    # Check the recursive conversion and loaded values
    check_conversion_and_values(cm)


def test_from_toml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary TOML file
        fname = os.path.join(d, "config.toml")
        with open(fname, "w") as f:
            toml.dump(TEST_SECTIONS, f)

        # Load the TOML file and trigger error
        with pytest.raises(KeyError, match=MISSING_KEYS_MSG):
            Config.from_toml(
                fname,
                required_keys=["section_3"],
                if_missing="raise",
            )
        # Load the TOML file and trigger warning
        with pytest.warns(UserWarning, match=MISSING_KEYS_MSG):
            Config.from_toml(
                fname,
                required_keys=["section_3"],
                if_missing="warn",
            )
        # Load the TOML file for real
        cm = Config.from_toml(fname)

    # Check the recursive conversion and loaded values
    assert isinstance(cm.section_1, Config)
    assert isinstance(cm.section_2, Config)
    assert len(cm) == len(TEST_SECTIONS)
    assert cm.section_1.a == 1
    assert cm.section_1.b == 2
    assert cm.section_2.c == 3
    assert cm.section_2.d == 4


def test_to_yaml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary YAML file
        fname = os.path.join(d, "config.yaml")
        cm = Config.from_dict(TEST_DICT)
        cm.to_yaml(fname)
        assert os.path.isfile(fname)
        with open(fname) as f:
            loaded_dict = yaml.safe_load(f)
        assert loaded_dict == cm
        assert loaded_dict == TEST_DICT


def test_to_yaml_string():
    cm = Config.from_dict(TEST_DICT)
    serialized = cm.to_yaml()
    loaded_dict = yaml.safe_load(serialized)
    assert loaded_dict == cm
    assert loaded_dict == TEST_DICT


def test_to_json():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary JSON file
        fname = os.path.join(d, "config.json")
        cm = Config.from_dict(TEST_DICT)
        cm.to_json(fname)
        assert os.path.isfile(fname)
        with open(fname) as f:
            loaded_dict = json.load(f)
        assert loaded_dict == cm
        assert loaded_dict == TEST_DICT


def test_to_json_string():
    cm = Config.from_dict(TEST_DICT)
    serialized = cm.to_json()
    loaded_dict = json.loads(serialized)
    assert loaded_dict == cm
    assert loaded_dict == TEST_DICT


def test_to_toml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary TOML file
        fname = os.path.join(d, "config.toml")
        cm = Config.from_dict(TEST_SECTIONS)
        cm.to_toml(fname)
        assert os.path.isfile(fname)
        with open(fname) as f:
            loaded_dict = toml.load(f)
        assert loaded_dict == cm
        assert loaded_dict == TEST_SECTIONS


def test_to_toml_string():
    cm = Config.from_dict(TEST_SECTIONS)
    serialized = cm.to_toml()
    loaded_dict = toml.loads(serialized)
    assert loaded_dict == cm
    assert loaded_dict == TEST_SECTIONS
