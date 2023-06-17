import json
import os
from tempfile import TemporaryDirectory

import pytest
import yaml

from holy_diver import ConfigList, Config

# Test data
TEST_LIST = [1, 2, {"a": 3}, [4, {"b": 5}]]
TEST_DICT = {"a": 1, "b": 2, "c": [1, {"d": 6}]}
TEST_DEEP_KEYS = {
    "_0",
    "_1",
    "_2",
    "_3",
    "_2.a",
    "_3._0",
    "_3._1",
    "_3._1.b",
}
# Error and warning messages
SETITEM_WARNING_MSG = r"Configuration item [0-9]+ set to .* after initialization!"
LOAD_WRONG_TYPE_MSG = "must encode a list, not a dict"


# Test cases
def test_init():
    clm = ConfigList(TEST_LIST)
    assert len(clm) == 4
    assert clm[0] == 1
    assert clm[1] == 2


def test_getitem():
    clm = ConfigList(TEST_LIST)
    assert clm[0] == 1
    assert clm[1] == 2
    assert clm[2]["a"] == 3
    assert clm[3][0] == 4
    assert clm[3][1]["b"] == 5


def test_getitem_str():
    clm = ConfigList(TEST_LIST)
    # Without underscore
    assert clm["0"] == 1
    assert clm["1"] == 2
    assert clm["2"]["a"] == 3
    assert clm["3"] == [4, {"b": 5}]
    # With underscore
    assert clm["_0"] == 1
    assert clm["_1"] == 2
    assert clm["_2"]["a"] == 3
    assert clm["_3"] == [4, {"b": 5}]


def test_setitem():
    clm = ConfigList(TEST_LIST)
    clm[1] = 6
    assert clm[1] == 6


def test_getattr():
    clm = ConfigList(TEST_LIST)
    assert clm._0 == 1
    assert clm._1 == 2
    assert clm._2.a == 3
    assert clm._3._0 == 4
    assert clm._3._1.b == 5


def test_setattr():
    clm = ConfigList(TEST_LIST)
    clm._0 = 6
    assert clm[0] == 6


def test_keys():
    clm = ConfigList(TEST_LIST)
    assert clm.keys() == ["_0", "_1", "_2", "_3"]


def test_convert_item():
    clm = ConfigList(TEST_LIST)
    converted = clm.convert_item(TEST_LIST)
    assert isinstance(converted, ConfigList)
    assert isinstance(converted[3], ConfigList)
    assert isinstance(converted[2], Config)
    assert isinstance(converted[3][1], Config)


def test_convert():
    clm = ConfigList(TEST_LIST)
    converted = clm.convert()
    assert converted is not clm
    assert isinstance(converted, ConfigList)
    assert isinstance(converted[3], ConfigList)
    assert isinstance(converted[2], Config)
    assert isinstance(converted[3][1], Config)


def test_deconvert_item():
    clm = ConfigList(TEST_LIST).convert()
    deconverted = clm.deconvert_item(clm)
    assert deconverted is not clm
    assert isinstance(deconverted, list)
    assert isinstance(deconverted[3], list)
    assert isinstance(deconverted[2], dict)
    assert isinstance(deconverted[3][1], dict)


def test_deconvert():
    clm = ConfigList(TEST_LIST).convert()
    deconverted = clm.deconvert()
    assert deconverted is not clm
    assert isinstance(deconverted, list)
    assert isinstance(deconverted[3], list)
    assert isinstance(deconverted[2], dict)


def test_deep_keys():
    clm = ConfigList(TEST_LIST)
    converted = clm.convert()
    deep_keys = converted.deep_keys()
    assert set(deep_keys) == TEST_DEEP_KEYS


def test_check_required_keys():
    clm = ConfigList(TEST_LIST).convert()
    missing = ["_25.c.d", "_40.h.k"]
    with pytest.raises(KeyError):
        clm.check_required_keys(missing, if_missing="raise")
    with pytest.warns(UserWarning):
        clm.check_required_keys(missing, if_missing="warn")
    returned_keys = clm.check_required_keys(missing, if_missing="return")
    assert set(returned_keys) == set(missing)
    # Check that no error is raised
    clm.check_required_keys(TEST_DEEP_KEYS, if_missing="raise")


def test_deep_get():
    clm = ConfigList(TEST_LIST)
    # Without underscore
    assert clm.deep_get("0") == 1
    assert clm.deep_get("1") == 2
    assert clm.deep_get("2.a") == 3
    assert clm.deep_get("3.0") == 4
    assert clm.deep_get("3.1.b") == 5
    assert isinstance(clm.deep_get("2"), Config)
    assert isinstance(clm.deep_get("3"), ConfigList)
    assert isinstance(clm.deep_get("3.1"), Config)
    # With underscore
    assert clm.deep_get("_0") == 1
    assert clm.deep_get("_1") == 2
    assert clm.deep_get("_2.a") == 3
    assert clm.deep_get("_3._0") == 4
    assert clm.deep_get("_3._1.b") == 5
    assert isinstance(clm.deep_get("_2"), Config)
    assert isinstance(clm.deep_get("_3"), ConfigList)
    assert isinstance(clm.deep_get("_3._1"), Config)


def test_deep_lookup():
    clm = ConfigList(TEST_LIST)
    # Without underscore
    assert clm["2.a"] == 3
    assert clm["3.0"] == 4
    assert clm["3.1.b"] == 5
    assert isinstance(clm["3.1"], Config)
    # With underscore
    assert clm["_2.a"] == 3
    assert clm["_3._0"] == 4
    assert clm["_3._1.b"] == 5
    assert isinstance(clm["_3._1"], Config)


