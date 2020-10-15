#!/usr/bin/env python
# coding=utf-8
#

# stdlib
import os
import sys
import math
import html
import tempfile
import textwrap
import subprocess
from operator import itemgetter
from datetime import date

# self-package
from mal.api import MyAnimeList
from mal.utils import print_error
from mal import color


def wrap_text(text, width=70):
    return "\n".join(
        [textwrap.indent(p, "    ") for p in textwrap.wrap(text, width)]
    )


def report_if_fails(response):
    if response != 200:
        print(color.colorize("Failed with HTTP: {}".format(response), "red"))


def select_item(items):
    """Select a single item from a list of results."""
    item = None
    if len(items) > 1:  # ambigious search results
        print(color.colorize("Multiple results:", "cyan"))
        # show user the results and make them choose one
        for index, title in enumerate(map(itemgetter("title"), items)):
            print("{index}: {title}".format_map(locals()))
        index = int(input("Which one? "))
        item = items[index]
    elif len(items) == 1:
        item = items[0]
    else:
        print(color.colorize("No matches in list ᕙ(⇀‸↼‶)ᕗ", "red"))
        sys.exit(1)

    return item


def start_end(entry, episode, total_episodes):
    """Fill details of anime if user just started it or finished it."""
    if total_episodes == episode:
        entry["status"] = "completed"
        entry["finish_date"] = date.today().strftime("%Y-%m-%d")
        print(color.colorize("Series completed!", "green"))

        # set/change score
        user_score = input(
            "Enter new score (leave blank to keep score at {}): ".format(
                entry.get("score", 0)
            )
        ).strip()
        if user_score:  # do nothing if blank answer
            try:
                entry["score"] = int(user_score)
            except ValueError:
                print(color.colorize("Invalid score.", "red"))

    elif episode == 1:
        if entry.get("media_type") == "manga":
            entry["status"] = "reading"
        else:
            entry["status"] = "watching"

        entry["start_date"] = date.today().strftime("%Y-%m-%d")

    return entry


def remove_completed(items):
    # remove animes that are already completed
    # preserves (rewatching)
    for index, status in enumerate(map(itemgetter("status"), items)):
        if status == "completed":
            del items[index]

    return items


def progress_update(mal, regex, inc=1, category="anime"):
    """
    Increase/Decrease anime or manga progress.

    Parameters:
        mal: An authenticated MyAnimeList class instance.
        regex: regex string to filter anime/manga titles.
        inc: Number to increase/decrease episodes or chapters by.
        category: Category to edit:  anime or manga

    Returns:
        Dictionary object with updated values.
    """
    items = remove_completed(mal.find(regex, category=category))
    item = select_item(items)  # also handles ambigious searches
    epi_chap = item["episode"] + inc

    if item["media_type"] == "manga":
        entry = dict(
            num_chapters_read=epi_chap,
            score=item.get("score", 0),
            media_type="manga",
        )
    else:
        entry = dict(
            num_watched_episodes=epi_chap,
            score=item.get("score", 0),
            media_type="anime",
        )

    template = {
        "title": color.colorize(item["title"], "yellow", "bold"),
        "episode": color.colorize(epi_chap, "red" if inc < 1 else "green"),
        "total_episodes": color.colorize(item["total_episodes"], "cyan"),
        "procedure": color.procedure_color(inc),
    }

    print(
        (
            "{procedure} progress for {title} to "
            "{episode}/{total_episodes}".format_map(template)
        )
    )

    entry = start_end(entry, epi_chap, item["total_episodes"])
    response = mal.update(item["id"], entry)
    report_if_fails(response)


