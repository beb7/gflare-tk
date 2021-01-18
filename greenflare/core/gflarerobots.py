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
                self.robots_txt = self.get_ua_rules(
                    self.user_agent, self.robots_txt)
            self.parse_rules()
            self.allows = self.process_rules(self.allows)
            self.disallows = self.process_rules(self.disallows)

    def get_matching_user_agent(self, robots_txt, user_agent):

        pattern = r'user\-agent\:\s*(\*|.*?)[\s*|$]'
        all_uas = re.findall(pattern, robots_txt, re.DOTALL | re.IGNORECASE)

        all_uas_ordered_by_specificity = [
            u for u in all_uas if u.lower() in user_agent.lower()]
        all_uas_ordered_by_specificity = sorted(
            all_uas_ordered_by_specificity, key=len, reverse=True)

        if all_uas_ordered_by_specificity:
            return all_uas_ordered_by_specificity[0]
        return None

    def get_ua_pattern(self, ua):
        pattern = f"""
		.*user\-agent\:\s*{re.escape(ua)}\s*	# Matching User-agent directive (escaped to allow User-Agent: *), UA is wrapped by any whitespace 0-n
		[#|\n*]									# Match until comment or newline(s)
		(user\-agent\:.*?[#|\n*])*				# Match any subsequent User-Agent directives that may follow								
		(.*?)									# Group that contains our rules, non-greedy
		(user\-agent\:.*?[#|\n*]|$)				# Until we hit our next User-Agent directive or end of file
		"""
        return pattern

    def get_short_ua(self, user_agent):
        parsed_ua = user_agent_parser.Parse(user_agent)

        if 'user_agent' in parsed_ua:
            return parsed_ua['user_agent']['family']
        return ''

    def get_ua_rules(self, crawler_user_agent, robots_txt):

        ua = self.get_short_ua(crawler_user_agent)
        matching_ua = self.get_matching_user_agent(robots_txt, ua)

        if matching_ua:
            # Extract all rules that belong to this User-agent
            match = re.match(self.get_ua_pattern(matching_ua),
                             robots_txt, re.DOTALL | re.IGNORECASE | re.VERBOSE)
            if match:
                return match.group(2).strip()
        else:
            # Extract all rules that belong to the catch-all User-agent: *
            pattern = self.get_ua_pattern('*')
            match = re.match(pattern, robots_txt, re.DOTALL |
                             re.IGNORECASE | re.VERBOSE)
            if match:
                return match.group(2).strip()
        return ''

    def remove_spaces(self, inp):
        return " ".join(inp.split(" "))

    def set_robots_txt(self, robots_txt, user_agent=None):
        self.robots_txt = robots_txt
        if user_agent:
            self.user_agent = user_agent
            self.robots_txt = self.get_ua_rules(
                self.user_agent, self.robots_txt)
        self.parse_rules()
        self.allows = self.process_rules(self.allows)
        self.disallows = self.process_rules(self.disallows)

    def parse_rules(self):
        exp_disallow_rule = re.compile(r"\s*Disallow:\s*(.*)", re.IGNORECASE)
        exp_allow_rule = re.compile(r"\s*Allow:\s*(.*)", re.IGNORECASE)

        for row in self.robots_txt.splitlines():
            row = self.remove_spaces(row)

            # Avoid := walrus operator for now to allow Python 3.7
            # compatibility
            d_match = re.match(exp_disallow_rule, row)
            if d_match:
                # Skip emtpy Disallow:
                path = d_match.group(1)
                if path:
                    self.disallows.append(path)

            a_match = re.match(exp_allow_rule, row)
            if a_match:
                # Skip emtpy Allow:
                path = a_match.group(1)
                if path:
                    self.allows.append(path)

        self.allow_lines = sorted(self.allows.copy(), key=len, reverse=True)
        self.disallow_lines = sorted(
            self.disallows.copy(), key=len, reverse=True)

    def process_rules(self, rules):
        rules = [re.escape(l).replace("\*", ".*").replace("\$", "$")
                 for l in rules]
        for i, r in enumerate(rules):
            if not re.match(r"^\.\*.*", r):
                rules[i] = f"^{r}"
            if not re.match(r".*\$|.*\.\*$", r):
                rules[i] = f"{r}.*"
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
                    if m:
                        break
                allow = self.allow_lines[group - 1]
        if self.disallow_lines:
            d_match = re.match(self.disallows, url)
            if d_match:
                group = 0
                for m in d_match.groups():
                    group += 1
                    if m:
                        break
                disallow = self.disallow_lines[group - 1]

        if allow and not disallow:
            return True
        if not allow and disallow:
            return False
        if allow and disallow:
            return len(allow) >= len(disallow)
        return True
