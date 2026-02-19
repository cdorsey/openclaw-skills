---
name: jellyfin-requests
description: Submit requsts to a Jellyfin server on behalf of the user
metadata:
  {
    "openclaw":
      {
        "emoji": "🪼",
        "requires": { "bins": ["uv"], "env": ["SEERR_API_KEY", "SEERR_URL"] },
        "primaryEnv": "SEERR_API_KEY",
        "install":
          [
            {
              "id": "uv-brew",
              "kind": "brew",
              "formula": "uv",
              "bins": ["uv"],
              "label": "Install uv (brew)",
            },
          ],
      },
  }
---

# Jellyfin requests

Use the bundled script to submit requests to a Jellyfin server via the Seerr API

Search for media based on a text query (use to retrieve a numeric ID)

```bash
uv run {baseDir}/scripts/request.py search "Ex Machina"
```

Submit a request for a movie

```bash
uv run {baseDir}/scripts/request.py add_movie 12345
```

Submit a request for all seasons of a TV show

```bash
uv run {baseDir}/scripts/request.py add_tv 12345
```

Submit a request for selected seasons of a TV show

```bash
uv run {baseDir}/scripts/request.py add_tv 12345 --seasons 1 2 3
```

Check whether media is currently available on the Jellyfin server

```bash
uv run {baseDir}/scripts/request.py get_available --media-type tv 12345
```

## Media availability

The `get_available` command should only be used when the user explitly requests the status or to
contextualize vague requests (e.g. "Download the next season of The Office"). Requests for existing
media will be ignored, so pre-checking is unnecessary.
