#!/usr/bin/env python
# coding=utf-8
#

# stdlib
import sys
import signal
import argparse

# self-package
import malpy3
from malpy3.api import MyAnimeList
from malpy3.utils import killed
from malpy3 import color
from malpy3 import login
from malpy3 import commands
from malpy3 import setup

import decorating

# catch if the user presses Ctrl+c and exit a special message
signal.signal(signal.SIGINT, lambda x, y: killed())


def create_parser():
    parser = argparse.ArgumentParser(
        prog="mal", description="MyAnimeList command line client."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="show the version of malpy3",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="commands",
    )

    # Parser for "search" command
    parser_search = subparsers.add_parser(
        "search", help="search an anime/manga globally on MAL"
    )
    parser_search.add_argument(
        "regex", help="a substring to match anime/manga titles"
    )
    parser_search.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to search: [%(choices)s]",
    )
    parser_search.add_argument(
        "-l",
        "--limit",
        default=30,
        metavar="limit",
        help="limit number of results (default: %(default)s).",
    )
    parser_search.add_argument(
        "--extend",
        "-e",
        action="store_true",  # defaults to false
        help="display extra information about anime/manga",
    )
    parser_search.set_defaults(func=commands.search)

    # Parser for "list" command
    parser_list = subparsers.add_parser(
        "list", help="list anime/manga in users list using status"
    )
    parser_list.add_argument(
        "status",
        nargs="?",
        default="",
        metavar="status",
        choices=[
            "",
            "watching",
            "reading",
            "completed",
            "on hold",
            "dropped",
            "plan to watch",
            "plan to read",
        ],
        help=("filter with status: [%(choices)s] (default: %(default)s)"),
    )
    parser_list.add_argument(
        "-l",
        "--limit",
        default=30,
        metavar="limit",
        help="limit number of results (default: %(default)s).",
    )
    parser_list.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to list: [%(choices)s]",
    )
    parser_list.add_argument(
        "--extend",
        "-e",
        action="store_true",  # defaults to False
        help="display extra info [start/finish dates, tags]",
    )
    parser_list.set_defaults(func=commands.list)
    # Parser for "filter" command
    parser_filter = subparsers.add_parser(
        "filter", help="find anime/manga in users list"
    )
    parser_filter.add_argument(
        "regex",
        nargs="?",
        default="",
        metavar="regex",
        help="regex pattern to match anime/manga titles",
    )
    parser_filter.add_argument(
        "-l",
        "--limit",
        default=30,
        metavar="limit",
        help="limit number of results (default: %(default)s).",
    )
    parser_filter.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to list: [%(choices)s]",
    )
    parser_filter.add_argument(
        "--extend",
        "-e",
        action="store_true",
        help="display all available information on anime/manga",
    )
    parser_filter.set_defaults(func=commands.filter)

    # Parser for "increase" command
    parser_increase = subparsers.add_parser(
        "increase",
        aliases=["inc"],
        help="decrease anime/manga episode or chapter progress (default: +1) ",
    )
    parser_increase.add_argument(
        "regex", default="", help="regex pattern to match anime/manga titles"
    )
    parser_increase.add_argument(
        "episodes",
        nargs="?",
        type=int,
        default=1,
        help="number of episodes/chapters to increase",
    )
    parser_increase.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to increase episodes/chapters: [%(choices)s]",
    )
    parser_increase.set_defaults(func=commands.increase)

    # Parser for "decrease" command
    parser_decrease = subparsers.add_parser(
        "decrease",
        aliases=["dec"],
        help="decrease anime/manga episode or chapter progress (default: -1) ",
    )
    parser_decrease.add_argument(
        "regex", help="regex pattern to match anime/manga titles"
    )
    parser_decrease.add_argument(
        "episodes",
        nargs="?",
        type=int,
        default=1,
        help="number of episodes to decrease",
    )
    parser_decrease.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to decrease episodes/chapters: [%(choices)s]",
    )

    parser_decrease.set_defaults(func=commands.decrease)

    # Parser for "login" command
    parser_login = subparsers.add_parser(
        "login", help="login to MAL and save access tokens"
    )
    parser_login.set_defaults(func=commands.login)

    # Parser for "config" command
    parser_config = subparsers.add_parser(
        "config", help="Print current config file and its path"
    )

    # Parser for "drop" command
    parser_drop = subparsers.add_parser(
        "drop", help="Put a selected anime/manga on drop list"
    )
    parser_drop.add_argument(
        "regex", help="regex pattern to match anime/manga titles"
    )
    parser_drop.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to decrease episodes/chapters: [%(choices)s]",
    )
    parser_drop.set_defaults(func=commands.drop)

    # Parser for "stats" command
    parser_stats = subparsers.add_parser(
        "stats", help="Show user's anime watch stats"
    )
    parser_stats.set_defaults(func=commands.stats)

    # Parser for "add" command
    parser_add = subparsers.add_parser(
        "add", help="add an anime/manga to the list"
    )
    parser_add.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to add from: [%(choices)s]",
    )
    parser_add_group = parser_add.add_mutually_exclusive_group()
    parser_add_group.add_argument(
        "--regex",
        "-r",
        metavar="regex",
        default="",
        help="regex pattern to match anime/manga titles",
    )
    parser_add_group.add_argument(
        "--id", "-i", metavar="id", help="anime/manga id to add"
    )
    parser_add.add_argument(
        "--status",
        "-s",
        type=str,
        nargs="?",
        metavar="status",
        choices=[
            "watching",
            "reading",
            "completed",
            "on hold",
            "dropped",
            "plan to watch",
            "plan to read",
        ],
        default="plan to watch",
        help="add anime/manga with this status [%(choices)s] (default: %(default)s)",
    )
    parser_add.set_defaults(func=commands.add)

    # Parser for "edit" command
    parser_edit = subparsers.add_parser("edit", help="edit anime/manga")
    parser_edit.add_argument(
        "regex", help="regex pattern to match anime titles"
    )
    parser_edit.add_argument(
        "--score",
        metavar="score",
        type=int,
        help="score to assign anime/manga",
    )
    parser_edit.add_argument(
        "--status",
        metavar="status",
        choices=[
            "watching",
            "reading",
            "completed",
            "on hold",
            "dropped",
            "plan to watch",
            "plan to read",
        ],
        help="status to assign to entry: [%(choices)s]",
    )
    parser_edit.add_argument(
        "--cat",
        "-c",
        default="anime",
        metavar="category",
        choices=["anime", "manga"],
        help="Category to edit from: [%(choices)s]",
    )
    parser_edit_tags = parser_edit.add_mutually_exclusive_group()
    parser_edit_tags.add_argument(
        "--set-tags",
        nargs="+",
        metavar="tag",
        dest="tags",
        help="space separated list of tags" " (replaces current tags)",
    )
    parser_edit_tags.add_argument(
        "--add-tags",
        nargs="+",
        metavar="tag",
        help="add these tags to the current ones",
    )
    parser_edit.set_defaults(func=commands.edit)

    return parser


def main():
    parser = create_parser()
    # Parse arguments
    if len(sys.argv) <= 1:
        args = parser.parse_args(["-h"])
    else:
        args = parser.parse_args()

    if args.version:
        print(malpy3.__version__)
        sys.exit(0)

    if args.command == "config":
        setup.print_config()
        sys.exit(0)

    # if the command is login, create credentials and exits
    # NOTE: if this statement is removed the `mal login` and
    # no credentials exists, login.create_credentials() will
    # be called twice! On login.get_credentials and args.func(mal, args)
    if args.command == "login":
        login.create_credentials()
        sys.exit(0)

    # Check if authorized
    config = login.get_credentials()
    if not config["config"]["animation"]:
        decorating.animated.enabled = False

    mal_api = MyAnimeList.login(config)
    if not mal_api:
        print(color.colorize("Invalid credentials! :(", "red", "bold"))
        print(color.colorize('Tip: Try "mal login" again :D', "white", "bold"))
        sys.exit(1)

    # Execute sub command
    args.func(mal_api, args)


if __name__ == "__main__":
    main()
