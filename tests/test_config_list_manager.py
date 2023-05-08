import json
import os
from tempfile import TemporaryDirectory

import pytest
import yaml

from dot_config import ConfigListManager, ConfigManager

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
    clm = ConfigListManager(TEST_LIST)
    assert len(clm) == 4
    assert clm[0] == 1
    assert clm[1] == 2


def test_getitem():
    clm = ConfigListManager(TEST_LIST)
    assert clm[0] == 1
    assert clm[1] == 2
    assert clm[2]["a"] == 3
    assert clm[3][0] == 4
    assert clm[3][1]["b"] == 5


def test_setitem():
    clm = ConfigListManager(TEST_LIST)
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        clm[1] = 6
    assert clm[1] == 6


def test_getattr():
    clm = ConfigListManager(TEST_LIST)
    assert clm._0 == 1
    assert clm._1 == 2
    assert clm._2.a == 3
    assert clm._3._0 == 4
    assert clm._3._1.b == 5


def test_setattr():
    clm = ConfigListManager(TEST_LIST)
    with pytest.warns(UserWarning, match=SETITEM_WARNING_MSG):
        clm._0 = 6
    assert clm[0] == 6


def test_keys():
    clm = ConfigListManager(TEST_LIST)
    assert clm.keys() == ["_0", "_1", "_2", "_3"]


def test_convert_item():
    clm = ConfigListManager(TEST_LIST)
    converted = clm.convert_item(TEST_LIST)
    assert isinstance(converted, ConfigListManager)
    assert isinstance(converted[3], ConfigListManager)
    assert isinstance(converted[2], ConfigManager)
    assert isinstance(converted[3][1], ConfigManager)


def test_convert():
    clm = ConfigListManager(TEST_LIST)
    converted = clm.convert()
    assert converted is not clm
    assert isinstance(converted, ConfigListManager)
    assert isinstance(converted[3], ConfigListManager)
    assert isinstance(converted[2], ConfigManager)
    assert isinstance(converted[3][1], ConfigManager)


def test_deconvert_item():
    clm = ConfigListManager(TEST_LIST).convert()
    deconverted = clm.deconvert_item(clm)
    assert deconverted is not clm
    assert isinstance(deconverted, list)
    assert isinstance(deconverted[3], list)
    assert isinstance(deconverted[2], dict)
    assert isinstance(deconverted[3][1], dict)


def test_deconvert():
    clm = ConfigListManager(TEST_LIST).convert()
    deconverted = clm.deconvert()
    assert deconverted is not clm
    assert isinstance(deconverted, list)
    assert isinstance(deconverted[3], list)
    assert isinstance(deconverted[2], dict)


def test_deep_keys():
    clm = ConfigListManager(TEST_LIST)
    converted = clm.convert()
    deep_keys = converted.deep_keys()
    assert set(deep_keys) == TEST_DEEP_KEYS


def test_depth():
    clm = ConfigListManager(TEST_LIST).convert()
    assert clm.depth == 2


def check_conversion_and_values(clm):
    assert len(clm) == 4
    assert isinstance(clm, ConfigListManager)
    assert isinstance(clm[3], ConfigListManager)
    assert isinstance(clm[2], ConfigManager)
    assert isinstance(clm[3][1], ConfigManager)
    assert clm._0 == 1
    assert clm._1 == 2
    assert clm._2.a == 3
    assert clm._3._0 == 4
    assert clm._3._1.b == 5


def test_from_list():
    clm = ConfigListManager.from_list(TEST_LIST)
    check_conversion_and_values(clm)


# Replace "path/to/yaml" and "path/to/json" with the actual paths to your test files
def test_from_yaml():
    with TemporaryDirectory(prefix="test_dot_config_") as d:
        # Prepare a temporary YAML file
        good_fname = os.path.join(d, "config.yaml")
        bad_fname = os.path.join(d, "bad_config.yaml")
        test_dict = {"a": 1, "b": 2, "c": [1, {"d": 6}]}
        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            yaml.dump(TEST_LIST, f)
            yaml.dump(test_dict, g)

        # Load the bad YAML file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            ConfigListManager.from_yaml(bad_fname)

        # Load the YAML file
        clm = ConfigListManager.from_yaml(good_fname)
    check_conversion_and_values(clm)


def test_from_json():
    with TemporaryDirectory(prefix="test_dot_config_") as d:
        # Prepare a temporary JSON file
        good_fname = os.path.join(d, "config.json")
        bad_fname = os.path.join(d, "bad_config.json")

        with open(good_fname, "w") as f, open(bad_fname, "w") as g:
            json.dump(TEST_LIST, f)
            json.dump(TEST_DICT, g)

        # Load the bad json file and trigger error
        with pytest.raises(TypeError, match=LOAD_WRONG_TYPE_MSG):
            ConfigListManager.from_json(bad_fname)

        # Load the json file
        clm = ConfigListManager.from_json(good_fname)
    check_conversion_and_values(clm)
