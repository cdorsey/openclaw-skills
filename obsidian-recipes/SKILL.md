---
name: obsidian-recipes
description: Instructions for adding a recipe to the user's Obsidian vault
metadata:
  { "openclaw": { "emoji": "🥕", "requires": { "bins": ["obsidian-cli"] } } }
---

# Recipe to Obsidian

Steps and best practices for adding a recipe to the Obsidian Vault

## Steps

1. Establish the location of the Obsidian vault. If the location is not in your memory, prompt the user and store it in memory before continuing
2. If the input is a URL, attempt to crawl the URL and extract the recipe. If the URL is from Notion (e.g. `*.notion.site` or `notion.so`), use the Notion API
   first — Notion pages render client-side and cannot be scraped with `web_fetch`. If this is not possible using your available tools, stop and report the failure to the user
3. Find the `Recipe` template in the Obsidian vault. Be sure to follow this template exactly when saving the recipe
4. Attempt to find a suitable banner image from the crawled URL. If successful, download the image to the `_assets` folder in the Obsidian vault, and reference it
   using the local file path. Avoid directly using remote URLs in the new note. If there is no URL or no suitable image can be found, omit it from the note
5. Using this information, construct the note and save it to the vault's Recipes folder. The folder name may not match exactly, but it will be at the root level
   of the vault. The file name should be the name of the dish.

## Frontmatter Notes

- The `tags` field must be a YAML list (not comma-separated). Each tag should include the `#` prefix and contain no whitespace. Example:
  ```yaml
  tags:
    - "#slow-cooker"
    - "#dinner"
  ```
