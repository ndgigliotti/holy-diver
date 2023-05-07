#!/usr/bin/env python

"""Tests for `deepconfig` package."""

import pytest

from deepconfig.deepconfig import ConfigManager


@pytest.fixture
def log_config():
    """Create a Configuration Manager for logging."""
    config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False,
            },
            "my.packg": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "__main__": {  # if __name__ == '__main__'
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
    return ConfigManager.from_dict(config)


def test_content(log_config):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