def search(mal, regex, limit=20, full=False, category="anime"):
    """ Search the MAL database for an anime."""
    result = mal.search(regex, limit=limit, category=category).json()["data"]
    # if no results or only one was found we treat them special
    if len(result) == 0:
        print(color.colorize("No matches in MAL database ᕙ(⇀‸↼‶)ᕗ", "red"))
        return
    if len(result) == 1:
        full = True  # full info if only one anime was found

    if category == "anime":
        ep_header = "Episodes"
        ep = "num_episodes"
    elif category == "manga":
        ep_header = "Chapters"
        ep = "num_chapters"

    lines = [
        "{index}: {title}",
        f"  {ep_header} " + ": {episodes}",
        "  Synopsis: {synopsis}",
    ]
    extra_lines = [
        "  Start date: {start}\tEnd date: {end}",
        "  Status: {status}",
    ]

    print(
        "Found",
        color.colorize(str(len(result)), "cyan", "underline"),
        "animes:",
    )
    for i, _anime in enumerate(result):
        # replace tags and special html chars (like &mdash;) with actual characters
        anime = _anime.get("node")
        synopsis = anime.get("synopsis")
        if full:
            synopsis = "\n" + wrap_text(anime.get("synopsis")) + "\n"

        elif len(synopsis) > 70 and not full:
            synopsis = synopsis[:70] + "..."

        # this template/line stuff might need some refactoring
        template = {
            "index": str(i + 1),
            "title": color.colorize(anime.get("title"), "red", "bold"),
            "episodes": color.colorize(anime.get(ep), "white", "bold"),
            "synopsis": synopsis,
            "start": "NA"
            if not (
                anime.get("start_date", None) == "0000-00-00"
                or anime.get("start_date", None)
            )
            else anime.get("start_date"),
            "end": "NA"
            if not (
                anime.get("end_date", None) == "0000-00-00"
                or anime.get("end_date", None)
            )
            else anime.get("end_date"),
            "status": anime.get("status"),
        }
        print("\n".join(line.format_map(template) for line in lines))
        if full:
            print("\n".join(line.format_map(template) for line in extra_lines))
        print("\n")


def drop(mal, regex, category="anime"):
    """
    Drop a anime/manga based a regex expression

    Parameters:
        mal: An authenticated MyAnimeList class instance.
        regex: regex to match Anime/Manga title.
        category: Category to drop from: Anime or Manga

    Returns: None

    """
    items = remove_completed(mal.find(regex, category=category))
    item = select_item(items)
    entry = dict(status="dropped", media_type=item.get("media_type"))
    old_status = item.get("status")
    template = {
        "title": color.colorize(item.get("title"), "yellow", "bold"),
        "old-status": color.colorize(old_status, "green", "bold"),
        "action": color.colorize("Dropping", "red", "bold"),
    }

    print(
        (
            "{action} anime {title} from list "
            "{old-status}".format_map(template)
        )
    )
    response = mal.update(item["id"], entry)
    report_if_fails(response)


def add(mal, regex, status="plan to watch"):
    """Add an entry to the user list."""
    results = mal.search(regex)
    selected = select_item(results)

    print(
        "Adding {title} to list as '{status}'".format(
            title=color.colorize(selected["title"], "yellow", "bold"),
            status=status,
        )
    )
    mal.update(
        selected["id"], {"status": mal.status_codes[status]}, action="add"
    )


