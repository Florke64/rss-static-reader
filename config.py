# config.py

# RSS-Static-Reader, parses RSS feeds into organized HTML documents, linking to the articles
#     Copyright (C) 2021  Daniel Wasiak
#     You should have received a copy of the GNU General Public License.
#     See `LICENSE.txt` for more details.

# Main configuration:

RELOAD_TIME: float = 15  # in minutes
RSS_FEED_FILE: str = "rss-feed-list.conf"
TARGET_HTML_DIR: str = "html"
RANDOM_ARTICLE_LINK: bool = True

# Advanced config:
WIDGET_LIST: tuple = (
    'article_link_block',
    'source_link_block',
    'category_link_block',
    'back_link_block',
    'page_title',
    'footer_generate_time',
    'random_article'
)

ACCEPTED_DATETIME_FORMAT: tuple = (
    '%a, %d %b %Y %H:%M:%S %z',     # Common date-time string format for most feeds
    '%Y-%m-%dT%H:%M:%SZ',           # Added as a fix of #3 issue (feedburner.com)
)

if __name__ == "__main__":
    print("Error: This is configuration file for RSS Static Reader and not a standalone program")
    exit(1)
