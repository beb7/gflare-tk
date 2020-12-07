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

from functools import partial
from csv import writer as csvwriter


def generate_menu(menu, labels, func):
    for label in labels:
        if label != '_':
            action_with_arg = partial(func, label)
            menu.add_command(label=label, command=action_with_arg)
        else:
            menu.add_separator()

def export_to_csv(csv_file, columns, data):

    with open(csv_file, "w", newline='', encoding='utf-8-sig') as csv_file:
        csv_writer = csvwriter(csv_file, delimiter=",", dialect='excel')
        csv_writer.writerow([i for i in columns])
        csv_writer.writerows(data)