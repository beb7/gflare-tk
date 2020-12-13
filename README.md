# Greenflare SEO Web Crawler
[![PyPI version](https://badge.fury.io/py/greenflare.svg)](https://badge.fury.io/py/greenflare)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/greenflare.svg)](https://img.shields.io/pypi/pyversions/greenflare.svg)
[![Downloads](https://pepy.tech/badge/greenflare)](https://pepy.tech/project/greenflare)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Greenflare is a lightweight free and open-source SEO web crawler for Linux, Mac, and Windows, and is dedicated to delivering high quality 
SEO insights and analysis solutions to the world.

## Features

* Cross-platform (Linux, Mac, and Windows)
* Low hardware requirements
* Scalable (tested against sites with 4M+ URLs) 
* Reports on on-page SEO elements (i.e. page title, meta robots, canonical tag)
* Analysis of HTTP header responses (i.e. X-Robots-Tag, Canonical HTTP Header)
* Status code reporting (i.e. 301, 404, 503 etc.) 
* robots.txt parser (implemented against the suggested REP standard by Google)
* Custom extraction through XPath or CSS
* Custom exclusion of URLs through various patterns
* Quick filtering and sorting of crawl data
* View broken internal links (3xx, 4xx, 5xx)
* Greenflare databases (.gflaredb) are sqlite tables 
* Export any view to CSV


## Getting Started

The quickest way to get started using Greenflare is to download one of 
our pre-built installers. Choose the version for your OS from our Download page:

https://greenflare.io/download

## Python Package

Greenflare is also available as a pypi package:

`pip install greenflare`

The use of a virtual environment (venv) is recommended. 
Linux users may chose to install ttkthemes for an improved visual experience.  


## Developers

Are you interested in becoming more involved in the development of 
Greenflare? Please submit a pull request if you want to help to build new amazing features or to fix nasty bugs!
Alternatively, please email ben at greenflare dot io

## Report a bug

Please report bugs by creating a new issue directly on GitHub:

https://github.com/beb7/gflare-tk/issues
