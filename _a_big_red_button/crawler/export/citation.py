"""
This script implements a very simple scheme for exporting
the relationship between authors using citation as the measure.

Kevin Ni, kevin.ni@nyu.edu.
"""

# import is limited to selected package for security concern
# also for that you will not ruin the system even if you got
# things wrong

from _a_big_red_button.crawler.db import WokPersistentSession
from _a_big_red_button.crawler.export_helper import WokPersistentSessionExportHelper
from _a_big_red_button.crawler.export.tools import *


def export(session: WokPersistentSessionExportHelper):
    data = dict()
    for article in session.articles:
        data[article.first_author_abbr] = {}

    for article in session.articles:
        first_author = article.first_author_abbr
        for citation in article['citation']:
            cited_author = normalize_name(citation.first_author)
            if cited_author in data:
                if cited_author not in data[first_author]:
                    data[first_author][cited_author] = 0
                data[first_author][cited_author] += 1

    for a, a_val in data.items():
        for b, b_val in a_val.items():
            session.write_edge(a, b, b_val)
