#!/usr/bin/env python
# coding=utf-8
#

# stdlib
from os import makedirs
from getpass import getpass

# 3rd party
import toml

# self-package
from malpy3.api import MyAnimeList
from malpy3 import color
from malpy3 import setup


def get_credentials():
    """Fetch the username and password from the right file."""
    config = setup.get_config()
    if config.get("login").get("access_token", "") == "":
        config = create_credentials()

    return config


def create_credentials():
    # logging messages
    login_header = color.colorize("-- MAL login", "cyan")
    successful = color.colorize(":: valid credentials!", "green")
    invalid = color.colorize(":: invalid credentials! try again", "red")
    print(login_header)

    config = setup.get_config()
    if not config["config"]["animation"]:
        config["config"]["animation"] = "True"
    elif not config["config"]["date_format"]:
        config["config"]["date_format"] = "%Y-%m-%d"

    username = input("Username: ")
    password = getpass()
    tokens = MyAnimeList.get_tokens(username, password).json()

    config["login"]["access_token"] = tokens.get("access_token")
    config["login"]["refresh_token"] = tokens.get("refresh_token")

    # confirm that account credentials are correct by trying to log in
    if MyAnimeList.login(config):
        # account is ok, create a config file
        toml.dump(config, setup.CONFIG_PATH.open("w"))
        print(successful, "saved in {}".format(setup.CONFIG_PATH))
    else:
        print(invalid)
        config = create_credentials()
    return config
