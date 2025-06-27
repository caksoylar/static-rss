import re
import sys
import time
from datetime import datetime, timezone

import feedparser
from mako.template import Template


def extract_image(entry):
    # 1. Check media content
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url')

    # 2. Check enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image/'):
                return enclosure.get('href')

    # 3. Fallback: look for <img> in summary
    if hasattr(entry, 'summary'):
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)

    return None


def main():
    template = Template(filename="rss.html")

    with open(sys.argv[1]) as f:
        feeds = f.read().splitlines()

    entries = []
    for feed in feeds:
        d = feedparser.parse(feed)
        title = d["feed"]["title"]
        for entry in d["entries"]:
            entry.published_datetime = datetime.fromtimestamp(time.mktime(entry["published_parsed"]), tz=timezone.utc)
            entry.source_title = title
            entry.image_url = extract_image(entry)
            entries.append(entry)

    entries.sort(key=lambda x: x.published_datetime, reverse=True)
    with open(sys.argv[2], "w") as fo:
        fo.write(template.render(all_entries=entries))


if __name__ == "__main__":
    main()
