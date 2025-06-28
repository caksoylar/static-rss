"""Simple RSS "reader" that fetches entries from a list of feeds, then renders an html."""

import re
import sys
from datetime import datetime, timezone
from textwrap import shorten

import feedparser
from mako.template import Template


def extract_image(entry):
    """Uses heuristics to find an image for a given entry."""

    # 1. Check media content
    if content := entry.get("media_content"):
        return content[0].get("url")

    # 2. Check enclosures
    if enclosures := entry.get("enclosures"):
        for enclosure in enclosures:
            if enclosure.get("type", "").startswith("image/"):
                return enclosure.get("href")

    # 3. Fallback: look for <img> in summary
    if summary := entry.get("summary"):
        if m := re.search(r'<img[^>]+src="([^">]+)"', summary):
            return m.group(1)

    return None


def get_feed_icon(d):
    """Try to find an icon for a given feed, might be extended later."""
    return d["feed"].get("image", {}).get("href")


def main():
    """Read template, feed list, render to last arg as html."""
    template = Template(filename="rss.html")

    with open(sys.argv[1], encoding="utf-8") as f:
        feeds = f.read().splitlines()

    entries = []
    for feed in feeds:
        d = feedparser.parse(feed)
        print(f"{feed}: {len(d['entries'])}")
        title = shorten(d["feed"]["title"], width=40, placeholder="…")
        icon = get_feed_icon(d)
        for entry in d["entries"]:
            entry.published_datetime = datetime(
                *entry["published_parsed"][:6], tzinfo=timezone.utc
            )
            entry.source_title = title
            entry.image_url = extract_image(entry)
            entry.source_icon_url = icon
            entries.append(entry)

    entries.sort(key=lambda x: x.published_datetime, reverse=True)
    with open(sys.argv[2], "w", encoding="utf-8") as fo:
        fo.write(template.render(all_entries=entries))


if __name__ == "__main__":
    main()
