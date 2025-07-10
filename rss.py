"""Simple RSS "reader" that fetches entries from a list of feeds, then renders an html."""

import json
import re
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime, timezone
from html import escape
from textwrap import shorten
from urllib.parse import urlparse

import feedparser
from mako.template import Template


def slugify(text):
    """Simple converter from arbitrary string to e.g. a valid html id value."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9_\-:.]", "-", text)
    if not re.match(r"^[a-z]", text):
        text = "id-" + text
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return escape(text, quote=True)


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


def get_feed_icon(d, url):
    """Try to find an icon for a given feed, might be extended later."""
    if feed_image := d["feed"].get("image", {}).get("href"):
        return feed_image

    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}/favicon.ico"


def main():
    """Read template, feed list, render to last arg as html."""
    ap = ArgumentParser("rss")
    ap.add_argument("-f", "--feed-list", type=str)
    ap.add_argument("-t", "--template", type=str, default="rss.html")
    ap.add_argument("-d", "--dump-feeds", type=str)
    ap.add_argument("-i", "--import-feeds", type=str)
    ap.add_argument("-o", "--output-html", type=str)
    args = ap.parse_args()

    assert args.feed_list or args.import_feeds
    if args.output_html:
        assert args.template

    if args.feed_list:
        with open(args.feed_list, encoding="utf-8") as f:
            feed_urls = f.read().splitlines()

        feeds = []
        for feed_url in feed_urls:
            d = feedparser.parse(feed_url)
            print(f"{feed_url}: {len(d['entries'])}")
            feeds.append((feed_url, d))
    else:
        with open(args.import_feeds, "r", encoding="utf-8") as f:
            feeds = json.load(f)

    if args.dump_feeds:
        with open(args.dump_feeds, "w", encoding="utf-8") as fo:
            json.dump(feeds, fo)

    entries = []
    feed_list = []
    for feed_url, feed in feeds:
        title = shorten(feed["feed"]["title"], width=40, placeholder="…")
        slug = slugify(title)
        icon = get_feed_icon(feed, feed_url)
        feed_list.append((slug, title, len(feed["entries"])))
        for entry in feed["entries"]:
            entry["published_datetime"] = datetime(
                *entry["published_parsed"][:6], tzinfo=timezone.utc
            )
            entry["source_title"] = title
            entry["source_title_slug"] = slug
            entry["image_url"] = extract_image(entry)
            entry["source_icon_url"] = icon
            entries.append(entry)
    entries.sort(key=lambda x: x["published_datetime"], reverse=True)

    print("\nTop 100 stats:")
    for feed, count in Counter(
        (post["source_title"] for post in entries[:100])
    ).most_common():
        print(f"{count:2d} <- {feed}")

    if args.output_html:
        template = Template(filename=args.template)
        with open(args.output_html, "w", encoding="utf-8") as fo:
            fo.write(template.render(all_entries=entries, feed_list=feed_list))


if __name__ == "__main__":
    main()
