"""
State controller.

Kevin Ni, kevin.ni@nyu.edu.
"""

import threading
from threading import Lock
from unicodedata import category as ucat

# from _a_big_red_button.crawler import WokPersistentSessionMeta
from _a_big_red_button.crawler.db import *
from _a_big_red_button.crawler.core import WokSearchResult, WokSearch
from _a_big_red_button.crawler.print_list import WoKPrintArticle
from _a_big_red_button.support.singleton import Singleton

# prepare logger
logger = get_logger('controller')


class Wok(metaclass=Singleton):
    def __init__(self):
        self._searcher: Optional[Wok.AsyncSearch] = None
        self._crawler: Optional[Wok.AsyncCrawler] = None
        self._persistent = WokPersistentStorage()

    # reset options

    def reset_all(self):
        # reset the manager
        assert not self.is_searching
        assert not self.is_crawling
        self._searcher = None
        self._crawler = None

    def reset_crawl(self):
        assert not self.is_crawling
        self._crawler = None

    def reset_search(self):
        assert not self.is_searching and not self.is_crawling
        self._searcher = None

    # search commands and states

    def search(self, term: str):
        term = term.strip()
        term_sanitised = ''.join(char for char in term if ucat(char) != 'Cc')
        self._searcher = self.AsyncSearch(term_sanitised)
        self._searcher.start()

    @property
    def can_search(self):
        return self._searcher is None or not self.is_searching

    @property
    def is_searching(self):
        return self._searcher is not None and self._searcher.searching

    @property
    def search_done(self):
        return self._searcher is not None and self._searcher.done

    @property
    def search_went_wrong(self):
        return self._searcher is not None and self._searcher.in_error

    @property
    def search_result_count(self):
        assert self.search_done and not self.search_went_wrong
        return self._searcher.result.result_count

    @property
    def search_what_went_wrong(self):
        assert self.search_went_wrong
        return self._searcher.error_explanation

    # crawl command and states

    @property
    def can_crawl(self):
        return self.search_done and not self.search_went_wrong \
               and not self.is_crawling

    @property
    def is_crawling(self):
        return self._crawler is not None and self._crawler.crawling

    @property
    def crawling_done(self):
        return self._crawler is not None and self._crawler.done

    @property
    def crawling_went_wrong(self):
        return self.crawling_done and self._crawler.in_error

    @property
    def crawling_total_count(self):
        assert self._crawler is not None
        return self._crawler.end - self._crawler.start_ + 1

    class AsyncSearch(threading.Thread):
        def __init__(self, term: str):
            super(Wok.AsyncSearch, self).__init__()
            self.search: Optional[WokSearch] = None
            self.result: Optional[WokSearchResult] = None
            self.term = term
            self.__started = False
            self.__done = False
            self.__error = False
            self.__exception = None

        @property
        def not_started(self):
            return not self.__started

        @property
        def searching(self):
            return self.__started and not self.done

        @property
        def done(self):
            return self.__started and self.__done

        @property
        def in_error(self):
            return self.__error

        @property
        def error_explanation(self):
            if self.__exception is None:
                return None
            return f'{self.__exception}'

        def run(self) -> None:
            self.__started = True
            try:
                self.search = WokSearch.make_new_search()
                self.result = self.search.search(self.term)
                self.__done = True
                if self.result is None:
                    self.__error = True
            except Exception as e:
                self.__done = True
                self.__error = True
                self.__exception = e
                logger.error(f'search failed: {e}')

    class AsyncCrawler(threading.Thread):
        def __init__(self, wok_result: WokSearchResult,
                     start: int, end: int, year_range: range = None,
                     session: WokPersistentSession = None):
            super().__init__()
            self.result = wok_result
            self.finished_count = 0
            self.start_, self.end, self.year_range = start, end, year_range
            # use the entire range if start and end are all provided as 0
            if self.start_ <= 0:
                self.start_ = 1
            if self.end <= 0:
                self.end = self.result.result_count
            logger.debug(f'using default range for crawler: '
                         f'[{self.start_} -> {self.end}]')
            self.__mutex = Lock()
            self.pool: List[WoKPrintArticle] = []
            self.capacity = 50
            self.session, self.export = session, session is not None
            if not self.export:
                logger.warning(f"not exporting crawler result, "
                               f"no record will be available afterwards")

            # states
            self.__started = False
            self.__done = False
            self.__error = False

            # process meta
            meta = WokPersistentSessionMeta.find_by_session(self.session)
            if meta is None:
                meta = WokPersistentSessionMeta.make_new_for_session(self.session)
            self.meta = meta

        @property
        def not_stared(self):
            with self.__mutex:
                return not self.__started

        @property
        def crawling(self):
            with self.__mutex:
                return self.__started and not self.__done

        @property
        def done(self):
            with self.__mutex:
                return self.__done

        @property
        def in_error(self):
            with self.__mutex:
                return self.__done and self.__error

        def run(self) -> None:
            # update states
            with self.__mutex:
                self.__started = True

            # do the following
            try:
                for print_list in self.result.request_all_print_lists(self.start_, self.end):
                    for article in print_list.find_all_articles(self.year_range):
                        self.finished_count += 1

                        if self.export:
                            self.pool.append(article)

                            if len(self.pool) >= self.capacity:
                                self.session.insert_many(
                                    [a.as_export_dict() for a in self.pool])
                                self.pool.clear()
            except Exception as e:
                logger.error(f"crawled failed: {e}")
                with self.__mutex:
                    self.__done = True
                    self.__error = True

            if self.pool:
                self.session.insert_many(
                    [a.as_export_dict() for a in self.pool])
                self.pool.clear()

            # update meta
            self.meta.add_range(range(self.start_, self.end + 1))
            self.meta.update_last_searched()
            self.meta.save()

            with self.__mutex:
                logger.info("crawling done")
                self.__done = True

    def crawl(self, start: int, end: int, year_range=None):
        self._crawler = self.AsyncCrawler(self._searcher.result,
                                          start, end, year_range,
                                          self._persistent[self._searcher.term])
        self._crawler.start()

    @property
    def crawling_progress(self):
        assert self.is_crawling or \
               (self.crawling_done and not self.crawling_went_wrong)
        return self._crawler.finished_count
