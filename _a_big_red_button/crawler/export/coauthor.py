"""
This script implements a very simple scheme for exporting
the relationship between co-authors.

Kevin Ni, kevin.ni@nyu.edu.
"""

# import is limited to selected package for security concern
# also for that you will not ruin the system even if you got
# things wrong
# also please do not touch the default import lines

from pathlib import Path
from itertools import combinations
from _a_big_red_button.crawler.db import WokPersistentSession
from _a_big_red_button.crawler.export_helper import WokPersistentSessionExportHelper
from _a_big_red_button.crawler.export.tools import *


def export(session: WokPersistentSessionExportHelper):
    # first construct a dict from authors to count of co-authors
    data = dict()

    # then scan through the articles and count co-authors for every user
    for article in session.articles:
        # generate enumeration for every single pair of co-authorship
        # this has to be permutation aka. unordered since co-authorship
        # does not constitute direction
        for (author_a, author_b) in combinations(article.all_authors_full, 2):
            identifier = frozenset([author_a, author_b])
            if identifier not in data:
                data[identifier] = 0
            data[identifier] += 1

    # then glue together authors that have publish that shares keywords
    for (a, b), count in data.items():
        session.write_edge(str(a), str(b), count)


if __name__ == '__main__':
    # test script
    # test passed
    export(
        WokPersistentSessionExportHelper(
            WokPersistentSession.find_by_session_id(
                '6bbc47cd37734349498828fe50ec0968b6253e20'),
            file_name=Path('Y:/blogtestout/d.csv')))
