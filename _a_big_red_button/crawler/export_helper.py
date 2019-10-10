"""
Implements a wrapper for a Wok session such that writing
code for exporting to Gephi is easier.

Kevin NI, kevin.ni@nyu.edu.
"""

from typing import List, Any
from pathlib import Path
import shutil
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.support.configuration import get_config
from _a_big_red_button.crawler.db import WokPersistentSession, MongoDocumentAsPyObject
from _a_big_red_button.crawler.db_article import WokArticleStub
from _a_big_red_button.crawler import WokPersistentSessionMeta
from _a_big_red_button.crawler.export.tools import *

# prepare logger
logger = get_logger('export')


class WokPersistentSessionExportHelper:
    @staticmethod
    def from_session_id(session_id: str, file_name: Path):
        return WokPersistentSessionExportHelper(
            WokPersistentSession.find_by_session_id(session_id),
            file_name
        )

    @staticmethod
    def from_term(term: str, file_name: Path):
        return WokPersistentSessionExportHelper(
            WokPersistentSession.find_by_term(term),
            file_name
        )

    def __init__(self, session: WokPersistentSession, file_name: Path):
        self.session = session
        self.meta = WokPersistentSessionMeta.find_by_session(self.session)
        self.file_name = file_name
        self.data = dict()

        if self.meta is None:
            raise RuntimeError(f'cannot create export helper for '
                               f'session(id={self.session.session_id}): '
                               f'no relative metadata is found')

        try:
            if self.file_name.exists():
                backup_file_name = self.file_name.with_suffix('.backup')
                shutil.move(str(self.file_name), str(backup_file_name))
                logger.warning(f'the export file {self.file_name} already exists '
                               f'and has been backed up to {backup_file_name}')

            self.file = open(str(self.file_name), mode='w', encoding='utf-8')
        except Exception as e:
            logger.error(f'cannot create export helper for '
                         f'session(id={self.session.session_id}): '
                         f'cannot open export file "{self.file_name}": '
                         f'{e}')
        else:
            self.write_title_line()

    def write_title_line(self):
        self.file.write(f'Source; Target; Weight\n')

    @property
    def articles(self):
        for document in self.session.collection.find():
            yield WokArticleStubForExporting(document)

    def write_edge(self, from_: str, to: str, weight: int):
        self.file.write(f'{from_}; {to}; {weight}\n')

    def __str__(self):
        return f'WokPersistentSessionExportHelper' \
               f'(session_id={self.session.session_id}, ' \
               f'export_file={self.file_name})'


class WokArticleStubForExporting(WokArticleStub):
    def __init__(self, document: dict):
        super().__init__(document)

        # # then dynamically bind fields
        # crawler_config = get_config('crawler')
        # export_fields = crawler_config.export_fields
        # export_article_fields = export_fields.article
        # export_citation_fields = export_fields.citation

    @property
    def first_author_abbr(self):
        return normalize_name(self.author[0].abbr)

    @property
    def first_author_full(self):
        return normalize_name(self.author[0].full)

    @property
    def all_authors_abbr(self):
        for author in self.author:
            yield normalize_name(author.abbr)

    @property
    def all_authors_full(self):
        for author in self.author:
            yield normalize_name(author.full)
