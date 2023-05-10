"""Module for ConfigManager class and related functions."""
import json
import logging
import os
import re
import warnings
from collections import UserDict
from typing import Any, Iterable, List, Optional, Union

import toml
import yaml

logger = logging.getLogger(__name__)

PROTECTED_KEYS = frozenset(
    [
        "depth",
        "deep_keys",
        "check_required_keys",
        "convert",
        "deconvert",
        "to_string",
        "__next__",
        "__getstate__",
        "__setstate__",
    ]
    + dir(UserDict())
)


def check_keys(
    keys: Iterable[str], reserved: Optional[Iterable[str]] = PROTECTED_KEYS
) -> None:
    """Check that keys are syntactically valid and not reserved."""
    alphanum = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    dunder = re.compile(r"^__.*__$")
    reserved = set() if reserved is None else set(reserved)
    for key in keys:
        if alphanum.fullmatch(key) is None:
            raise ValueError(
                f"Key '{key}' is not a valid alphanumeric "
                f"attribute name matching r'{alphanum.pattern}'."
            )
        if dunder.fullmatch(key) is not None:
            raise ValueError(
                f"Key '{key}' is an invalid attribute name "
                f"matching the dunder pattern r'{dunder.pattern}'."
            )
        if key in reserved:
            raise ValueError(f"Key '{key}' is a reserved attribute or method name.")


def is_protected(key: str):
    return key in PROTECTED_KEYS or re.fullmatch(r"__\w+__", key) is not None