def test_deep_keys_evaluable():
    clm = ConfigList(TEST_LIST).convert()
    for key in clm.deep_keys():
        assert eval(f"clm.{key}") == clm.deep_get(key)


def test_depth():
    clm = ConfigList(TEST_LIST).convert()
    assert clm.depth == 2


def test_search_no_regex():
    test_data = [{"a": {"a": {"a": 1}}}, {"b": {"b": {"b": 2}}}]
    clm = ConfigList(test_data).convert()
    assert clm.search("a") == {
        "_0.a": {"a": {"a": 1}},
        "_0.a.a": {"a": 1},
        "_0.a.a.a": 1,
    }
    assert clm.search("b") == {
        "_1.b": {"b": {"b": 2}},
        "_1.b.b": {"b": 2},
        "_1.b.b.b": 2,
    }
    assert clm.search("a", return_values=True) == [{"a": {"a": 1}}, {"a": 1}, 1]
    assert clm.search("b", return_values=True) == [{"b": {"b": 2}}, {"b": 2}, 2]


def test_search_regex():
    test_data = [{"a": {"a": {"a": 1}}}, {"b": {"b": {"b": 2}}}]
    clm = ConfigList(test_data).convert()
    assert clm.search("a", regex=True) == {
        "_0.a": {"a": {"a": 1}},
        "_0.a.a": {"a": 1},
        "_0.a.a.a": 1,
    }
    assert clm.search("b", regex=True) == {
        "_1.b": {"b": {"b": 2}},
        "_1.b.b": {"b": 2},
        "_1.b.b.b": 2,
    }
    assert clm.search("a", regex=True, return_values=True) == [
        {"a": {"a": 1}},
        {"a": 1},
        1,
    ]
    assert clm.search("b", regex=True, return_values=True) == [
        {"b": {"b": 2}},
        {"b": 2},
        2,
    ]
    assert clm.search(r"[ab]", regex=True) == {
        "_0.a": {"a": {"a": 1}},
        "_0.a.a": {"a": 1},
        "_0.a.a.a": 1,
        "_1.b": {"b": {"b": 2}},
        "_1.b.b": {"b": 2},
        "_1.b.b.b": 2,
    }
    assert clm.search(r"[ab]", regex=True, return_values=True) == [
        {"a": {"a": 1}},
        {"a": 1},
        1,
        {"b": {"b": 2}},
        {"b": 2},
        2,
    ]


def check_conversion_and_values(clm):
    assert len(clm) == 4
    assert isinstance(clm, ConfigList)
    assert isinstance(clm[3], ConfigList)
    assert isinstance(clm[2], Config)
    assert isinstance(clm[3][1], Config)
    assert clm._0 == 1
    assert clm._1 == 2
    assert clm._2.a == 3
    assert clm._3._0 == 4
    assert clm._3._1.b == 5


def test_from_list():
    clm = ConfigList.from_list(TEST_LIST)
    check_conversion_and_values(clm)


# Replace "path/to/yaml" and "path/to/json" with the actual paths to your test files
def test_from_yaml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary YAML file
        good_fname = os.path.join(d, "config.yaml")
        bad_fname = os.path.join(d, "bad_config.yaml")
        test_dict = {"a": 1, "b": 2, "c": [1, {"d": 6}]}
        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            yaml.dump(TEST_LIST, f)
            yaml.dump(test_dict, g)

        # Load the bad YAML file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            ConfigList.from_yaml(bad_fname)

        # Load the YAML file
        clm = ConfigList.from_yaml(good_fname)
    check_conversion_and_values(clm)


def test_from_json():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary JSON file
        good_fname = os.path.join(d, "config.json")
        bad_fname = os.path.join(d, "bad_config.json")

        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            json.dump(TEST_LIST, f)
            json.dump(TEST_DICT, g)

        # Load the bad json file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            ConfigList.from_json(bad_fname)

        # Load the json file
        clm = ConfigList.from_json(good_fname)
    check_conversion_and_values(clm)


def test_to_yaml():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary YAML file
        fname = os.path.join(d, "config.yaml")
        clm = ConfigList(TEST_LIST)
        clm.to_yaml(fname)
        assert os.path.isfile(fname)
        with open(fname) as f:
            loaded = yaml.safe_load(f)
        assert loaded == clm
        assert loaded == TEST_LIST


def test_to_yaml_string():
    clm = ConfigList(TEST_LIST)
    serialized = clm.to_yaml()
    assert isinstance(serialized, str)
    loaded = yaml.safe_load(serialized)
    assert loaded == clm
    assert loaded == TEST_LIST


def test_to_json():
    with TemporaryDirectory(prefix="test_holy_diver_") as d:
        # Prepare a temporary JSON file
        fname = os.path.join(d, "config.json")
        clm = ConfigList(TEST_LIST)
        clm.to_json(fname)
        assert os.path.isfile(fname)
        with open(fname) as f:
            loaded = json.load(f)
        assert loaded == clm
        assert loaded == TEST_LIST


def test_to_json_string():
    clm = ConfigList(TEST_LIST)
    serialized = clm.to_json()
    assert isinstance(serialized, str)
    loaded = json.loads(serialized)
    assert loaded == clm
    assert loaded == TEST_LIST
