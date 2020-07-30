import re
import urllib.parse
from ua_parser import user_agent_parser

class GFlareRobots:
	def __init__(self, robots_txt, user_agent=None):
		self.robots_txt = robots_txt
		self.user_agent = user_agent
		self.disallows = []
		self.allows = []
		self.allow_lines = None
		self.disallow_lines = None
		if self.robots_txt:
			if self.user_agent:
				self.robots_txt = self.get_ua_rules(self.user_agent, self.robots_txt)
			self.parse_rules()
			self.allows = self.process_rules(self.allows)
			self.disallows = self.process_rules(self.disallows)

	def get_ua_pattern(self, ua):
		return fr'.*User\-agent\:\s*{re.escape(ua)}\s*(#|\n)(.*?)(User\-agent\:|$)'

	def get_ua_rules(self, ua, robots_txt):
		parsed_ua = user_agent_parser.Parse(ua)
		if 'user_agent' in parsed_ua: ua = parsed_ua['user_agent']['family']

		pattern = self.get_ua_pattern(ua)
		match = re.match(pattern, robots_txt, re.DOTALL)
		if match: 
			return match.group(2).strip()
		else:
			pattern = self.get_ua_pattern('*')
			match = re.match(pattern, robots_txt, re.DOTALL)
			if match: return match.group(2).strip()
			return ''

	def remove_spaces(self, inp):
		return " ".join(inp.split(" "))

	def set_robots_txt(self, robots_txt, user_agent=None):
		self.robots_txt = robots_txt
		if user_agent:
				self.user_agent = user_agent
				self.robots_txt = self.get_ua_rules(self.user_agent, self.robots_txt)
		self.parse_rules()
		self.allows = self.process_rules(self.allows)
		self.disallows = self.process_rules(self.disallows)

	def parse_rules(self):
		exp_disallow_rule = re.compile(r"\s*Disallow:\s*(.*)", re.IGNORECASE)
		exp_allow_rule = re.compile(r"\s*Allow:\s*(.*)", re.IGNORECASE)

		for row in self.robots_txt.splitlines():
			row = self.remove_spaces(row)
			
			# Avoid := walrus operator for now to allow Python 3.7 compatibility
			d_match = re.match(exp_disallow_rule, row)
			if d_match: self.disallows.append(d_match.group(1))
			
			a_match = re.match(exp_allow_rule, row)
			if a_match: self.allows.append(a_match.group(1))

		self.allow_lines = sorted(self.allows.copy(), key=len, reverse=True)
		self.disallow_lines = sorted(self.disallows.copy(), key=len, reverse=True)

	def process_rules(self, rules):
		rules = [re.escape(l).replace("\*", ".*").replace("\$", "$") for l in rules]
		for i, r in enumerate(rules):
			if not re.match(r"^\.\*.*", r): rules[i] = f"^{r}"
			if not re.match(r".*\$|.*\.\*$", r): rules[i] = f"{r}.*"
		return re.compile("|".join([f"({r})" for r in rules]))

	def is_allowed(self, url):
		scheme, netloc, path, query, frag = urllib.parse.urlsplit(url)
		url = str(urllib.parse.urlunsplit(("", "", path, query, "")))
		allow = None
		disallow = None

		if self.allow_lines:
			a_match = re.match(self.allows, url)
			if a_match:
				group = 0
				for m in a_match.groups():
					group += 1
					if m: break
				allow = self.allow_lines[group -1]
		if self.disallow_lines:
			d_match = re.match(self.disallows, url)
			if d_match:
				group = 0
				for m in d_match.groups():
					group += 1
					if m: break
				disallow = self.disallow_lines[group -1]

		if allow and not disallow: return True
		if not allow and disallow: return False
		if allow and disallow: return len(allow) >= len(disallow)
		return True