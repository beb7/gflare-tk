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
import unittest

sys.path.append('..')
from greenflare.core.gflarerobots import GFlareRobots
from greenflare.core.gflareresponse import GFlareResponse


class TestRobotsTxt(unittest.TestCase):

    def test_basic(self):
        robots_txt = "User-agent: *\nDisallow: /test/"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        allowed_url = "https://www.example.com/is/allowed.html"
        disallowed_url = "https://www.example.com/test/is/not/allowed.html"

        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(allowed_url),
                         True, "Should be allowed")
        self.assertEqual(robot.is_allowed(disallowed_url),
                         False, "Should be disallowed")

    def test_ua_as_submatch(self):
        robots_txt = "User-agent: *\nAllow: /\nUser-agent: Google\nDisallow: /test/"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        allowed_url = "https://www.example.com/is/allowed.html"
        disallowed_url = "https://www.example.com/test/is/not/allowed.html"

        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(allowed_url),
                         True, "Should be allowed")
        self.assertEqual(robot.is_allowed(disallowed_url),
                         False, "Should be disallowed")

    def test_least_restrictive(self):
        robots_txt = "User-agent: *\nDisallow: /test*\nAllow: /test/"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        allowed_url = "https://www.example.com/test/is/allowed.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(allowed_url),
                         True, "Should be allowed")

    def test_specificity(self):
        robots_txt = "User-agent: *\nDisallow: /test*\nDisallow: /test/is/"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/is/disallowed.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

    def test_specificity_two(self):
        robots_txt = "User-agent: *\nDisallow: /test/corner/\nAllow: /test/\nDisallow: /test/is/"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/corner/funpart.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

    def test_ua_override(self):
        robots_txt = "User-agent: *\nAllow: /test*\nUser-agent: Google\nDisallow: /"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/is/disallowed.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

    def test_grouped_ua_ends_with_rule(self):
        robots_txt = "User-agent: *\nDisallow: /\nUser-agent: Google\nUser-agent: Bingbot\nAllow: /"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/is/allowed.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), True, "Should be allowed")

    def test_grouped_ua_ends_with_additional_uas(self):
        robots_txt = "User-agent: *\nDisallow: /\nUser-agent: Google\nUser-agent: Bingbot\nUser-agent: Greenflare\nAllow: /\nUser-agent: Yandex\nDisallow: /"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/is/allowed.html"
        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), True, "Should be allowed")

    def test_grouped_ua_ends_with_additional_uas_two(self):
        robots_txt = "User-agent: *\nAllow: /\nUser-agent: Google\n\n\n\nUser-agent:       	Bingbot\nUser-agent: Greenflare      # My own crawler\nDisallow: /test/is/disallowed\nUser-agent: Yandex\nDisallow: /*test"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        ua_greenflare = "Greenflare SEO Spider/1.0"
        ua_bingbot = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        ua_yandex = "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"
        ua_firefox = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"

        url = "https://www.example.com/test/is/disallowed.html"

        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

        robot = GFlareRobots(robots_txt, user_agent=ua_greenflare)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

        robot = GFlareRobots(robots_txt, user_agent=ua_bingbot)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

        robot = GFlareRobots(robots_txt, user_agent=ua_yandex)
        self.assertEqual(robot.is_allowed(url), False, "Should be disallowed")

        robot = GFlareRobots(robots_txt, user_agent=ua_firefox)
        self.assertEqual(robot.is_allowed(url), True, "Should be allowed")

    def test_broken_robots_txt(self):
        robots_txt = "User-agent: *Allow: /\n\nDisallow: /test/is/disallowed\nUser-agent: Yandex\nDisallow: /*test"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        url = "https://www.example.com/test/is/disallowed.html"

        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(url), True, "Should be allowed")

    def test_rogue_sitemap_entry(self):
        robots_txt = "User-agent: *\nAllow: /allowed/section\nSitemap: https://www.example.com/sitemap.xml\nDisallow: /disallowed/section\nDisallow: /*section"
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        allowed_url = "https://www.example.com/allowed/section"
        disallowed_url = "https://www.example.com/disallowed/section"

        robot = GFlareRobots(robots_txt, user_agent=ua)
        self.assertEqual(robot.is_allowed(allowed_url),
                         True, "Should be allowed")
        self.assertEqual(robot.is_allowed(disallowed_url),
                         False, "Should be disallowed")


class TestFullStatus(unittest.TestCase):

    def test_canonical(self):
        gf = GFlareResponse({
            'CRAWL_ITEMS': [
                'canonical_tag',
                'canonical_http_header',
                'robots_txt',
                'meta_robots',
                'x_robots_tag'
            ]
        }, columns=None)
        seo_items = {'status_code': 200,
                     'canonical_tag': 'https://www.example.com/'}
        url = 'https://www.example.com'

        self.assertEqual(gf.get_full_status(
            url, seo_items), 'ok', 'Should return ok')

        url = 'https://www.example.com/'
        self.assertEqual(gf.get_full_status(
            url, seo_items), 'ok', 'Should return ok')

if __name__ == '__main__':
    unittest.main()
