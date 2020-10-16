import sys
import unittest

sys.path.append('..')
from greenflare.core.gflarerobots import GFlareRobots

class TestRobotsTxt(unittest.TestCase):

	def test_basic(self):
		robots_txt = "User-agent: *\nDisallow: /test/"
		ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
		
		allowed_url = "https://www.example.com/is/allowed.html"
		disallowed_url = "https://www.example.com/test/is/not/allowed.html"

		robot = GFlareRobots(robots_txt, user_agent=ua)
		self.assertEqual(robot.is_allowed(allowed_url), True, "Should be allowed")
		self.assertEqual(robot.is_allowed(disallowed_url), False, "Should be disallowed")

	def test_ua_as_submatch(self):
		robots_txt = "User-agent: *\nAllow: /\nUser-agent: Google\nDisallow: /test/"
		ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
		
		allowed_url = "https://www.example.com/is/allowed.html"
		disallowed_url = "https://www.example.com/test/is/not/allowed.html"

		robot = GFlareRobots(robots_txt, user_agent=ua)
		self.assertEqual(robot.is_allowed(allowed_url), True, "Should be allowed")
		self.assertEqual(robot.is_allowed(disallowed_url), False, "Should be disallowed")

	def test_least_restrictive(self):
		robots_txt = "User-agent: *\nDisallow: /test*\nAllow: /test/"
		ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
		
		allowed_url = "https://www.example.com/test/is/allowed.html"
		robot = GFlareRobots(robots_txt, user_agent=ua)
		self.assertEqual(robot.is_allowed(allowed_url), True, "Should be allowed")

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
		self.assertEqual(robot.is_allowed(allowed_url), True, "Should be allowed")
		self.assertEqual(robot.is_allowed(disallowed_url), False, "Should be disallowed")

if __name__ == '__main__':
	unittest.main()