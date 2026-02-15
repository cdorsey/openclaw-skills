#! /usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.12.5",
#     "requests>=2.32.5",
# ]
# ///

import os
from argparse import ArgumentParser
from datetime import date
from typing import Annotated, Any, Literal

from urllib.parse import quote, urlencode

import requests
from pydantic import AliasChoices, BaseModel, Field, field_validator
from requests.auth import AuthBase

MediaType = Literal["movie", "tv"]


class ApiKeyAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: requests.PreparedRequest):
        r.headers["X-Api-Key"] = self.token

        return r


class MediaResult(BaseModel):
    id: int
    media_type: Annotated[MediaType, Field(validation_alias="mediaType")]
    title: Annotated[
        str, Field(validation_alias=AliasChoices("originalTitle", "originalName"))
    ]
    overview: str
    release_date: Annotated[
        date | None, Field(default=None, validation_alias=AliasChoices("releaseDate", "firstAirDate"))
    ]

    @field_validator("release_date", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CommandHandler:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        api_key = api_key or os.getenv("SEERR_API_KEY")

        if not api_key:
            raise ValueError("No Seerr API key was provided")

        self.auth = ApiKeyAuth(api_key)

        base_url = base_url or os.getenv("SEERR_URL")

        if not base_url:
            raise ValueError("No Seerr URL was provided")

        self.base_url = base_url.rstrip("/")

    def search_media(self, query: str) -> list[MediaResult]:
        # Seerr doesn't support + encoding for search queries
        params = urlencode({"query": query}, quote_via=quote)

        res = requests.get(
            f"{self.base_url}/api/v1/search?{params}",
            auth=self.auth,
        )

        results = res.json()["results"]

        return [
            MediaResult.model_validate(result)
            for result in results
            if result["mediaType"] in ("movie", "tv")
            ][:5]

    def add_request(
        self, media_type: MediaType, id: int, seasons: list[str] | None = None
    ) -> str:
        body: dict[str, Any] = {"mediaType": media_type, "mediaId": id}

        if seasons:
            body["seasons"] = seasons

        res = requests.post(
            f"{self.base_url}/api/v1/request", json=body, auth=self.auth
        )

        if not res.ok:
            try:
                message = res.json()["message"]
            except Exception:
                message = "Unknown error"

            return f"{res.reason}: {message}"

        return res.reason


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search for media")
    search_parser.add_argument("query", help="Search query")

    add_movie_parser = subparsers.add_parser(
        "add_movie", help="Add a new request for a movie"
    )
    add_movie_parser.add_argument("media_id", type=int, help="The media ID to request")

    add_tv_parser = subparsers.add_parser(
        "add_tv", help="Add a new request for a tv show"
    )
    add_tv_parser.add_argument("media_id", type=int, help="The media ID to request")
    add_tv_parser.add_argument(
        "--seasons",
        nargs="*",
        type=int,
        help="Seasons to request (defaults to all seasons)",
    )

    args = parser.parse_args()

    handler = CommandHandler()

    match args.command:
        case "search":
            for media in handler.search_media(args.query):
                print(media.model_dump_json())
        case "add_movie":
            print(handler.add_request("movie", args.media_id))
        case "add_tv":
            print(handler.add_request("tv", args.media_id, args.seasons))


if __name__ == "__main__":
    main()
