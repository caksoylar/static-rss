import sys
import time
from datetime import datetime, timezone

import feedparser
from mako.template import Template


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
            entries.append(entry)

    entries.sort(key=lambda x: x.published_datetime, reverse=True)
    with open(sys.argv[2], "w") as fo:
        fo.write(template.render(all_entries=entries))


if __name__ == "__main__":
    main()
