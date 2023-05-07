"""Main module."""
import datetime
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
    + dir({})
)


def check_keys(keys: Iterable[str]) -> None:
    """Check that keys are syntactically valid and not reserved."""
    alphanum = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    dunder = re.compile(r"^__.*__$")
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
        if key in PROTECTED_KEYS:
            raise ValueError(f"Key '{key}' is a reserved attribute or method name.")


class ConfigManager(UserDict):
    _protected_attrs = PROTECTED_KEYS

    def __init__(
        self,
        dict_: dict = None,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
    ) -> None:
        self.data = {}
        if defaults is not None:
            check_keys(defaults.keys())
            self.data.update(defaults)
        if dict_ is not None:
            check_keys(dict_.keys())
            self.data.update(dict_)
        if required_keys is not None:
            self.check_required_keys(required_keys)

    def __getitem__(self, key: str) -> Any:
        """Get an item."""
        return self.convert().data[key]

    def __setitem__(self, key: str, item: Any) -> None:
        """Set an item."""
        self.data[key] = item
        warnings.warn(f"Configuration key '{key}' set to {item} after initialization!")

    def __getattr__(self, name: str) -> Any:
        """Get an attribute or item."""
        if name in self._protected_attrs:
            return super().__getattr__(name)
        else:
            return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if name in self._protected_attrs:
            super().__setattr__(name, value)
        else:
            self[name] = value

    def deep_keys(self) -> List[str]:
        """Return a list of all keys using dot notation."""
        keys = []
        for k, v in self.convert().items():
            keys.append(k)
            if isinstance(v, type(self)):
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

    def convert(self, item: Optional[Any] = None) -> Any:
        """Recursively convert nested dicts to nested ConfigManagers.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to convert, by default None. If None, the ConfigManager itself is converted.

        Returns
        -------
        Any
            Converted item.

        """
        if item is None:
            item = self.data
        if isinstance(item, dict):
            return type(self)({k: self.convert(v) for k, v in item.items()})
        if isinstance(item, (list, tuple, set)):
            return [self.convert(i) for i in item]
        return item

    def deconvert(self, item: Optional[Any] = None) -> Any:
        """Recursively deconvert nested ConfigManagers to nested dicts.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to deconvert, by default None. If None, the ConfigManager itself is deconverted.

        Returns
        -------
        Any
            Deconverted item.

        """
        if item is None:
            item = self
        if isinstance(item, type(self)):
            return {k: self.deconvert(v) for k, v in item.items()}
        if isinstance(item, (list, tuple, set)):
            return [self.deconvert(i) for i in item]
        return item

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
        cls, dict_: dict, defaults: dict = None, required_keys: Iterable[str] = None
    ) -> "ConfigManager":
        """Create nested ConfigManagers from a dictionary.

        Parameters
        ----------
        dict_ : dict
            Dictionary to convert.
        defaults : dict, optional
            Default values to add to the configuration, by default None.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration, by default None.


        Returns
        -------
        ConfigManager
            Nested ConfigManagers created from the dict.

        """
        return cls(dict_, defaults=defaults, required_keys=required_keys).convert()

    @classmethod
    def from_yaml(
        cls,
        path: str,
        defaults: dict = None,
        required_keys: Iterable[str] = None,
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
        safe : bool, optional
            Whether to use safe loading, by default False.

        Returns
        -------
        ConfigManager
            Nested ConfigManagers created from the YAML file.

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path, "r") as f:
            data = load(f)
        return cls(data, defaults=defaults, required_keys=required_keys).convert()

    @classmethod
    def from_json(
        cls, path: str, defaults: dict = None, required_keys: Iterable[str] = None
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

        Returns
        -------
        ConfigManager
            Nested ConfigManagers created from the JSON file.

        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls(data, defaults=defaults, required_keys=required_keys).convert()
