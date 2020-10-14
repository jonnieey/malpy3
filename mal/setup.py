#!/usr/bin/env python
# coding=utf-8


# stdlib
from pathlib import Path
import textwrap
import toml

# 3rd party
from xdg import XDG_CONFIG_HOME
import decorating

# self-package
from mal import __name__ as APP_NAME

# variables for proper saving
APP_FILE = "myanimelist.toml"
CONFIG_PATH = Path(XDG_CONFIG_HOME) / APP_NAME / APP_FILE

DEFAULT_CONFIG = """
[config]
    animation = true
    date_format = "%Y-%m-%d"
[login]
    access_token = ""
    refresh_token = ""
"""


def get_config():
    """
    Create a toml configuration file or read if it exists

    Returns:
        Dictionary with configuration options.
    """
    if CONFIG_PATH.exists():
        try:
            config = toml.load(CONFIG_PATH.absolute())
            return config

        except Exception as e:
            return toml.loads(DEFAULT_CONFIG)

    else:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as f:
            f.write(textwrap.dedent(DEFAULT_CONFIG).lstrip("\n"))

        return toml.loads(DEFAULT_CONFIG)


@decorating.cache
def date_format():
    """Get current date format from config file"""
    return get_config()["config"]["date_format"]


def print_config():
    """Print current config and its PATH"""
    print("\nFile on: {}\n".format(CONFIG_PATH))
    with open(CONFIG_PATH, "r") as f:
        print(f.read())
