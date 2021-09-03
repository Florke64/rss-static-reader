# RSS Static Reader

Parse RSS feed into organized HTML documents, linking to articles.

![Github thumbnail image](github/thumbnail.png 'Parse RSS feed into organized HTML documents, linking to articles.')

## Brief description

RSS-Static-Reader is a [Python](https://python.org) script, made as a hobby project for my personal use and shared on [GitHub](https://github.com/flrque/rss-static-reader) under the GPLv2 [license](LICENSE). This program is intended to be self-hosted on a (potencially) low-end server hardware. It will periodically generate HTML documents from given RSS feed links. After documents are created, you can use anything from [Apache HTTP server](https://httpd.apache.org) to [darkhttpd](https://unix4lyfe.org/darkhttpd) to access them. You can even use [rsync](https://rsync.samba.org) or [Syncthing](https://syncthing.net/) to sync these HTML files over all of your devices to access them anywhere or use some service like [zerotier-one](https://zerotier.com/) if your server is hidden behind NAT.
Possibilities are infinite due to the simplistic nature of this program.

## Basic requirements

As it is simply a Python script, you should be abe to run it under any choosen Operating System without any troubble or additional configuration done.

You need Python - at least `python3.9` is required, mainly due to the declaration of functions' arguments I've done.

You can check your current version of Python installed on a system via `python --version` command.
If your Python is, let's say, version `3.7` it won't be compatible. However, please bear in mind, that you can have multiple installations of Python at once. In this case, you should run this script not with `python rss_static_reader.py` command but with for example `python3.9 rss_static_reader.py`.

One required thing is to install `feedparser` module for python. It is actively supported Python module and you can insatll it easily via `pip install feedparser`. It is dependency of the rss-static-reader and core library it uses.

## Screenshot

![Screenshot](github/screenshot-target-00.jpg 'Screenshot of the default theme.')

## Configuration

### config.py

Contains program configuration. You can limit the amount of articles shown on a single page or the target directory for prepared HTML files. Everything you can do with this config file is defined by variables and all available variables are already included (or described within a comments) in the said file.

### rss-feed-list.conf

Is the list of RSS feeds. It contains links to RSS feeds, their names and categories. Each line should look as follows:

`HTTP Link`;`RSS Feed Title`;`Category`
(multiple categories must be seperated by `,`)

#### Example:

```plain-text
https://archlinux.org/feeds/news/;Arch Linux News;Linux
https://omgubuntu.co.uk/feed;OMG, Ubuntu!;Linux,Technology
https://itsfoss.com/feed;It's FOSS;Technology
```

## Planned features

Below is the list of features I want to implement into this program. When I complete them all, I'll consider this project done and only keep on maintaining it if I find any bug or want to tweak something small.

- **HTML themes**:
Output look can be customized to look a bit nicer than now.

- **Random article**:
Link to randomly choosen "article of the day" or something like that.

- **Feed limit**:
Number of the articles shown under the single page would be possible limit.

- **Scheduled updates**:
(Partially implemented)
~~Probably most important, almost core function of this project. Program will periodically refresh generated HTML files so everytime you open them there will new set of news appear.~~

- **Code cleanup**: Technical thing I'll work on. Currently code is a total mess and I want to improve it as I learn Python. It also means that I'll work on Exception handling.

## License

Copyright (C) 2021  Daniel Wasiak

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

>Read full license in [LICENSE](LICENSE) file.
