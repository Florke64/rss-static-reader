#!/bin/env python3
# rss_static_reader.py

# RSS-Static-Reader, parses RSS feeds into organized HTML documents, linking to the articles
#     Copyright (C) 2021  Daniel Wasiak
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Built-in Python Libraries
import os
import os.path as path
import base64 as base
import time
import datetime
import threading
from typing import Union

# 3rd party Python libraries
import feedparser

# Program configuration file
import config


# # #  UTILS  # # #

def list_element_or_default(list_array: list, element_number: int, default_value: any = None) -> any:
    array_len: int = len(list_array)
    if array_len > element_number and list_array[element_number] is not None and list_array[element_number] != "":
        return list_array[element_number]
    else:
        return default_value


def get_uri_friendly_str(text: str, encoding: str = 'utf-8') -> str:
    return base.b64encode(bytes(text, encoding)).decode(encoding)


# # #  PARSING RSS FEED  # # #

class FeedSource:
    def __init__(self, feed_url: str, feed_title: str, feed_categories: list[Union[str]] = None) -> None:
        self.feed_url: str = feed_url
        self.feed_title: str = feed_title
        self.feed_categories: list[Union[str]] = feed_categories
        self.id: str = "src_" + get_uri_friendly_str(feed_url)

        self.article_count: int = 0


def feed_source_factory(feed_source_plain_data: list[Union[str]]) -> FeedSource:
    def split_categories(feed_categories_list: str) -> Union[list[Union[str]], None]:
        if feed_categories_list is None or feed_categories_list == "":
            return ["Uncategorized"]

        return feed_categories_list.split(',')

    # Parsing feed URL
    feed_url: str = list_element_or_default(feed_source_plain_data, 0, None)
    # Parsing feed title
    feed_title: str = list_element_or_default(feed_source_plain_data, 1, "Untitled RSS Feed")
    # Parsing feed categories
    feed_categories: str = list_element_or_default(feed_source_plain_data, 2, "")
    feed_categories: list[Union[str]] = split_categories(feed_categories)

    # TODO: Links will use raw_feed_categories elements in the future
    # raw_feed_categories: list[Union[str]] = []
    #
    # for category in feed_categories:  # type: str
    #     raw_feed_categories.append(get_uri_friendly_str(category))

    # Crating final FeedSource object
    return FeedSource(feed_url, feed_title, feed_categories)


class FeedArticle:
    def __init__(self, article_title: str, article_url: str, published_on: str, article_author: str,
                 feed_source: FeedSource = None) -> None:
        self.article_title: str = article_title
        self.article_url: str = article_url

        datetime_format = "%a, %d %b %Y %H:%M:%S %z"
        self.published_date_time: datetime = datetime.datetime.strptime(published_on, datetime_format)
        # self.published_date_time: str = published_on
        self.article_author: str = article_author

        self.feed_source: Union[FeedSource, None] = feed_source

        # Optional Values
        self.comments_url: Union[str, None] = None


def article_list_factory(feedparser_entries: dict, feed_source: FeedSource) -> list[Union[FeedArticle]]:
    articles: list[Union[FeedArticle]] = []

    for n in range(len(feedparser_entries)):
        title = feedparser_entries[n]['title']
        author = feedparser_entries[n]['author']
        published_date = feedparser_entries[n]['published']
        article_url = feedparser_entries[n]['link']
        # comments_url = feedparser_entries[n]['comments']  #  not implemented yet

        articles.append(FeedArticle(title, article_url, published_date, author, feed_source))

    return articles


# FEED_SOURCES: list[Union[FeedSource]] = []
FEED_SOURCES: dict[str, FeedSource] = {}
FEED_ARTICLES: list[Union[FeedArticle]] = []


class FeedParser(threading.Thread):
    def __init__(self, feed_source_id: str) -> None:
        threading.Thread.__init__(self)

        self.feed_source_id: str = feed_source_id
        self.feed_source: FeedSource = FEED_SOURCES.get(feed_source_id)

        self.fetched_articles: list[Union[FeedArticle]] = []
        self.articles_num: int = 0
        self.feed_data: Union[list, None] = None

        self.start_time: Union[float, None] = None
        self.end_time: Union[float, None] = None
        self.elapsed_time: Union[float, None] = None

    def run(self) -> None:
        # Staring time counter to track time spent on receiving the data
        self.start_time = time.time()

        # Using `feedparser` library to gather RSS feed data from URL
        self.feed_data = feedparser.parse(self.feed_source.feed_url)

        # Calculating time elapsed on the feedparser call
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

        self.fetched_articles: list[Union[FeedArticle]] = article_list_factory(
            self.feed_data.get('entries'),
            self.feed_source
        )

        self.articles_num = len(self.fetched_articles)

        print(f"{self.feed_source.feed_title} ({self.articles_num} articles) -- Parser finished in {self.elapsed_time}")