def stats(mal, username=None):
    """Print user anime stats."""
    # get all the info
    animes = mal.list(stats=True, user=username)
    if not animes:
        print_error(
            "Empty query",
            "username not found",
            "could not fetch list for user '{}'".format(username),
            kill=True,
        )
    user_info = animes.pop("stats")  # remove stats from anime list

    # gather all the numbers
    total_entries = len(animes)
    rewatched, episodes, mean_score, scored = 0, 0, 0, 0
    for anime in animes.values():
        episodes += anime["episode"]  # this is watched episodes
        if anime["rewatching"] != 0:
            rewatched += anime["rewatching"]
            # take into account episodes seen in previous watchings
            episodes += anime["rewatching"] * anime["total_episodes"]

        if anime["score"] != 0:
            scored += 1
        mean_score += anime["score"]

    if scored != 0:
        mean_score /= scored
    # added two for circle colored + space on each list
    line_size = 44 + 2
    # ↑ code for calculating this was so messy I hardcoded instead
    # it's 20 spaces for each of the 'sides' and 4 spaces in between them

    # colored bar. borrowed the bar char from neofetch
    bar = "█"
    colors = ["green", "blue", "yellow", "red", "gray"]
    lists = ["watching", "completed", "onhold", "dropped", "plantowatch"]
    colored = str()
    if total_entries != 0:  # to prevent division by zero
        for i, status in enumerate(lists):
            entries = int(user_info[status])
            bars = round(line_size * (entries / total_entries))
            colored += color.colorize(bar * bars, colors[i])
    else:
        colored = color.colorize(bar * line_size, "white")

    # format the lines to print more easily afterwards
    template = {
        "days": user_info["days_spent_watching"],
        "mean_score": "{:.2f}".format(mean_score),
        "watching": user_info["watching"],
        "completed": user_info["completed"],
        "hold": user_info["onhold"],
        "plan": user_info["plantowatch"],
        "dropped": user_info["dropped"],
        "total_entries": str(total_entries),
        "episodes": str(episodes),
        "rewatched": str(rewatched),
        "padd": "{p}",  # needed to format with padding afterwards
    }

    def point_color(color_name):
        return color.colorize("● ", color_name, "bold")

    lines = [
        "Days: {days}{padd}Mean Score: {mean_score}",
        colored,
        (
            point_color("green"),
            [
                "Watching:{padd}{watching}",
                "Total Entries:{padd}{total_entries}",
            ],
        ),
        (
            point_color("blue"),
            ["Completed:{padd}{completed}", "Rewatched:{padd}{rewatched}"],
        ),
        (
            point_color("yellow"),
            ["On-Hold:{padd}{hold}", "Episodes:{padd}{episodes}"],
        ),
        (point_color("red"), ["Dropped:{padd}{dropped}"]),
        (point_color("gray"), ["Plan to Watch:{padd}{plan}"]),
    ]
    # add info to lines and format them to look nice
    def padd_str(string, final_size):
        return string.replace(
            "{p}", " " * (final_size - len(string) + len("{p}"))
        )

    lines = [
        padd_str(line.format_map(template), line_size)
        if not isinstance(line, tuple)
        else
        # first format each side, then add padding then join with the tab
        line[0]
        + (" " * 4).join(
            padd_str(side.format_map(template), 20) for side in line[1]
        )
        for line in lines
    ]

    print(color.colorize("Anime Stats", "white", "underline"))
    print("\n".join(lines))


def find(mal, regex, status="", limit=30, extra=False, category="anime"):
    """
    Find all anime in a certain status given a regex.

    Parameters:
        regex: regex to match Anime/Manga title.
        status: status to filter with.
        limit: int to limit result output.
        extra: include additional information
        category: Category to find from: Anime or Manga

    Returns: None

    """
    items = mal.find(
        regex,
        status=status,
        limit=limit,
        extra=extra,
        category=category,
    )
    if len(items) == 0:
        print(color.colorize("No matches in list ᕙ(⇀‸↼‶)ᕗ", "red"))
        return

    # filter the results if necessary
    if status != "":
        items = [x for x in items if x.get("status") == status]

    n_items = color.colorize(str(len(items)), "cyan", "underline")
    print("Matched {} items:".format(n_items))

    # pretty print all the animes found
    sorted_items = sorted(items, key=itemgetter("status"), reverse=True)
    for index, item in enumerate(sorted_items):
        anime_pprint(index + 1, item, extra=extra)


