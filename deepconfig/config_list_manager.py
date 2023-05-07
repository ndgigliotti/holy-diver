import re
from collections import UserList
from typing import Any, List


class ConfigListManager(UserList):
    _attr_index_pattern = re.compile(r"^_[0-9]+$")

    def __getattr__(self, name: str) -> Any:
        """Get an attribute or item."""
        if self._attr_index_pattern.fullmatch(name):
            return self.data[int(name[1:])]
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute or item."""
        if self._attr_index_pattern.fullmatch(name):
            self.data[int(name[1:])] = value
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
        from deepconfig.config_manager import ConfigManager

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
        from deepconfig.config_manager import ConfigManager

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
        from deepconfig.config_manager import ConfigManager

        keys = []
        self = self.convert()
        for i in range(len(self.data)):
            if isinstance(self.data[i], (type(self), ConfigManager)):
                for k in self.data[i].deep_keys():
                    keys.append(f"_{i}.{k}")
            else:
                keys.append(f"_{i}")
        return keys

    @property
    def depth(self) -> int:
        """Return the depth of the configuration tree."""
        return max([k.count(".") for k in self.deep_keys()])
