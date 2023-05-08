import json
import re
import warnings
from collections import UserList
from typing import Any, List

import yaml


class ConfigListManager(UserList):
    _attr_index_pattern = re.compile(r"^_[0-9]+$")

    def __getitem__(self, i):
        if isinstance(i, slice):
            return type(self)(self.data[i]).convert()
        else:
            return self.convert().data[i]

    def __setitem__(self, i, item):
        self.data[i] = item
        warnings.warn(f"Configuration item {i} set to {item} after initialization!")

    def __getattr__(self, name: str) -> Any:
        """Get an attribute or item."""
        if self._attr_index_pattern.fullmatch(name):
            # return self.convert().data[int(name[1:])]
            return self[int(name[1:])]
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if self._attr_index_pattern.fullmatch(name):
            self[int(name[1:])] = value
        else:
            super().__setattr__(name, value)

    def keys(self):
        return [f"_{i}" for i in range(len(self.data))]

    def convert_item(self, item: Any) -> Any:
        """Recursively convert nested dicts and lists to nested managers.

        Parameters
        ----------
        item : Optional[Any], optional
            Item to convert.

        Returns
        -------
        Any
            Converted item.

        """
        from dot_config.config_manager import ConfigManager

        if item is None:
            item = self.data
        if isinstance(item, dict):
            return ConfigManager({k: self.convert_item(v) for k, v in item.items()})
        if isinstance(item, (list, tuple, set)):
            return type(self)([self.convert_item(x) for x in item])
        return item

    def convert(self) -> "ConfigListManager":
        """Recursively convert nested dicts and lists to nested managers.

        Returns
        -------
        ConfigListManager
            New hierarchy of managers and values.

        """
        return self.convert_item(self.data)

    def deconvert_item(self, item: Any) -> Any:
        """Recursively deconvert nested managers to nested dicts and lists.

        Parameters
        ----------
        item :Any
            Item to deconvert.

        Returns
        -------
        Any
            Deconverted item.

        """
        from dot_config.config_manager import ConfigManager

        if isinstance(item, ConfigManager):
            return {k: self.deconvert_item(v) for k, v in item.items()}
        if isinstance(item, (type(self), tuple, set)):
            return [self.deconvert_item(x) for x in item]
        return item

    def deconvert(self) -> Any:
        """Recursively deconvert nested managers to nested dicts and lists.

        Returns
        -------
        Any
            New hierarchy of dicts and lists.

        """
        return self.deconvert_item(self)

    def deep_keys(self) -> List[str]:
        """Return a list of all keys in the configuration tree.

        Returns
        -------
        list
            List of all keys in the configuration tree.

        """
        from dot_config.config_manager import ConfigManager

        keys = []
        self = self.convert()
        for i in range(len(self.data)):
            keys.append(f"_{i}")
            if isinstance(self.data[i], (type(self), ConfigManager)):
                for k in self.data[i].deep_keys():
                    keys.append(f"_{i}.{k}")
        return keys

    @property
    def depth(self) -> int:
        """Return the depth of the configuration tree."""
        return max([k.count(".") for k in self.deep_keys()])

    @classmethod
    def from_list(cls, list: List[Any]) -> "ConfigListManager":
        """Create a ConfigListManager from a list.

        Parameters
        ----------
        list : List[Any]
            List to convert.

        Returns
        -------
        ConfigListManager
            Nested managers created from a list.

        """
        return cls(list).convert()

    @classmethod
    def from_yaml(cls, path: str, safe: bool = False) -> "ConfigListManager":
        """Create a ConfigListManager from a YAML file.

        Parameters
        ----------
        path : str
            Path to YAML file.
        safe : bool, optional
            If True, load the YAML file safely. Defaults to False.

        Returns
        -------
        ConfigListManager
            Nested managers created from a YAML file.

        Raises
        ------
        TypeError
            If the YAML file encodes a dict.

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path, "r") as f:
            cfg = load(f)
        if isinstance(cfg, dict):
            raise TypeError(
                "YAML file must encode a list, not a dict. "
                "Use `ConfigManager.from_yaml` instead."
            )
        return cls(cfg).convert()

    def to_string(self) -> str:
        """Convert the ConfigListManager to a string.

        Returns
        -------
        str
            String representation of the ConfigListManager.

        """
        return yaml.dump(self.deconvert())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.data)})"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def from_json(cls, path: str) -> "ConfigListManager":
        """Create a ConfigListManager from a JSON file.

        Parameters
        ----------
        path : str
            Path to JSON file.

        Returns
        -------
        ConfigListManager
            Nested managers created from a JSON file.

        Raises
        ------
        TypeError
            If the JSON file encodes a dict.

        """
        with open(path, "r") as f:
            cfg = json.load(f)
        if isinstance(cfg, dict):
            raise TypeError(
                "JSON file must encode a list, not a dict. "
                "Use `ConfigManager.from_json` instead."
            )
        return cls(cfg).convert()
