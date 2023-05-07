"""Module for ConfigManager class and related functions."""
import json
import logging
import re
import warnings
from collections import UserDict
from typing import Any, Iterable, List, Optional

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
        """Get an attribute or item."""
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
            dict, defaults=defaults, required_keys=required_keys, if_missing=if_missing
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

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path, "r") as f:
            data = load(f)
        return cls(
            data, defaults=defaults, required_keys=required_keys, if_missing=if_missing
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

        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls(
            data, defaults=defaults, required_keys=required_keys, if_missing=if_missing
        ).convert()
