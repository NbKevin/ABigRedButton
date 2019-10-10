"""
This script implements a wrapper around the raw articles downloaded
into the local sessions.

Kevin NI, kevin.ni@nyu.edu.
"""

from typing import *
from _a_big_red_button.support.mongo_db.mongo_db import MongoDocumentAsPyObject


class WokAuthorStub(MongoDocumentAsPyObject):
    # typed field notation
    # annotation is for type hinting only
    # this class is not used at run time
    abbr: str
    full: str


class WokCitationStub(MongoDocumentAsPyObject):
    first_author: str
    journal: str
    volume: str
    issue: str
    page: int
    year: int
    doi: str


class WokArticleStub(MongoDocumentAsPyObject):
    # typed field notation
    author: List[WokAuthorStub]
    abstract: str
    addr: List[str]
    cauthor: str
    citation: List[WokCitationStub]
    citecount: int
    direction: List[str]
    doi: str
    eissn: str
    email: List[str]
    ids: str
    issn: str
    journal: str
    keyword: List[str]
    keywordplus: List[str]
    lang: str
    pub: str
    pubaddr: str
    pubabbr: str
    pubisoabbr: str
    quote: int
    quote180: int
    quote2013: int
    quotewoscore: int
    title: str
    type: str
    v: int
    i: int
    p: int
    wosno: str
    wostype: List[str]
    year: str

    def __init__(self, source: dict):
        super().__init__(source)
