#!/usr/bin/env python
# coding=utf-8
#

# stdlib
import re
from xml.etree import cElementTree as ET
from datetime import datetime

# 3rd party
import requests
from decorating import animated

# self-package
from malpy3.utils import checked_connection, checked_regex, checked_cancer
from malpy3 import setup

config = setup.get_config()


class MyAnimeList(object):
    """Does all the actual communicating with the MAL api."""

    base_url = "https://api.myanimelist.net/v2"
    mal_client_id = "6114d00ca681b7701d1e15fe11a4987e"
    user_agent = "NineAnimator/2 CFNetwork/976 Darwin/18.2.0"

    def __init__(
        self,
        access_token,
        refresh_token,
        date_format=config["config"]["date_format"],
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.date_format = date_format

    @checked_connection
    @animated("validating login")
    def validate_login(self):
        """
        Verify successful login to myanimelist profile.

        Returns:
            Response status code.

        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r = requests.get(self.base_url + "/users/@me", headers=headers)

        return r.status_code

    @classmethod
    def login(cls, config):
        """
        Create an instante of MyAnimeList and log it in.

        Parameters:
            config: Dictionary  with configuration options.

        Return:
            MyAnimeList instance.
        """
        access_token = config["login"]["access_token"]
        refresh_token = config["login"]["refresh_token"]
        date_format = config["config"]["date_format"]

        mal = cls(access_token, refresh_token, date_format)

        # 401 = unauthorized
        if mal.validate_login() == 401:
            return None

        return mal

    @staticmethod
    def get_tokens(username, password):
        """Authenticate user via account username and password to get tokens.

        Parameters:
            username: myanimelist account username.
            password: myanimelist account password.

        Returns:
            Response object.
        """
        url = "https://api.myanimelist.net/v2/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": "6114d00ca681b7701d1e15fe11a4987e",
        }
        r = requests.post(url, headers=headers, data=data)
        return r

    @checked_cancer
    @checked_connection
    @animated("searching in database")
    def search(self, query, limit=20, category="anime"):
        """
        Search myanimelist database for anime/manga.

        Parameters:
            query: regex pattern to search.
            limit: Number of returned results.
            category: Category to search in: Anime or Manga

        Returns:
            Response object.
        """
        fields = [
            "anime_statistics",
            "end_date",
            "genres",
            "id",
            "my_list_status",
            "num_episodes",
            "num_chapters",
            "start_date",
            "status",
            "synopsis",
            "title",
        ]
        headers = {
            "Authorization": f"Bearer: {self.access_token}",
            "Accept": "application/json",
            "User-Agent": f"{self.user_agent}",
            "X-MAL-Client-ID": "6114d00ca681b7701d1e15fe11a4987e",
        }

        payload = dict(q=query, limit=limit, fields=",".join(fields))

        if category == "anime":
            search_url = self.base_url + "/anime"
        elif category == "manga":
            search_url = self.base_url + "/manga"

        r = requests.get(
            search_url,
            params=payload,
            headers=headers,
        )

        if r.status_code == 204:
            return []

        return r

    @checked_cancer
    @checked_connection
    @animated("preparing animes/manga")
    def list(self, status="", limit=100, extra=False, category="anime"):
        """
        Get Anime and Manga from myanimelist profile.

        Parameters:
            status: status to filter results
            limit: Number of returned results.
            extra: Extra anime/manga information.
            category: Category to search in: Anime or Manga.

        Returns:
            Dictionary of parsed anime/manga fields.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-MAL-Client-ID": self.mal_client_id,
        }

        anime_fields = [
            "end_date",
            "media_type",
            "num_episodes",
            "start_date",
            "my_list_status{score,num_episodes_watched,is_rewatching,status,tags}",
        ]
        manga_fields = [
            "authors",
            "end_date",
            "media_type",
            "num_chapters",
            "num_volumes",
            "start_date",
            "my_list_status{score,num_chapters_read,is_rereading,num_volumes_read,status,tags}",
        ]

        if category == "anime":
            ep_chap = "num_episodes_watched"
            fields = anime_fields
            list_url = self.base_url + "/users/@me/animelist"
            total_ep_chap = "num_episodes"
            re_watch_read = "is_rewatching"

        elif category == "manga":
            ep_chap = "num_chapters_read"
            fields = manga_fields
            list_url = self.base_url + "/users/@me/mangalist"
            total_ep_chap = "num_chapters"
            re_watch_read = "is_rereading"

        payload = dict(status=status, limit=limit, fields=",".join(fields))

        r = requests.get(
            list_url,
            params=payload,
            headers=headers,
        )
        result = dict()
        raw_entry = r.json()["data"]

        # anime information
        for entry in raw_entry:
            if entry:
                anime_node = entry.get("node", None)
                my_list_status = anime_node.get("my_list_status")
                list_anime_status = entry.get("list_status", None)

                entry_id = int(anime_node.get("id"))

                result[entry_id] = {
                    "id": entry_id,
                    "title": anime_node.get("title"),
                    "total_episodes": anime_node.get(f"{total_ep_chap}"),
                    "episode": my_list_status.get(f"{ep_chap}"),
                    "status": my_list_status.get("status"),
                    "media_type": anime_node.get("media_type"),
                    "score": my_list_status.get("score"),
                    "is_rewatching": my_list_status.get(f"{re_watch_read}"),
                }

                # add extra info about anime if needed
                if extra:
                    extra_info = {
                        "start_date": self._fdate(
                            anime_node.get("start_date")
                        ),
                        "end_date": self._fdate(anime_node.get("end_date")),
                        "tags": anime_node.get("tags"),
                    }
                    result[entry_id].update(extra_info)

        return result

    def _fdate(self, date, api_format="%Y-%m-%d"):
        """
        Format date based on the user config format

        Parameters:
            date: datetime object.
            api_format: strftime format string
        returns: formatted date string.
        """
        if not date:
            return "NA"
        if any(int(s) == 0 for s in date.split("-")):
            return date
        return datetime.strptime(date, api_format).strftime(self.date_format)

    @checked_regex
    @animated("matching animes/manga")
    def find(
        self, regex, status="", limit=None, extra=False, category="anime"
    ):
        """
        Get anime/manga from user's profile.

        Parameters:
            regex: regex to filter anime/manga titles.
            status: status to filter results.
            limit: Number of returned results.
            extra: Extra anime/manga information.
            category: Category to search in: Anime or Manga.

        Returns:
            List of parsed anime/manga fields.
        """
        result = []
        for value in self.list(
            status=status,
            limit=limit,
            extra=extra,
            category=category,
        ).values():
            if re.search(regex, value["title"], re.I):
                result.append(value)
        return result

    @checked_cancer
    @checked_connection
    @animated("updating")
    def update(self, item_id, entry=None):
        """
        Update anime/manga.

        Parameters:
            item_id: id of anime/manga.
            entry: dict object to patch/update.

        Returns:
            Response status code.
        """
        media_type = entry.get("media_type")
        entry.pop("media_type")

        if media_type == "manga":
            root = "manga"
        else:
            root = "anime"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-MAL-Client-ID": self.mal_client_id,
        }

        payload = entry
        r = requests.patch(
            self.base_url + f"/{root}/{item_id}/my_list_status",
            data=payload,
            headers=headers,
        )
        return r.status_code

    @checked_connection
    def get_user_info(self):
        """
        Get user's information and anime statistics.

        Returns:
            Response object.
        """
        fields = [
            "anime_statistics",
        ]

        payload = dict(fields=",".join(fields))
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        r = requests.get(
            self.base_url + "/users/@me", params=payload, headers=headers
        )
        return r

    @checked_connection
    def get_anime_details(self, _id, entry=None):
        """
        Get anime/manga information

        Parameters:
            _id: id of anime/manga.
            entry: dictionary with status and media_type.

        Return:
            Response object.
        """
        fields = [
            "alternative_titles",
            "average_episode_duration",
            "background",
            "broadcast",
            "created_at",
            "end_date",
            "genres",
            "id",
            "main_picture",
            "mean",
            "media_type",
            "my_list_status",
            "nsfw",
            "num_episodes",
            "num_list_users",
            "num_scoring_users",
            "popularity",
            "rank",
            "rating",
            "recommendations",
            "related_anime",
            "related_manga",
            "source",
            "start_date",
            "start_season",
            "anime_statistics",
            "status",
            "studios",
            "synopsis",
            "title",
            "updated_at",
        ]
        if entry.get("media_type") == "manga":
            info_url = self.base_url + f"/manga/{_id}"
        else:
            info_url = self.base_url + f"/anime/{_id}"

        payload = dict(fields=",".join(fields))
        headers = {
            "Authorization": f"Bearer: {self.access_token}",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-MAL-Client-ID": self.mal_client_id,
        }

        r = requests.get(
            info_url,
            params=payload,
            headers=headers,
        )
        return r
