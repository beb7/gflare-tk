"""
@author Benjamin Görler <ben@greenflare.io>

@section LICENSE

Greenflare SEO Web Crawler (https://greenflare.io)
Copyright (C) 2020  Benjamin Görler. This file is part of
Greenflare, an open-source project dedicated to delivering
high quality SEO insights and analysis solutions to the world.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
from os import path
from pathlib import Path


class Defaults:

    version = '0.98'

    crawl_items = [
        'url',
        'crawl_status',
        'status_code',
        'content_type',
        'page_title',
        'meta_description',
        'h1',
        'unique_inlinks',
        'respect_nofollow',
        'canonicals',
        'canonical_tag',
        'pagination',
        'hreflang',
        'canonical_http_header',
        'robots_txt',
        'redirect_url',
        'meta_robots',
        'x_robots_tag',
        'respect_robots_txt',
        'report_on_status',
        'follow_blocked_redirects'
    ]

    headers = {
        'Accept-Language': 'en-gb',
        'Accept-Encoding': 'gzip',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    user_agents = {
        'Greenflare': 'Greenflare SEO Crawler/1.0',
        'Windows Chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Macintosh Chrome': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Googlebot Desktop': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Googlebot Mobile': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Bingbot Desktop': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
        'Bingbot Mobile': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Mobile Safari/537.36 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'
    }

    settings = {
        'MODE': 'Spider',
        'THREADS': 5,
        'URLS_PER_SECOND': 0,
        'USER_AGENT': user_agents['Greenflare'],
        'UA_SHORT': 'Greenflare',
        'MAX_RETRIES': 3,
        'CRAWL_ITEMS': crawl_items,
        'EXTRACTION_SEPARATOR': ' | '
    }

    display_columns = [
        'url',
        'crawl_status',
        'status_code',
        'content_type',
        'h1',
        'page_title',
        'canonical_tag',
        'robots_txt',
        'redirect_url'
    ]

    popup_menu_labels = [
        'Sort A-Z',
        'Sort Z-A',
        'Sort Smallest To Largest',
        'Sort Largest To Smallest',
        '_',
        'Equals',
        'Does Not Equal',
        '_',
        'Begins With',
        'Ends With',
        '_',
        'Contains',
        'Does Not Contain',
        '_',
        'Greater Than',
        'Greater Than Or Equal To',
        'Less Than',
        'Less Than Or Equal To']

    window_title = 'Greenflare SEO Crawler'

    file_extension = '.gflaredb'

    linux_theme = 'breeze'

    download_url = 'https://greenflare.io/download/'
    latest_release_url = 'https://greenflare.io/download/LATEST'

    @classmethod
    def set_working_dir(cls, directory):
        cls.working_dir = directory

    @classmethod
    def root_icon(cls):
        pkg_path = cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-32x32.png'
        if path.isfile(pkg_path):
            return pkg_path
        return cls.working_dir + path.sep + 'greenflare/resources' + path.sep + 'greenflare-icon-32x32.png'

    @classmethod
    def about_icon(cls):
        # Check if we are run as part of an macOS APP bundle
        if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
            return str(Path(cls.working_dir).parent) + path.sep + 'Resources' + path.sep + 'images' + path.sep + 'greenflare-icon-192x192.png'
        pkg_path = cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-192x192.png'
        if path.isfile(pkg_path): 
            return pkg_path
        return cls.working_dir + path.sep + 'greenflare/resources' + path.sep + 'greenflare-icon-192x192.png' 
