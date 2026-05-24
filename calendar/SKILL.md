---
name: calendar
description: Interact with the user's calendar
metadata:
  {
    "openclaw":
      {
        "emoji": "📅",
        "requires": { "bins": ["uv"], "env": ["DAV_AUTH", "DAV_URL"] },
        "primaryEnv": "DAV_AUTH",
      },
  }
---

# Calendar

Interact with the user's calendar using the CalDAV specification. All calendar operations are performed using the bundled `cal.py` script.

Calendar configuration is stored externally and loaded at runtime. No user information is required when running the script.

## Examples

Get calendar events in a time range

```bash
uv run {baseDir}/scripts/cal.py get_events --start 2025-01-01 --end 2025-12-31
```

Get details of a single event

```bash
uv run {baseDir}/scripts/cal.py get_event 019e5ba4-8387-7041-bcd0-dea0d6fce429
```

Create an event (without timezone information, defaults to user's local timezone)

```bash
uv run {baseDir}/scripts/cal.py create_event "Team Meeting" --start 2025-06-15T09:00:00 --end 2025-06-15T10:00:00 --location "Conference Room"
```

Create an event in a specific timezone

```bash
uv run {baseDir}/scripts/cal.py create_event "Team Meeting" --start 2025-06-15T09:00:00-05:00 --end 2025-06-15T10:00:00-05:00 --timezone America/Chicago
```

Create an all-day event

```bash
uv run {baseDir}/scripts/cal.py create_event "Independence Day" --start 2025-07-04 --end 2025-07-04
```
