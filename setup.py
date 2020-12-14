'''
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
'''

from setuptools import setup, find_packages
from greenflare.core.defaults import Defaults

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='greenflare',
    version=Defaults.version,
    description='SEO Web Crawler and Analysis Tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://greenflare.io',
    project_urls={
        'Source': 'https://github.com/beb7/gflare-tk/',
        'Tracker': 'https://github.com/beb7/gflare-tk/issues',
    },
    author='Benjamin Görler',
    author_email='ben@greenflare.io',
    license='GPLv3+',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests', 'lxml', 'cssselect', 'ua-parser', 'pillow', 'packaging'],
    entry_points={
        'console_scripts': [
            'greenflare=greenflare.app:main',
        ]
    },
)
