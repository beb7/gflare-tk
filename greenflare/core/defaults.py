import sys
from os import path


class Defaults:

    version = '0.92.2'

    crawl_items = [
        'url',
        'crawl_status',
        'status_code',
        'content_type',                
        'page_title',
        'meta_description',
        'h1',
        'h2',
        'unique_inlinks',
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
        'CRAWL_ITEMS': crawl_items
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

    linux_theme = 'arc'

    @classmethod
    def set_working_dir(cls, directory):
        cls.working_dir = directory

    @classmethod
    def root_icon(cls):
        return cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-32x32.png'

    @classmethod
    def about_icon(cls):
        return cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-192x192.png'
