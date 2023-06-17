import json
import os
import pprint
import re
import warnings
from collections import UserList
from typing import Any, Iterable, List, Optional, Union

import yaml
from holy_diver.constants import DEEP_KEY, DEEP_KEY_PROPER
from holy_diver.config_mixin import ConfigMixin


class ConfigList(UserList, ConfigMixin):
    _attr_idx_pat = re.compile(r"^[_]?([0-9]+)$")

    def __init__(
        self,
        data: list = None,
        required_keys: Optional[Iterable[str]] = None,
        if_missing: str = "raise",
    ):
        super().__init__(initlist=data)
        if required_keys is not None:
            self.check_required_keys(required_keys, if_missing=if_missing)

    def check_str_idx(self, idx):
        return isinstance(idx, str) and self._attr_idx_pat.fullmatch(idx) is not None

    def as_int(self, idx):
        return int(self._attr_idx_pat.fullmatch(idx).group(1))

    def __getitem__(self, i):
        if isinstance(i, slice):
            return type(self)(self.data[i]).convert()
        elif self.check_str_idx(i):
            return self.convert().data[self.as_int(i)]
        elif isinstance(i, str) and DEEP_KEY_PROPER.fullmatch(i) is not None:
            return self.deep_get(i)
        else:
            return self.convert().data[i]

    def __setitem__(self, i, item):
        if self.check_str_idx(i):
            i = self.as_int(i)
        self.data[i] = self.convert_item(item)
        # warnings.warn(f"Configuration item {i} set to {item} after initialization!")

    def __getattr__(self, name: str) -> Any:
        """Get an item."""
        return self[self.as_int(name)]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if self.check_str_idx(name):
            self[self.as_int(name)] = value
        else:
            super().__setattr__(name, value)

    def keys(self):
        return [f"_{i}" for i in range(len(self.data))]

    def get(self, key, default=None):
        if key in self.keys():
            return self[key]
        else:
            return default

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
        from holy_diver.config import Config

        if item is None:
            item = self.data
        if isinstance(item, dict):
            return Config({k: self.convert_item(v) for k, v in item.items()})
        if isinstance(item, (list, tuple, set)):
            return type(self)([self.convert_item(x) for x in item])
        return item

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
        from holy_diver.config import Config

        if isinstance(item, Config):
            return {k: self.deconvert_item(v) for k, v in item.items()}
        if isinstance(item, (type(self), tuple, set)):
            return [self.deconvert_item(x) for x in item]
        return item

    def deep_keys(self) -> List[str]:
        """Return a list of all keys in the configuration tree.

        Returns
        -------
        list
            List of all keys in the configuration tree.

        """
        keys = []
        self = self.convert()
        for i in range(len(self.data)):
            keys.append(f"_{i}")
            if isinstance(self.data[i], ConfigMixin):
                for k in self.data[i].deep_keys():
                    keys.append(f"_{i}.{k}")
        return keys

    @classmethod
    def from_list(cls, list: List[Any]) -> "ConfigList":
        """Create a ConfigList from a list.

        Parameters
        ----------
        list : List[Any]
            List to convert.

        Returns
        -------
        ConfigList
            Nested managers created from a list.

        """
        return cls(list).convert()

    @classmethod
    def from_yaml(
        cls,
        path: str,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
        safe: bool = False,
        encoding: str = "utf-8",
    ) -> "ConfigList":
        """Create a ConfigList from a YAML file.

        Parameters
        ----------
        path : str
            Path to YAML file.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration. Defaults to None.
        if_missing : str, optional
            What to do if a required key is missing. Defaults to "raise".
        safe : bool, optional
            If True, load the YAML file safely. Defaults to False.
        encoding : str, optional
            Encoding of the YAML file. Defaults to "utf-8".

        Returns
        -------
        ConfigList
            Nested managers created from a YAML file.

        Raises
        ------
        TypeError
            If the YAML file encodes a dict.

        """
        load = yaml.safe_load if safe else yaml.full_load
        with open(path, encoding=encoding) as f:
            cfg = load(f)
        if isinstance(cfg, dict):
            raise TypeError(
                "YAML file must encode a list, not a dict. "
                "Use `Config.from_yaml` instead."
            )
        return cls(cfg, required_keys=required_keys, if_missing=if_missing).convert()

    @classmethod
    def from_json(
        cls,
        path: str,
        required_keys: Iterable[str] = None,
        if_missing: str = "raise",
        encoding: str = "utf-8",
    ) -> "ConfigList":
        """Create a ConfigList from a JSON file.

        Parameters
        ----------
        path : str
            Path to JSON file.
        required_keys : Iterable[str], optional
            Keys that must be present in the configuration. Defaults to None.
        if_missing : str, optional
            What to do if a required key is missing. Defaults to "raise".
        encoding : str, optional
            Encoding of the JSON file. Defaults to "utf-8".

        Returns
        -------
        ConfigList
            Nested managers created from a JSON file.

        Raises
        ------
        TypeError
            If the JSON file encodes a dict.

        """
        with open(path, encoding=encoding) as f:
            cfg = json.load(f)
        if isinstance(cfg, dict):
            raise TypeError(
                "JSON file must encode a list, not a dict. "
                "Use `Config.from_json` instead."
            )
        return cls(cfg, required_keys=required_keys, if_missing=if_missing).convert()
