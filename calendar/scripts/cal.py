#! /usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pydantic>=2.12.5",
#     "caldav>=3.2.0",
#     "toon-format>=0.9.0b1"
# ]
# ///

"""
usage: cal.py [-h] {get_events,get_event,create_event} ...

positional arguments:
  {get_events,get_event,create_event}
    get_events          Get events from a caldav calendar
    get_event           Get a single event from a caldav calendar
    create_event        Create a single event in a caldav calendar

options:
  -h, --help            show this help message and exit
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from datetime import date, datetime
from typing import Self
from uuid import uuid7
from zoneinfo import ZoneInfo

import toon_format as toon
from caldav.calendarobjectresource import Event
from caldav.davclient import get_calendar, get_davclient
from pydantic import BaseModel

DEFAULT_TIMEZONE = ZoneInfo("America/New_York")


class CalendarEvent(BaseModel):
    id: str
    url: str
    summary: str
    location: str | None = None
    start: date | datetime
    end: date | datetime

    @classmethod
    def from_event(cls, event: Event) -> Self:
        ical_component = event.get_icalendar_component()
        return cls(
            id=str(ical_component.uid),
            url=str(event.url),
            summary=str(ical_component.summary),
            location=str(ical_component.location) if ical_component.location else None,
            start=ical_component.start,
            end=ical_component.end,
        )


def safe_date_parse(date_str: str, strict: bool = True) -> date | datetime | None:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            if strict:
                raise ValueError(f"Invalid date format: {date_str}")
            return None


class CommandHandler:
    def get_events(
        self,
        start: str | None = None,
        end: str | None = None,
    ) -> list[CalendarEvent]:
        with get_calendar() as calendar:
            events = calendar.search(
                event=True,
                start=safe_date_parse(start) if start else None,
                end=safe_date_parse(end) if end else None,
                expand=bool(start and end),
            )

            return [CalendarEvent.from_event(event) for event in events]

    def get_event(self, event_id: str) -> CalendarEvent | None:
        with get_davclient() as client:
            calendar = client.get_principal().calendar()

            resp = client.request(f"{calendar.url}{event_id}.ics", method="GET")

            try:
                event = Event(data=resp.raw, url=f"{calendar.url}{event_id}.ics")
            except AssertionError:
                return None

            return CalendarEvent.from_event(event)

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        location: str | None = None,
        timezone: str | None = None,
    ) -> CalendarEvent:
        dtstart = safe_date_parse(start, strict=True)
        dtend = safe_date_parse(end, strict=True)

        tz = ZoneInfo(timezone) if timezone else DEFAULT_TIMEZONE

        if isinstance(dtstart, datetime):
            dtstart = dtstart.replace(tzinfo=tz)
        if isinstance(dtend, datetime):
            dtend = dtend.replace(tzinfo=tz)

        with get_calendar() as calendar:
            event = calendar.add_event(
                summary=summary,
                uid=str(uuid7()),
                dtstart=dtstart,
                dtend=dtend,
                location=location,
            )

            breakpoint()

            return CalendarEvent.from_event(event)


def main(args: Namespace):
    handler = CommandHandler()

    match args.command:
        case "get_events":
            events = handler.get_events(args.start, args.end)
            print(
                toon.encode(
                    {"events": [event.model_dump(mode="json") for event in events]}
                )
                if events
                else "No events."
            )
        case "get_event":
            event = handler.get_event(args.event_id)
            print(
                toon.encode(event.model_dump(mode="json"))
                if event
                else "Event not found."
            )
        case "create_event":
            event = handler.create_event(
                args.summary,
                start=args.start,
                end=args.end,
                location=args.location,
                timezone=args.timezone,
            )
            print(toon.encode({"created_event": event.model_dump(mode="json")}))


if __name__ == "__main__":
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_events_subparser = subparsers.add_parser(
        "get_events", help="Get events from a caldav calendar"
    )
    get_events_subparser.add_argument(
        "--cal-id", type=str, help="The ID of the calendar to get events from"
    )
    get_events_subparser.add_argument(
        "--start",
        type=date.fromisoformat,
        help="The start date to search for events from (inclusive)",
    )
    get_events_subparser.add_argument(
        "--end",
        type=date.fromisoformat,
        help="The end date to search for events until (inclusive)",
    )

    get_event_subparser = subparsers.add_parser(
        "get_event", help="Get a single event from a caldav calendar"
    )
    get_event_subparser.add_argument(
        "event_id", type=str, help="The ID of the event to get"
    )

    create_event_subparser = subparsers.add_parser(
        "create_event", help="Create a single event in a caldav calendar"
    )
    create_event_subparser.add_argument(
        "summary", type=str, help="The summary of the event to create"
    )
    create_event_subparser.add_argument(
        "--start", type=str, help="The start date of the event to create"
    )
    create_event_subparser.add_argument(
        "--end", type=str, help="The end date of the event to create"
    )
    create_event_subparser.add_argument(
        "--location", type=str, help="The location of the event to create"
    )
    create_event_subparser.add_argument(
        "--timezone",
        type=str,
        help="IANA timezone name (e.g. America/Chicago); overrides tzinfo on start/end timestamps",
    )

    args = parser.parse_args()

    main(args)