class ConfigManager(UserDict):
    def __init__(
        self,
        dict: dict = None,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
    ) -> None:
        self.data = {}
        if defaults is not None:
            check_keys(defaults.keys())
            self.data.update(defaults)
        if dict is not None:
            check_keys(dict.keys())
            self.data.update(dict)
        if required_keys is not None:
            self.check_required_keys(required_keys, if_missing=if_missing)

    def __getitem__(self, key: str) -> Any:
        """Get an item."""
        return self.convert().data[key]

    def __setitem__(self, key: str, item: Any) -> None:
        """Set an item."""
        self.data[key] = item
        warnings.warn(f"Configuration key '{key}' set to {item} after initialization!")

    def __getattr__(self, name: str) -> Any:
        """Get an item."""
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if is_protected(name):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def deep_keys(self) -> List[str]:
        """Return a list of all keys using dot notation."""
        from dot_config.config_list_manager import ConfigListManager

        keys = []
        for k, v in self.convert().items():
            keys.append(k)
            if isinstance(v, (type(self), ConfigListManager)):
                keys.extend([f"{k}.{i}" for i in v.deep_keys()])
        return keys

    @property
    def depth(self) -> int:
        """Return the depth of the configuration tree."""
        return max([k.count(".") for k in self.deep_keys()])

    def check_required_keys(
        self, keys: Iterable[str], if_missing: str = "raise"
    ) -> list[str]:
        """Check that the ConfigManager has the required keys.

        Parameters
        ----------
        keys : Iterable[str]
            Iterable of keys, including nested keys in dot notation, e.g. "models.bart.tokenizer".
        if_missing : str, optional
            Action to take if any keys are missing, by default "raise". Options are:
                * "raise": raise a KeyError
                * "warn": raise a warning and return a list of missing keys
                * "return": quietly return a list of missing keys

        Returns
        -------
        list[str]
            List of missing keys.

        Raises
        ------
        ValueError
            If `if_missing` is not one of "raise", "warn", "log", or "return".
        KeyError
            If `if_missing` is "raise" and any keys are missing.
        """
        if if_missing not in {"raise", "warn", "return"}:
            raise ValueError(
                f"`if_missing` must be 'raise', 'warn', 'log', or 'return', not '{if_missing}'."
            )
        missing_keys = sorted(set(keys) - set(self.deep_keys()))
        msg = f"Configuration is missing required keys: {missing_keys}."

        if missing_keys:
            if if_missing == "raise":
                raise KeyError(msg)
            elif if_missing == "warn":
                warnings.warn(msg)

        return missing_keys

    def convert_item(self, item: Any) -> Any:
        """Recursively convert nested dicts and lists to nested managers.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to convert, by default None. If None, the ConfigManager itself is converted.

        Returns
        -------
        Any
            Converted item.

        """
        from dot_config.config_list_manager import ConfigListManager

        if isinstance(item, dict):
            return type(self)({k: self.convert_item(v) for k, v in item.items()})
        if isinstance(item, (list, tuple, set)):
            return ConfigListManager([self.convert_item(x) for x in item])
        return item

    def convert(self) -> "ConfigManager":
        """Recursively convert nested dicts and lists to nested managers.

        Returns a copy of self.

        Returns
        -------
        ConfigManager
            New hierarchy of managers and values.

        """
        return self.convert_item(self.data)

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
        from dot_config.config_list_manager import ConfigListManager

        if item is None:
            item = self
        if isinstance(item, type(self)):
            return {k: self.deconvert_item(v) for k, v in item.items()}
        if isinstance(item, (ConfigListManager, tuple, set)):
            return [self.deconvert_item(x) for x in item]
        return item

    def deconvert(self) -> dict:
        """Recursively deconvert nested managers to nested dicts and lists.

        Returns a copy.

        Returns
        -------
        dict
            Deconverted hierarchy of dicts and lists.

        """
        return self.deconvert_item(self)

    def to_string(self) -> str:
        """Convert the ConfigManager to a string.

        Returns
        -------
        str
            String representation of the ConfigManager.

        """
        return yaml.dump(self.deconvert())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.data)})"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_dict(
        cls,
        dict: dict = None,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
    ) -> "ConfigManager":
        """Create nested ConfigManagers from a dictionary.

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
        ConfigManager
            Nested ConfigManagers created from the dict.

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
    ) -> "ConfigManager":
        """Create nested ConfigManagers from a YAML file.

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

        Returns
        -------
        ConfigManager
            Nested ConfigManagers created from the YAML file.

        Raises
        ------
        KeyError
            If `if_missing` is "raise" and any keys are missing.
        TypeError
            If the YAML file encodes a list.

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path) as f:
            data = load(f)
        if isinstance(data, list):
            raise TypeError(
                "YAML file must encode a dict, not a list. "
                "Use `ConfigListManager.from_yaml` instead."
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
    ) -> "ConfigManager":
        """Create nested ConfigManagers from a JSON file.

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

        Returns
        -------
        ConfigManager
            Nested ConfigManagers created from the JSON file.

        Raises
        ------
        KeyError
            If `if_missing` is "raise" and any keys are missing.
        TypeError
            If the JSON file encodes a list.

        """
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            raise TypeError(
                "JSON file must encode a dict, not a list. "
                "Use `ConfigListManager.from_json` instead."
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
    ) -> "ConfigManager":
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

        Returns
        -------
        ConfigManager
            Nested managers created from the TOML file.

        """
        with open(path) as f:
            data = toml.load(f)

        return cls(
            data,
            defaults=defaults,
            required_keys=required_keys,
            if_missing=if_missing,
        ).convert()

    def to_yaml(self, path: Optional[str] = None) -> Union[str, bool]:
        """Write the configuration to a YAML file.

        If `path` is None, return the YAML string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str, optional
            Path to YAML file.

        Returns
        -------
        str or bool
            YAML string or True if successful.
        """
        if path is None:
            return yaml.dump(self.deconvert())

        with open(path, "w") as f:
            yaml.dump(self.deconvert(), f)
        return os.path.isfile(path)

    def to_json(self, path: Optional[str] = None) -> Union[str, bool]:
        """Write the configuration to a JSON file.

        If `path` is None, return the JSON string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str, optional
            Path to JSON file.

        Returns
        -------
        str or bool
            JSON string or True if successful.

        """
        if path is None:
            return json.dumps(self.deconvert())

        with open(path, "w") as f:
            json.dump(self.deconvert(), f)
        return os.path.isfile(path)

    def to_toml(self, path: Optional[str]=None) -> Union[str, bool]:
        """Write the configuration to a TOML file.

        If `path` is None, return the TOML string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str
            Path to TOML file.

        Returns
        -------
        str or bool
            TOML string or True if successful.
        """
        if path is None:
            return toml.dumps(self.deconvert())

        with open(path, "w") as f:
            toml.dump(self.deconvert(), f)
        return os.path.isfile(path)
