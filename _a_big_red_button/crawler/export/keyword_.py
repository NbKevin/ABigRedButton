"""
This script implements a very simple scheme for exporting
the relationship between authors using citation as the measure.

Kevin Ni, kevin.ni@nyu.edu.
"""

# import is limited to selected package for security concern
# also for that you will not ruin the system even if you got
# things wrong
# also please do not touch the default import lines

from _a_big_red_button.crawler.db import WokPersistentSession
from _a_big_red_button.crawler.export_helper import WokPersistentSessionExportHelper
from _a_big_red_button.crawler.export.tools import *


def export(session: WokPersistentSessionExportHelper):
    # first construct a dict from authors to count of keywords
    data = dict()
    for article in session.articles:
        data[article.first_author_abbr] = {}

    # then scan through the articles and count keywords for every user
    for article in session.articles:
        first_author = article.first_author_abbr
        if not hasattr(article, 'keywordplus') or article.keywordplus is None:
            continue
        for keyword in article.keywordplus:
            if keyword not in data[first_author]:
                data[first_author][keyword] = 0
            data[first_author][keyword] += 1

    # then glue together authors that have publish that shares keywords
    edges = {}
    for author in data:
        for another_author in data:
            if author == another_author:
                continue

            edge = frozenset([author, another_author])
            if edge in edges:
                continue

            count = 0
            for keyword in data[author]:
                if keyword in data[another_author]:
                    count += (data[author][keyword] + data[another_author][keyword])

            if count > 0:
                edges[edge] = count

    for edge, count in edges.items():
        author_a, author_b = edge
        session.write_edge(author_a, author_b, count)
