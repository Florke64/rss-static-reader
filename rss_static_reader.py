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
import random
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

class FeedCategory:
    def __init__(self, category_name: str) -> None:
        self.name: str = category_name
        self.id: str = "cat_" + get_uri_friendly_str(category_name)
        self.article_count: int = 0

    def add_article(self) -> None:
        self.article_count += 1


class FeedSource:
    def __init__(self, feed_url: str, feed_title: str, categories: list[Union[str]] = None) -> None:
        self.feed_url: str = feed_url
        self.name: str = feed_title
        self.categories: list[Union[str]] = categories
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
    category_names: str = list_element_or_default(feed_source_plain_data, 2, "")
    category_names: list[Union[str]] = split_categories(category_names)

    # Crating final FeedSource object
    return FeedSource(feed_url, feed_title, category_names)


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

    def register(self):
        FEED_ARTICLES.append(self)
        FEED_SOURCES.get(self.feed_source.id).article_count += 1

        for category_name in self.feed_source.categories:  # type: str
            category_id: str = "cat_" + get_uri_friendly_str(category_name)
            if FEED_CATEGORIES.get(category_id) is None:
                category: FeedCategory = FeedCategory(category_name)
                FEED_CATEGORIES.update({category.id: category})

            FEED_CATEGORIES.get(category_id).add_article()


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


FEED_SOURCES: dict[str, FeedSource]
FEED_ARTICLES: list[Union[FeedArticle]]
RANDOM_ARTICLE_LINK: str = "#"
FEED_CATEGORIES: dict[str, FeedCategory]
WIDGET_TEMPLATES: dict[str, str]


def clear_cache() -> None:
    global FEED_SOURCES
    global FEED_ARTICLES
    global FEED_CATEGORIES
    global WIDGET_TEMPLATES

    FEED_SOURCES = {}
    FEED_ARTICLES = []
    FEED_CATEGORIES = {}
    WIDGET_TEMPLATES = {}


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

        print(f"{self.feed_source.name} ({self.articles_num} articles) -- Parser finished in {self.elapsed_time}")


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


def load_widgets(widget_list: tuple[Union[str]]) -> None:
    widgets_directory: str = path.join("html_template", "widgets")
    if not path.isdir(widgets_directory):
        print('Error no widgets directory!')
        return

    global WIDGET_TEMPLATES
    for widget in widget_list:  # type: str
        widget_template_content: str = ''
        with open(path.join(widgets_directory, f"{widget}.htm"), 'rt') as widget_file:
            for text_line in widget_file:  # type: str
                widget_template_content += text_line

            widget_file.close()

        WIDGET_TEMPLATES.update({widget: widget_template_content})


# # #  GENERATING HTML FILES  # # #

def wipe_target() -> None:
    target_directory: str = path.join(config.TARGET_HTML_DIR)
    if not path.isdir(target_directory):
        os.mkdir(target_directory)
        return

    for file in os.listdir(target_directory):  # type: str
        os.remove(path.join(target_directory, file))


def use_widget(widget_id: str, widget_data: dict[str, str]) -> str:
    widget_template: str = WIDGET_TEMPLATES.get(widget_id)

    if widget_template is None:
        raise IndexError(f'Widget {widget_id} doesn\'t exist or HTML theme is not complete.')

    for key in widget_data.keys():  # type: str
        widget_template = widget_template.replace(f'%{key}%', widget_data.get(key))

    return widget_template


