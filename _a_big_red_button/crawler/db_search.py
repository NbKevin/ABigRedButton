"""
This script implements the feature of searching for relative information
concerning a given name (abbreviation).

Kevin Ni, kevin.ni@nyu.edu.
"""

from _a_big_red_button.crawler.db import *
from _a_big_red_button.crawler.db_article import WokAuthorStub, WokCitationStub


class WokLocalSessionSearchResult(PyObjectLike):
    # typed field notation
    coauthors: Set[WokAuthorStub]
    citation: Set[WokCitationStub]
    keywords: Set[str]
    publisher: Set[str]
    emails: Set[str]
    doi: Set[str]

    # list of decorated fields
    __fields__ = ['coauthors', 'citation', 'keywords', 'publisher', 'emails', 'doi']

    def __getattr__(self, item):
        if item in self.__fields__:
            setattr(self, item, set())
            return getattr(self, item)

    def __init__(self):
        super().__init__()


def search_in_all_sessions(author: str) -> WokLocalSessionSearchResult:
    return join_search_result(*(search_in_session(session, author) for session in WokPersistentStorage().all_sessions))


def search_in_session(session: WokPersistentSession, author: str) -> WokLocalSessionSearchResult:
    # step by step progress
    # first we search for all the articles where the given author is listed as AUTHORS
    result = WokLocalSessionSearchResult()

    # TODO search with MongoDB
    # session.collection.find({"author": author})

    for article in session.articles:
        for author_ in article.author:
            if author.upper() in author_.abbr.upper() or author in author_.full.upper():
                # add information from this article into the result
                # first we go with the author
                for author__ in article.author:
                    if author.upper() in author__.abbr.upper() or author in author__.full.upper():
                        continue
                    result.coauthors.add(author__.clone())

                # then we go with the emails
                for email in article.email:
                    result.emails.add(email)

                # then we go with publisher
                result.publisher.add(article.pub)

                # then we go with keywords
                if article.keywordplus is not None:
                    for keyword in article.keywordplus:
                        result.keywords.add(keyword)

                # then citation
                for citation in article.citation:
                    result.citation.add(citation.clone())

                # then DOI
                result.doi.add(article.doi)
    return result


def join_search_result(*results: WokLocalSessionSearchResult) -> WokLocalSessionSearchResult:
    final_result = WokLocalSessionSearchResult()
    for result in results:
        for field in final_result.__fields__:
            setattr(final_result, field, getattr(final_result, field).union(getattr(result, field)))
    return final_result
