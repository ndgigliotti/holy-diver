"""Module for Config class and related functions."""
import json
import logging
import os
import re
import warnings
import pprint
from collections import UserDict
from typing import Any, Iterable, List, Optional, Union

import toml
import yaml
from holy_diver.constants import DEEP_KEY_PROPER, DEEP_KEY, DUNDER, PRIVATE
from holy_diver.config_mixin import ConfigMixin

logger = logging.getLogger(__name__)

PROTECTED_KEYS = frozenset(
    [
        "depth",
        "deep_keys",
        "check_required_keys",
        "convert",
        "convert_item",
        "deconvert",
        "deconvert_item",
        "deep_get",
        "deep_set",
        "search",
        "to_string",
    ]
    + dir(UserDict())
)


def check_keys(
    keys: Iterable[str], reserved: Optional[Iterable[str]] = PROTECTED_KEYS
) -> None:
    """Check that keys are syntactically valid and not reserved."""
    alphanum = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    reserved = set() if reserved is None else set(reserved)
    for key in keys:
        if alphanum.fullmatch(key) is None:
            raise ValueError(
                f"Key '{key}' is not a valid alphanumeric "
                f"attribute name matching r'{alphanum.pattern}'."
            )
        if DUNDER.fullmatch(key) is not None:
            raise ValueError(
                f"Key '{key}' is an invalid attribute name "
                f"matching the dunder pattern r'{DUNDER.pattern}'."
            )
        if PRIVATE.fullmatch(key) is not None:
            raise ValueError(
                f"Key '{key}' is an invalid attribute name "
                f"matching the private pattern r'{PRIVATE.pattern}'."
            )
        if key in reserved:
            raise ValueError(f"Key '{key}' is a reserved attribute or method name.")


def is_protected(key: str):
    """Check if a key is protected."""
    is_dunder = DUNDER.fullmatch(key) is not None
    is_private = PRIVATE.fullmatch(key) is not None
    is_reserved = key in PROTECTED_KEYS
    return any([is_dunder, is_private, is_reserved])


def deep_merge(d1: dict, d2: dict, in_place: bool = False) -> Union[dict, None]:
    """Merge two nested dictionaries.

    Values from `d2` take priority over values from `d1`.

    Parameters
    ----------
    d1 : dict
        First dictionary.
    d2 : dict
        Second dictionary.
    in_place : bool, optional
        Whether to merge in place, by default False.

    Returns
    -------
    dict
        Merged dictionary.
    """
    merged = d1 if in_place else d1.copy()
    for k, v in d2.items():
        if isinstance(v, dict):
            merged[k] = deep_merge(merged.get(k, {}), v)
        else:
            merged[k] = v
    return None if in_place else merged