def generate_html_files(target_directory_path: str = "html_target", subfeed_id: str = "index") -> None:
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

    page_type = FEED_SOURCES.get(subfeed_id) or FEED_CATEGORIES.get(subfeed_id)
    page_title = 'All Articles' if subfeed_id == 'index' else page_type.name
    page_title_dom = use_widget('page_title', {'page_title': page_title})

    index_html: str = path.join(target_directory, f"{subfeed_id}.html")
    with open(index_html, 'wt') as html_file:
        sources_dedicated_links_dom: str = ''
        article_dedicated_links_dom: str = ''
        category_dedicated_links_dom: str = ''

        for source in FEED_SOURCES.values():  # type: FeedSource
            sources_dedicated_links_dom += use_widget('source_link_block', {
                'source_id': source.id,
                'rss_source_title': source.name,
                'articles_count': str(source.article_count)
            })

        for category in FEED_CATEGORIES.values():  # type: FeedCategory
            category_dedicated_links_dom += use_widget('category_link_block', {
                'category_id': category.id,
                'category_name': category.name,
                'category_article_amount': str(category.article_count)
            })

        global RANDOM_ARTICLE_LINK
        article_count: int = len(FEED_ARTICLES)
        random_article_index: int = random.randint(0, article_count)

        i: int = 0
        for article in FEED_ARTICLES:  # type: FeedArticle
            if subfeed_id == "index" or \
                (type(page_type) is FeedSource and article.feed_source.id == FEED_SOURCES.get(subfeed_id).id) or \
                    (type(page_type) is FeedCategory and FEED_CATEGORIES.get(subfeed_id).name in article.feed_source.categories):
                article_dedicated_links_dom += use_widget('article_link_block', {
                    'art_link': article.article_url,
                    'art_title': article.article_title,
                    'src_title': article.feed_source.name,
                    'art_author': article.article_author,
                    'pub_date': article.published_date_time.strftime("%A, %d %b %Y %H:%M"),
                    # TODO: Move DATE_FORMAT to config.py
                })

            if i == random_article_index and subfeed_id == "index":
                RANDOM_ARTICLE_LINK = article.article_url

            i += 1

        if config.RANDOM_ARTICLE_LINK and subfeed_id == "index":
            index_html_template_content = index_html_template_content.replace(
                '<!--__RSS_RANDOM_ARTICLE_LINK__-->',
                use_widget('random_article', {'art_link': RANDOM_ARTICLE_LINK})
            )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_SOURCES_DEDICATED_LINKS__-->',
            sources_dedicated_links_dom
        )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_CATEGORY_DEDICATED_LINKS__-->',
            category_dedicated_links_dom
        )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_ARTICLE_DEDICATED_LINKS__-->',
            article_dedicated_links_dom
        )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_BACK_HOME_LINK__-->',
            WIDGET_TEMPLATES.get('back_link_block')
        ) if subfeed_id != "index" else index_html_template_content

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_PAGE_TITLE__-->',
            page_title_dom
        )

        index_html_template_content = index_html_template_content.replace(
            '<!--__RSS_FEED_FOOTER_GEN_TIME__-->',
            use_widget('footer_generate_time', {'time': datetime.datetime.now().strftime("%A, %d %b %Y %H:%M")})
        )

        html_file.write(index_html_template_content)

        html_file.close()


def process() -> None:
    load_widgets(config.WIDGET_LIST)

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
            article.register()

    # Sorting articles by the date they were posted
    FEED_ARTICLES.sort(key=lambda art: art.published_date_time, reverse=True)

    generate_html_files(config.TARGET_HTML_DIR)

    for category_id in FEED_CATEGORIES.keys():  # type: str
        generate_html_files(config.TARGET_HTML_DIR, category_id)

    for source_id in FEED_SOURCES.keys():  # type: str
        generate_html_files(config.TARGET_HTML_DIR, source_id)


class MainLoop(threading.Thread):
    def __init__(self) -> None:
        threading.Thread.__init__(self)

        self.__running: bool = False

    def run(self) -> None:
        # Converting minutes from config to seconds
        reload_time_sec: float = config.RELOAD_TIME * 60 if config.RELOAD_TIME > 0 else -1

        self.set_running(True)

        start_time: float = time.time()
        while self.__running:
            clear_cache()
            wipe_target()
            process()

            finish_time: float = time.time()

            total_job_time: float = finish_time - start_time
            print(f"Job finished in {total_job_time} seconds.")

            if reload_time_sec != -1:
                print(f"INFO: Waiting {config.RELOAD_TIME} minute(s) for next run...\n")
                time.sleep(reload_time_sec)
            else:
                break

    def set_running(self, running: bool):
        self.__running = running


def main() -> None:
    main_loop: threading.Thread = MainLoop()
    main_loop.start()

    # TODO: Command-line tool (stop / edit config / force regen / etc.)


def gplv2_notice():
    print("RSS Static Reader, Copyright (C) 2021 Daniel Wasiak \n\
RSS Static Reader comes with ABSOLUTELY NO WARRANTY; for details see `LICENSE.txt` file. \n\
This is free software, and you are welcome to redistribute it \n\
under certain conditions; see `LICENSE.txt` file for details.\n")


if __name__ == "__main__":
    gplv2_notice()
    main()