def edit(mal, regex, changes, category="anime"):
    """
    Select and change entry. Opens file with data to change if no
    field was given.

    Parameters:
        mal: An authenticated MyAnimeList class instance.
        regex: regex string to filter anime/manga titles.
        changes: Dictionary with fields to update
        category: Category to edit:  anime or manga

    Return:
        None
    """
    # find the correct entry to modify (handles animes not found)

    entry = select_item(mal.find(regex, extra=True, category=category))

    if not changes:  # open file for user to choose changes manually
        tmp_path = tempfile.gettempdir() + "/mal_tmp"
        editor = os.environ.get("EDITOR", "/usr/bin/vi")
        # write information to tmp file
        with open(tmp_path, "w") as tmp:
            tmp.write('# change fields for "{}"\n'.format(entry["title"]))
            tmp.write("status: {}\n".format(entry["status"]))
            for field in ["score", "tags"]:
                tmp.write("{}: {}\n".format(field, entry[field]))

        # open the file with the default editor
        subprocess.call([editor, tmp_path])

        # read back the data into a dict if any changes were made
        with open(tmp_path, "r") as tmp:
            lines = [
                l
                for l in tmp.read().split("\n")
                if l and not l.startswith("#")
            ]

        # delete tmp file, we don't need it anymore
        os.remove(tmp_path)

        changes = dict()
        for field, value in [tuple(l.split(":")) for l in lines]:
            field, value = field.strip(), value.strip()
            if field == "status":
                value = value
            if str(entry[field]) != value:
                changes[field] = value
        if not changes:
            return

    # change entry
    for field, new in changes.items():
        if field == "add_tags":
            if entry.get("tags") is None:
                entry["tags"] = new
            else:
                entry["tags"] += " " + new
        else:
            entry[field] = new

    # if the entry didn't have a tag before and none was provived by
    # the user as a change we need to remove the entry from the dict
    # to prevent the api from thinking we want to add the 'None' tag
    if entry.get("tags") is None:
        entry.pop("tags")

    # send changes back to patch/update
    changes["media_type"] = category
    response = mal.update(entry["id"], changes)
    report_if_fails(response)


def anime_pprint(index, item, extra=False):
    """
    Pretty print an anime's information.

    Parameters:
        index: Index of object (Used for numbering).
        item : Anime/Manga object
        extra: Print extra information

    Prints formatted colored output.
    """
    if item.get("media_type") == "manga":
        episode_header = "chapters"
        re_read_watch = "#in-rereading"
    else:
        episode_header = "episoses"
        re_read_watch = "#in-rewatching"

    padding = int(math.log10(index)) + 3
    remaining_color = (
        "blue" if item.get("episode") < item.get("total_episodes") else "green"
    )
    remaining = "{episode}/{total_episodes}".format_map(item)
    in_rewatching = (
        f"{re_read_watch}" "-{is_rewatching}".format_map(item)
        if item.get("is_rewatching")
        else ""
    )
    template = {
        "index": index,
        "padding": " " * padding,
        "status": item.get("status").capitalize(),
        "title": color.colorize(item.get("title"), "red", "bold"),
        "remaining": color.colorize(remaining, remaining_color, "bold"),
        "score": color.score_color(item.get("score")),
        "rewatching": (color.colorize(in_rewatching, "yellow", "bold")),
    }
    # add formating options for extra info
    if extra:
        template.update(
            {
                "start": item.get("start_date")
                if item.get("start_date") != "0000-00-00"
                else "NA",
                "finish": item.get("end_date")
                if item["end_date"] != "0000-00-00"
                else "NA",
                "tags": item.get("tags"),
            }
        )

    message_lines = [
        "{index}: {title}".format_map(template),
        (
            "{padding}{status} at {remaining} "
            f"{episode_header} "
            "with score {score} {rewatching}".format_map(template)
        ),
    ]

    # the extra information lines
    if extra:
        message_lines.extend(
            [
                "{padding}Started: {start} \t Finished: {finish}".format_map(
                    template
                ),
                "{padding}Tags: {tags}".format_map(template),
            ]
        )

    print("\n".join(message_lines), "\n")
