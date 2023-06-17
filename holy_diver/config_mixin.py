import json
import os
import pprint
import re
import abc
from typing import Any, Iterable, Optional, Union
import warnings

import yaml
from holy_diver.constants import DEEP_KEY


class ConfigMixin(abc.ABC):
    @abc.abstractmethod
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
        pass

    def convert(self) -> "ConfigMixin":
        """Recursively convert nested dicts and lists to nested managers.

        Returns a copy of self.

        Returns
        -------
        Config
            New hierarchy of managers and values.

        """
        return self.convert_item(self.data)

    @abc.abstractmethod
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
        pass

    def deconvert(self) -> dict:
        """Recursively deconvert nested managers to nested dicts and lists.

        Returns a copy.

        Returns
        -------
        dict
            Deconverted hierarchy of dicts and lists.

        """
        return self.deconvert_item(self)

    @abc.abstractmethod
    def deep_keys(self) -> list[str]:
        """Return a list of all keys using dot notation."""
        pass

    def deep_get(self, key: str) -> Any:
        """Get a value using dot notation."""
        if DEEP_KEY.fullmatch(key) is None:
            raise ValueError(f"Key '{key}' is not a valid deep key.")
        keys = key.split(".")
        value = self.convert()
        for k in keys:
            try:
                value = value[k]
            except KeyError:
                raise KeyError(f"Key '{key}' not found.")
        return value

    def deep_items(self) -> list[str]:
        """Return a list of tuples of deep keys and values."""
        return [(k, self.deep_get(k)) for k in self.deep_keys()]

    def set_deep_key(self, key: str, value: Any) -> None:
        """Set a value using dot notation."""
        raise NotImplementedError("This method is not yet implemented.")
        if DEEP_KEY.fullmatch(key) is None:
            raise ValueError(f"Key '{key}' is not a valid deep key.")
        keys = key.split(".")
        item = self
        for k in keys[:-1]:
            item = item.get(k, {})
        item[keys[-1]] = value

    def check_required_keys(
        self, keys: Iterable[str], if_missing: str = "raise"
    ) -> list[str]:
        """Check that the config has the required keys.

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

    @property
    def depth(self) -> int:
        """Return the depth of the configuration tree."""
        return max([k.count(".") for k in self.deep_keys()])

    def search(
        self, key: str, regex=False, return_values=False
    ) -> Union[dict[str, Any], list[Any]]:
        """Search for a key in the configuration tree.

        Parameters
        ----------
        key : str
            Key or key pattern to search for. Will be matched against
            the lowest key in the hierarchy. If `regex` is False, must be
            an exact match. If `regex` is True, will try to match the
            lowest key using `re.search`.
        regex : bool, optional
            Whether to use regex pattern matching, by default False.
        return_values : bool, optional
            Whether to return a list of values instead of a dictionary,
            by default False.

        Returns
        -------
        Union[dict[str, Any], list[Any]]
            Dictionary of keys and values, or list of values.

        """
        results = {}
        for k, v in self.deep_items():
            final_key = k.split(".")[-1]
            if regex:
                if re.search(key, final_key) is not None:
                    results[k] = v
            else:
                if final_key == key:
                    results[k] = v
        return list(results.values()) if return_values else results

    def to_string(self) -> str:
        """Convert the configuration manager to a string.

        Returns
        -------
        str
            String representation of the configuration.

        """
        return pprint.pformat(self.deconvert())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.data)})"

    def __str__(self) -> str:
        return self.to_string()

    def to_yaml(
        self, path: Optional[str] = None, encoding: str = "utf-8"
    ) -> Union[str, bool]:
        """Write the configuration to a YAML file.

        If `path` is None, return the YAML string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str, optional
            Path to YAML file.
        encoding : str, optional
            Encoding of the YAML file, by default "utf-8".

        Returns
        -------
        str or bool
            YAML string or True if successful.
        """
        if path is None:
            return yaml.dump(self.deconvert())

        with open(path, "w", encoding=encoding) as f:
            yaml.dump(self.deconvert(), f)
        return os.path.isfile(path)

    def to_json(
        self, path: Optional[str] = None, encoding: str = "utf-8"
    ) -> Union[str, bool]:
        """Write the configuration to a JSON file.

        If `path` is None, return the JSON string. Otherwise, write
        to the file at `path` and return True if successful.

        Parameters
        ----------
        path : str, optional
            Path to JSON file.
        encoding : str, optional
            Encoding of the JSON file, by default "utf-8".

        Returns
        -------
        str or bool
            JSON string or True if successful.

        """
        if path is None:
            return json.dumps(self.deconvert())

        with open(path, "w", encoding=encoding) as f:
            json.dump(self.deconvert(), f)
        return os.path.isfile(path)
