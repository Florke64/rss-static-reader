# config.py

# RSS-Static-Reader, parses RSS feeds into organized HTML documents, linking to the articles
#     Copyright (C) 2021  Daniel Wasiak
#     You should have received a copy of the GNU General Public License.
#     See `LICENSE.txt` for more details.

RSS_FEED_FILE: str = "rss-feed-list.conf"
TARGET_HTML_DIR: str = "html"

RSS_SOURCE_LINE = "<a href=\"rss-source/%rss_source_html_title%.html\">%rss_source_title%</a> (%articles_count%)</span>"

if __name__ == "__main__":
    print("Error: This is configuration file for RSS Static Reader and not a standalone program")
    exit(1)