def read_feed_sources(file_feed_list: str) -> dict[str, FeedSource]:
    config_file_path: str = path.join(file_feed_list)
    if not path.isfile(config_file_path):
        return {}

    _feed_sources: dict[str, FeedSource] = {}

    with open(config_file_path, 'rt') as config_file:

        for line in config_file:  # type: str
            # Skipping empty lines and comments
            stripped_line: str = line.strip()
            if stripped_line == '' or stripped_line.startswith('#'):
                continue

            feed_source_data: list[Union[str]] = line.replace('\n', '').split(';', 2)
            feed_source: FeedSource = feed_source_factory(feed_source_data)
            _feed_sources.update({feed_source.id: feed_source})

        config_file.close()

    return _feed_sources


# # #  GENERATING HTML FILES  # # #

def get_article_dedicated_link_block(article: FeedArticle) -> str:
    template: str = '\n\t\t<div class="article">\
\n\t\t\t<b><a href="%art_link%" target="_blank">%art_title%</a></b> -- %src_title%<br/>\
\n\t\t\t<small>Author: %art_author%, Published on: %pub_date%</small><br/>\
\n\t\t</div>'

    template = template.replace('%art_link%', article.article_url)
    template = template.replace('%art_title%', article.article_title)
    template = template.replace('%src_title%', article.feed_source.feed_title)
    template = template.replace('%art_author%', article.article_author)
    template = template.replace('%pub_date%', article.published_date_time.strftime("%A, %d %b %Y %H:%M"))

    return template


def get_source_dedicated_link_block(feed_source_id: str) -> str:
    feed_source: FeedSource = FEED_SOURCES.get(feed_source_id)

    template: str = '\n\t\t<a href="%source_id%.html">%rss_source_title%</a> (%articles_count%)</span>'
    template = template.replace('%rss_source_title%', feed_source.feed_title)
    template = template.replace('%articles_count%', str(feed_source.article_count))
    template = template.replace('%source_id%', feed_source_id)

    return template


def generate_html_files(target_directory_path: str = "html_target") -> None:
    target_directory: str = path.join(target_directory_path)
    if not path.isdir(target_directory):
        os.mkdir(target_directory)

    # TODO: Add more templates
    index_html_template_content: str = ""
    index_html_template: str = path.join("html_template/index.html")
    with open(index_html_template, 'rt') as html_file:
        for line in html_file:  # type: str
            index_html_template_content += line

        html_file.close()

    index_html: str = path.join(target_directory, "index.html")
    with open(index_html, 'wt') as html_file:
        sources_dedicated_links_dom: str = ''
        article_dedicated_links_dom: str = ''

        for source_id in FEED_SOURCES.keys():  # type: FeedSource
            sources_dedicated_links_dom += get_source_dedicated_link_block(source_id)

        for article in FEED_ARTICLES:  # type: FeedArticle
            article_dedicated_links_dom += get_article_dedicated_link_block(article)

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_SOURCES_DEDICATED_LINKS__-->',
            sources_dedicated_links_dom
        )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_ARTICLE_DEDICATED_LINKS__-->',
            article_dedicated_links_dom
        )

        html_file.write(index_html_template_content)

        html_file.close()

    # _feed_sources: list[Union[FeedSource]] = []
    #
    # with open(target_directory, 'rt') as config_file:
    #
    #     for line in config_file:  # type: str
    #         # Skipping empty lines and comments
    #         stripped_line: str = line.strip()
    #         if stripped_line == '' or stripped_line.startswith('#'):
    #             continue
    #
    #         feed_source_data: list[Union[str]] = line.replace('\n', '').split(';', 2)
    #         feed_source: FeedSource = feed_source_factory(feed_source_data)
    #         _feed_sources.append(feed_source)
    #
    #     config_file.close()


def main() -> None:
    # Firstly, get list of RSS sources to grab articles from...
    global FEED_SOURCES
    FEED_SOURCES = read_feed_sources(config.RSS_FEED_FILE)

    # Run RSS Parsers in threads -- track threads until they finish job
    running_feed_parsers: list[Union[FeedParser]] = []
    for feed_source_id in FEED_SOURCES.keys():  # type: str
        feed_parser: FeedParser = FeedParser(feed_source_id)
        running_feed_parsers.append(feed_parser)
        feed_parser.start()

    global FEED_ARTICLES
    for feed_parser in running_feed_parsers:  # type: FeedParser
        feed_parser.join()

        # Appending all grabbed articles to the main list
        for article in feed_parser.fetched_articles:  # type: FeedArticle
            FEED_ARTICLES.append(article)
            FEED_SOURCES.get(article.feed_source.id).article_count += 1

        # Sorting articles by the date they were posted
        FEED_ARTICLES.sort(key=lambda art: art.published_date_time, reverse=True)

    generate_html_files(config.TARGET_HTML_DIR)

    # for article in FEED_ARTICLES:  # type: FeedArticle
    #     print(article.article_title, article.published_date_time)


def gplv2_notice():
    print("RSS Static Reader, Copyright (C) 2021 Daniel Wasiak \n\
RSS Static Reader comes with ABSOLUTELY NO WARRANTY; for details see `LICENSE.txt` file. \n\
This is free software, and you are welcome to redistribute it \n\
under certain conditions; see `LICENSE.txt` file for details.\n")


if __name__ == "__main__":
    gplv2_notice()
    main()
