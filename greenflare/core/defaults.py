import sys
from os import path

class Defaults:

	version = '0.91'
	crawl_items = [	
		'url',
		'content_type',
		'status_code',
		'indexability',
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

	settings = {
		'MODE': 'Spider',
		'THREADS': 5,
		'URLS_PER_SECOND': 0,
		'USER_AGENT': 'Greenflare SEO Spider/1.0',
		'UA_SHORT': 'Greenflare',
		'MAX_RETRIES': 3,
		'CRAWL_ITEMS': crawl_items
	}

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

	@classmethod
	def set_working_dir(cls, directory):
		cls.working_dir = directory

	@classmethod
	def root_icon(cls):
		return cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-32x32.png'

	@classmethod
	def about_icon(cls):
		return cls.working_dir + path.sep + 'resources' + path.sep + 'greenflare-icon-192x192.png'

	# platform specific settings