class Config(UserDict, ConfigMixin):
    def __init__(
        self,
        data: dict = None,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
    ) -> None:
        self.data = {}
        if defaults is not None and data is not None:
            check_keys(defaults.keys())
            check_keys(data.keys())
            self.data.update(defaults)
            deep_merge(self.data, data, in_place=True)
        else:
            if defaults is not None:
                check_keys(defaults.keys())
                self.data = defaults
            if data is not None:
                check_keys(data.keys())
                self.data = data
        if required_keys is not None:
            self.check_required_keys(required_keys, if_missing=if_missing)

    def __getitem__(self, key: str) -> Any:
        """Get an item."""
        if DEEP_KEY_PROPER.fullmatch(key) is not None:
            return self.deep_get(key)
        return self.convert().data[key]

    def __setitem__(self, key: str, item: Any) -> None:
        """Set an item."""
        self.data[key] = self.convert_item(item)
        # warnings.warn(f"Configuration key '{key}' set to {item} after initialization!")

    def __getattr__(self, name: str) -> Any:
        """Get an item."""
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if is_protected(name):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def deep_keys(self) -> list[str]:
        """Return a list of all keys using dot notation."""
        from holy_diver.config_list import ConfigList

        keys = []
        for k, v in self.convert().items():
            keys.append(k)
            if isinstance(v, (type(self), ConfigList)):
                keys.extend([f"{k}.{i}" for i in v.deep_keys()])
        return keys

    def update(self, other: dict, deep: bool = False) -> None:
        """Update the configuration with a dictionary.

        Parameters
        ----------
        other : dict
            Dictionary to update with.
        deep : bool, optional
            Whether to update nested managers, by default False.

        """
        if deep:
            self.data = deep_merge(self.deconvert(), self.deconvert_item(other))
            self.data = self.convert().data
        else:
            self.data.update(self.convert_item(other))

    def convert_item(self, item: Any) -> Any:
        """Recursively convert nested dicts and lists to nested managers.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to convert, by default None. If None, the Config itself is converted.

        Returns
        -------
        Any
            Converted item.

        """
        from holy_diver.config_list import ConfigList

        if isinstance(item, dict):
            return type(self)({k: self.convert_item(v) for k, v in item.items()})
        if isinstance(item, (list, tuple, set)):
            return ConfigList([self.convert_item(x) for x in item])
        return item

    def deconvert_item(self, item: Any) -> Any:
        """Recursively deconvert nested managers to nested dicts and lists.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to deconvert.

        Returns
        -------
        Any
            Deconverted item.

        """
        from holy_diver.config_list import ConfigList

        if item is None:
            item = self
        if isinstance(item, type(self)):
            return {k: self.deconvert_item(v) for k, v in item.items()}
        if isinstance(item, (ConfigList, tuple, set)):
            return [self.deconvert_item(x) for x in item]
        return item

    @classmethod
    def from_dict(
        cls,
        dict: dict = None,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
    ) -> "Config":
        """Create nested Configs from a dictionary.

        Parameters
        ----------
        dict : dict, optional
            Dictionary to convert, by default None.
        defaults : dict, optional
            Default values to add to the configuration, by default None.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration, by default None.
        if_missing : str, optional
            Action to take if any keys are missing, by default "raise". Options are:
                * "raise": raise a KeyError
                * "warn": raise a warning

        Returns
        -------
        Config
            Nested Configs created from the dict.

        Raises
        ------
        KeyError
            If `if_missing` is "raise" and any keys are missing.

        """
        return cls(
            dict,
            defaults=defaults,
            required_keys=required_keys,
            if_missing=if_missing,
        ).convert()

    @classmethod
    def from_yaml(
        cls,
        path: str,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
        safe: bool = False,
        encoding: str = "utf-8",
    ) -> "Config":
        """Create nested Configs from a YAML file.

        Parameters
        ----------
        path : str
            Path to YAML file.
        defaults : dict, optional
            Default values to add to the configuration, by default None.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration, by default None.
        if_missing : str, optional
            Action to take if any keys are missing, by default "raise". Options are:
                * "raise": raise a KeyError
                * "warn": raise a warning
        safe : bool, optional
            Whether to use safe loading, by default False.
        encoding : str, optional
            Encoding of the YAML file, by default "utf-8".

        Returns
        -------
        Config
            Nested Configs created from the YAML file.

        Raises
        ------
        KeyError
            If `if_missing` is "raise" and any keys are missing.
        TypeError
            If the YAML file encodes a list.

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path, encoding=encoding) as f:
            data = load(f)
        if isinstance(data, list):
            raise TypeError(
                "YAML file must encode a dict, not a list. "
                "Use `ConfigList.from_yaml` instead."
            )
        return cls(
            data,
            defaults=defaults,
            required_keys=required_keys,
            if_missing=if_missing,
        ).convert()

    @classmethod
    def from_json(
        cls,
        path: str,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
        encoding: str = "utf-8",
    ) -> "Config":
        """Create nested Configs from a JSON file.

        Parameters
        ----------
        path : str
            Path to JSON file.
        defaults : dict, optional
            Default values to add to the configuration, by default None.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration, by default None.
        if_missing : str, optional
            Action to take if any keys are missing, by default "raise". Options are:
                * "raise": raise a KeyError
                * "warn": raise a warning
        encoding : str, optional
            Encoding of the JSON file, by default "utf-8".

        Returns
        -------
        Config
            Nested Configs created from the JSON file.

        Raises
        ------
        KeyError
            If `if_missing` is "raise" and any keys are missing.
        TypeError
            If the JSON file encodes a list.

        """
        with open(path, encoding=encoding) as f:
            data = json.load(f)
        if isinstance(data, list):
            raise TypeError(
                "JSON file must encode a dict, not a list. "
                "Use `ConfigList.from_json` instead."
            )
        return cls(
            data,
            defaults=defaults,
            required_keys=required_keys,
            if_missing=if_missing,
        ).convert()

    @classmethod
    def from_toml(
        cls,
        path: str,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
        encoding: str = "utf-8",
    ) -> "Config":
        """Create nested managers from a TOML file.

        Parameters
        ----------
        path : str
            Path to TOML file.
        defaults : dict, optional
            Default values to add to the configuration, by default None.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration, by default None.
        if_missing : str, optional
            Action to take if any keys are missing, by default "raise". Options are:
                * "raise": raise a KeyError
                * "warn": raise a warning
        encoding : str, optional
            Encoding of the TOML file, by default "utf-8".

        Returns
        -------
        Config
            Nested managers created from the TOML file.

        """
        with open(path, encoding=encoding) as f:
            data = toml.load(f)

        return cls(
            data,
            defaults=defaults,
            required_keys=required_keys,
            if_missing=if_missing,
        ).convert()



    def to_toml(
        self, path: Optional[str] = None, encoding: str = "utf-8"
    ) -> Union[str, bool]:
        """Write the configuration to a TOML file.

        If `path` is None, return the TOML string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str
            Path to TOML file.
        encoding : str, optional
            Encoding of the TOML file, by default "utf-8".

        Returns
        -------
        str or bool
            TOML string or True if successful.
        """
        if path is None:
            return toml.dumps(self.deconvert())

        with open(path, "w", encoding=encoding) as f:
            toml.dump(self.deconvert(), f)
        return os.path.isfile(path)
