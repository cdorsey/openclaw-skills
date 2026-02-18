---
name: calendar
description: Interact with the user's calendar
metadata:
  {
    "openclaw":
      {
        "emoji": "📅",
        "requires": { "bins": ["uv", "curl"], "env": ["DAV_AUTH", "DAV_URL"] },
        "primaryEnv": "DAV_AUTH",
      },
  }
---

# Calendar

Use the CalDAV specification to interact with the user's calendar upon request. Commands should be executed using `curl`. If a new file name is needed (i.e. creating a new event), use the bundled script.

Before executing any actions, get the user's DAV username and preferred calendar. If this is not in your memory, prompt the user and store them for later use.

## Security

Avoid printing the auth token or URL directly, always use `$DAV_AUTH` and `$DAV_URL`, respectively.

## Examples

_Note: Examples use the `default` calendar of user `johndoe`_

Get calendar events in a time range

```bash
curl -X REPORT -H "Depth: 1" -H "Prefer: return-minimal" -H "Authorization: Basic $DAV_AUTH" -d '
<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
    <d:prop>
        <d:getetag />
        <c:calendar-data />
    </d:prop>
    <c:filter>
        <c:comp-filter name="VCALENDAR">
            <c:comp-filter name="VEVENT">
                <c:time-range start="20250101T000000Z" end="20251231T235959Z" />
            </c:comp-filter>
        </c:comp-filter>
    </c:filter>
</c:calendar-query>
' $DAV_URL/calendars/johndoe/default
```

Get details of a single event

```bash
curl -H "Depth: 1" -H "Prefer: return-minimal" -H "Authorization: Basic $DAV_AUTH" $DAV_URL/calendars/johndoe/default/633bff89b1de69fe40cda18126274fec.ics
```

Create an event

```bash
uv run {baseDir}/scripts/generate_filename.py
# 633bff89b1de69fe40cda18126274fec.ics

curl -X PUT -H "Content-Type: text/calendar; charset=utf-8" -H "Authorization: Basic $DAV_AUTH" -d '
BEGIN:VCALENDAR
....
END:VCALENDAR
' $DAV_URL/calendars/johndoe/default/633bff89b1de69fe40cda18126274fec.ics
```

Update an event

```bash
curl -X PUT -H "Content-Type: text/calendar; charset=utf-8" -H "If-Match: 21345-324" -H "Authorization: Basic $DAV_AUTH" -d '
BEGIN:VCALENDAR
....
END:VCALENDAR
' $DAV_URL/calendars/johndoe/default/633bff89b1de69fe40cda18126274fec.ics
```

Delete event `633bff89b1de69fe40cda18126274fec.ics` with ETag `21345-324`

```bash
curl -X DELETE -H "If-Match: 21345-324" -H "Authorization: $DAV_AUTH" $DAV_URL/calendars/johndoe/633bff89b1de69fe40cda18126274fec.ics
```
