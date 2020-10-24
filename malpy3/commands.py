#!/usr/bin/env python
# coding=utf-8
#

"""These function serve as an entry point for the several subcommands
of malpy3. All they do is basically call the functions that do actual work
in the core module."""

# stdlib
import sys

# self-package
from malpy3 import core
from malpy3 import login as _login
from malpy3 import setup


def search(mal, args):
    """Search MAL (not just the user) anime database."""
    core.search(
        mal,
        args.regex.lower(),
        extra=args.extend,
        limit=args.limit,
        category=args.cat,
    )


def filter(mal, args):
    """Search and find an anime in the users list."""
    core.find(
        mal,
        args.regex.lower(),
        limit=args.limit,
        extra=args.extend,
        category=args.cat,
    )


def increase(mal, args):
    core.progress_update(
        mal, args.regex.lower(), inc=args.episodes, category=args.cat
    )


def decrease(mal, args):
    core.progress_update(
        mal, args.regex.lower(), inc=-args.episodes, category=args.cat
    )


def login(mal, args):
    """Creates login credentials so that next time the program is called
    it can log in right at the start without any problem."""
    _login.create_credentials()
    sys.exit(0)


def list(mal, args):
    """Show all the animes on the users list."""
    # . matches any character except line breaks
    # + matches one or more occurences of the previous character
    core.find(
        mal,
        ".+",
        args.status.replace(" ", "_"),
        limit=args.limit,
        extra=args.extend,
        category=args.cat,
    )


def drop(mal, args):
    """Drop a anime from lists based in a regex expression"""
    core.drop(mal, args.regex, category=args.cat)


def stats(mal, args):
    """Show the user's anime watching statistics as presented on MAL."""
    core.stats(mal)


def add(mal, args):
    """Add an anime with a certain status to the list."""
    core.add(
        mal,
        args.regex.lower(),
        _id=args.id,
        status=args.status.replace(" ", "_"),
        category=args.cat,
    )


def edit(mal, args):
    """Edit an entry in the users list, if it was present. Notify otherwise."""
    changes = dict()
    for field in ["score", "status", "tags", "add_tags"]:
        attr = getattr(args, field)
        if attr is not None:
            if isinstance(attr, int):
                changes[field] = attr
            else:
                changes[field] = attr.replace(" ", "_")

    # turn list of tags into a single string if needed
    for field in ["tags", "add_tags"]:
        if field in changes.keys():
            changes[field] = " ".join(changes[field])

    core.edit(mal, args.regex.lower(), changes, category=args.cat)


def delete(mal, args):
    core.delete(mal, regex=args.regex, _id=args.id, category=args.cat)
