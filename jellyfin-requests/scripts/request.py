#! /usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.12.5",
#     "requests>=2.32.5",
#     "toon-format>=0.9.0b1"
# ]
# ///

import os
from argparse import ArgumentParser
from datetime import date
from enum import Enum, auto
from typing import Annotated, Any, Literal

from urllib.parse import quote, urlencode

import requests
import toon_format as toon
from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    Field,
    ValidationError,
    PlainSerializer,
    field_validator,
)
from requests.auth import AuthBase

MediaType = Literal["movie", "tv"]


class SeerrMediaStatus_(Enum):
    MISSING = auto()
    PENDING = auto()
    PROCESSING = auto()
    PARTIALLY_AVAILABLE = auto()
    AVAILABLE = auto()
    DELETED = auto()


SeerrMediaStatus = Annotated[
    SeerrMediaStatus_, PlainSerializer(lambda value: value.name, return_type=str)
]


class ApiKeyAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: requests.PreparedRequest):
        r.headers["X-Api-Key"] = self.token

        return r


class SearchResult(BaseModel, frozen=True):
    id: int
    media_type: Annotated[
        MediaType,
        Field(
            validation_alias="mediaType",
        ),
    ]
    title: Annotated[
        str, Field(validation_alias=AliasChoices("originalTitle", "originalName"))
    ]
    overview: str
    release_date: Annotated[
        date,
        Field(
            default=None, validation_alias=AliasChoices("releaseDate", "firstAirDate")
        ),
    ]


class SeasonStatus(BaseModel, frozen=True):
    season_number: Annotated[int, Field(validation_alias="seasonNumber")]
    status: SeerrMediaStatus


class MediaStatus(BaseModel, frozen=True):
    id: int
    name: Annotated[str, Field(validation_alias=AliasChoices("name", "title"))]
    status: Annotated[
        SeerrMediaStatus, Field(validation_alias=AliasPath("mediaInfo", "status"))
    ]
    seasons: Annotated[
        list[SeasonStatus] | None,
        Field(validation_alias=AliasPath("mediaInfo", "seasons")),
    ] = None

    @field_validator("seasons")
    @staticmethod
    def validate_seasons(value):
        if isinstance(value, list) and len(value) == 0:
            return None

        return value


class CommandHandler:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        api_key = api_key or os.getenv("SEERR_API_KEY")

        if not api_key:
            raise ValueError("No Seerr API key was provided")

        self.auth = ApiKeyAuth(api_key)

        base_url = base_url or os.getenv("SEERR_URL")

        if not base_url:
            raise ValueError("No Seerr URL was provided")

        self.base_url = base_url.rstrip("/") + "/api/v1"

    def search_media(self, query: str) -> list[SearchResult]:
        # Seerr doesn't support + encoding for search queries
        params = urlencode({"query": query}, quote_via=quote)

        res = requests.get(
            f"{self.base_url}/search?{params}",
            auth=self.auth,
        )

        results = []
        for result in res.json()["results"]:
            if len(results) >= 5:
                break

            try:
                results.append(SearchResult.model_validate(result))
            except ValidationError:
                pass

        return results

    def add_request(
        self, media_type: MediaType, id: int, seasons: list[str] | None = None
    ) -> str:
        body: dict[str, Any] = {"mediaType": media_type, "mediaId": id}

        if seasons:
            body["seasons"] = seasons

        res = requests.post(f"{self.base_url}/request", json=body, auth=self.auth)

        if not res.ok:
            try:
                message = res.json()["message"]
            except Exception:
                message = "Unknown error"

            return f"{res.reason}: {message}"

        return res.reason

    def get_available(self, media_type: MediaType, id: int) -> MediaStatus:
        if media_type == "tv":
            url = f"{self.base_url}/tv/{id}"
        else:
            url = f"{self.base_url}/movie/{id}"

        res = requests.get(url, auth=self.auth)

        return MediaStatus.model_validate_json(res.content)


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

    get_available_parser = subparsers.add_parser(
        "get_available", help="Check current availability status in library"
    )
    get_available_parser.add_argument(
        "--media-type", choices=("movie", "tv"), required=True
    )
    get_available_parser.add_argument("media_id", type=int)

    args = parser.parse_args()

    handler = CommandHandler()

    match args.command:
        case "search":
            results = [
                media.model_dump(mode="json")
                for media in handler.search_media(args.query)
            ]
            print(toon.encode({"results": results}))
        case "add_movie":
            print(handler.add_request("movie", args.media_id))
        case "add_tv":
            print(handler.add_request("tv", args.media_id, args.seasons))
        case "get_available":
            print(
                toon.encode(
                    handler.get_available(args.media_type, args.media_id).model_dump(
                        exclude_none=True, mode="json"
                    )
                )
            )


if __name__ == "__main__":
    main()
