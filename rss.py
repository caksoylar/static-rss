import sys

import feedparser
from mako.template import Template


def main():
    template = Template(filename="rss.html")

    with open(sys.argv[1]) as f:
        feeds = f.read().splitlines()
    print(feeds)
    for feed in feeds:
        d = feedparser.parse(feed)
        print(d["feed"]["title"])

    with open(sys.argv[2], "w") as fo:
        fo.write(template.render(feed=feedparser.parse(feeds[1])))



if __name__ == "__main__":
    main()
