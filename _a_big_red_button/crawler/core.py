"""
This script implements a simple crawler interface scraping data from
Web of Knowledge (webofknowledge.com). It was partially inspired by the
original script written by Yiyun Fan, yf855@nyu.edu.

Kevin Ni, kevin.ni@nyu.edu.
"""

from typing import *
import re
import csv
import requests
import time
from io import StringIO
from lxml import etree
from queue import Queue, Empty, Full
import threading
from _a_big_red_button.support.configuration import get_config
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.crawler.print_list import WoKPrintList
from _a_big_red_button.consolesync import CONSOLE_SYNC_HANDLER

# get logger
logger = get_logger('crawler', CONSOLE_SYNC_HANDLER, force_add_additional=True)

# get config
_config = get_config('crawler')


class WokSearchResult:
    def __init__(self, result_url: str, result_count: int,
                 search_id: str, search_term: str,
                 session: requests.Session, headers: Dict[str, str]):
        self.result_url, self.result_count = result_url, result_count
        self.search_id, self.search_term = search_id, search_term
        self.session, self.headers = session, headers

        # threading primitives
        self.task_queue = Queue()
        self.result_queue = Queue()

    @staticmethod
    def assemble_print_list_url(start: int, end: int, search_id: str, search_term: str):
        return _config.url.print_list.format(
            from_=start, to=end, sid=search_id, term=search_term)

    class PrintListRequestWorker(threading.Thread):
        def __init__(self, task_queue: Queue, result_queue: Queue,
                     search_id: str, search_term: str,
                     result_count: int, step: int,
                     session: requests.Session,
                     intermission: int, worker_number: int):
            super().__init__()
            self.task_queue, self.result_queue = task_queue, result_queue
            self.search_id, self.search_term = search_id, search_term
            self.result_count, self.step = result_count, step
            self.session, self.headers = session, self.assemble_headers(search_id)
            self.intermission = intermission
            self.worker_number = worker_number

        def __repr__(self):
            return f"PrintListRequestWorker(number={self.worker_number})"

        @staticmethod
        def assemble_headers(search_id: str):
            headers = _config.headers.base.dict.copy()
            headers['Referer'] = \
                _config.headers.print_list['Referer'].format(search_id=search_id)
            return headers

        def run(self) -> None:
            while True:
                time.sleep(self.intermission)
                try:
                    start = self.task_queue.get(timeout=5)
                except Empty:
                    logger.debug(f"{self}: no more available tasks")
                    break
                else:
                    if start is None:
                        logger.info(f"{self}: no more tasks at all")
                        break

                    # notify the producer
                    self.task_queue.task_done()

                    # compute the request range
                    # end = start + self.step - 1
                    # end = min(end, self.result_count)
                    (start, end) = start

                    # request the print list
                    url = WokSearchResult.assemble_print_list_url(
                        start, end, self.search_id, self.search_term)
                    logger.info(f"requesting print list [{start} -> {end}]...")
                    req = self.session.get(url, headers=self.headers)

                    # validate response
                    if req.status_code != 200:
                        logger.error(f"cannot request print list [{start} -> {end}]: "
                                     f"status code = [{req.status_code}], "
                                     f"response = [{req.content}]")
                        logger.critical(f"PRINT LIST [{start} -> {end}] "
                                        f"HAS BEEN SKIPPED")
                        continue

                    # parse response
                    req.encoding = 'utf-8'  # force UTF-8
                    try:
                        self.result_queue.put(
                            WoKPrintList(StringIO(req.text), start, end), timeout=5)
                    except Full:
                        logger.error(f"cannot put print list [{start} -> {end}] "
                                     f"back in queue: timed out")
                        logger.critical(f"PRINT LIST [{start} -> {end}] "
                                        f"HAS BEEN SKIPPED")

            logger.info(f"{self}: concluded")

    def request_all_print_lists(self, start_from, stop_by: int) -> \
            Generator[WoKPrintList, Any, Any]:
        # validate range and step
        # or so called sanitising the parameters
        step = _config.core.result_iter_step
        if step > 50 or step < 10:
            logger.warning(f"iterating through all results using step = [{step}], "
                           f"this may cause unknown problems, use at your own risk")
        if stop_by > self.result_count:
            logger.warning(f"iterating through [{start_from} -> {stop_by}] "
                           f"exceeds maximum result number, using that instead")
            stop_by = self.result_count
        if start_from < 1:
            logger.warning(f"iterating through [{start_from} -> {stop_by}] "
                           f"exceeds minimum result number, using 1 instead")
            start_from = 1
        current_start = start_from

        # determine starting points and enqueue them as tasks
        while current_start <= stop_by:
            self.task_queue.put((current_start, min(current_start + step - 1, stop_by)))
            current_start += step

        # start worker threads
        threads = []
        worker_number = _config.core.worker_num
        for i in range(worker_number):
            threads.append(self.PrintListRequestWorker(
                self.task_queue, self.result_queue,
                self.search_id, self.search_term, self.result_count,
                step, self.session,
                _config.core.worker_intermission, i
            ))
            threads[-1].start()
        logger.info(f"started {worker_number} worker threads")

        while True:
            try:
                yield self.result_queue.get(timeout=3)
            except Empty:
                if not self.result_queue.empty():
                    logger.error("this should not happen: result pipe not drained yet")
                if not any(filter(lambda thread: thread.is_alive(), threads)):
                    logger.info("all workers has finished")
                    break

        # join worker threads
        for thread in threads:
            thread.join()


class WokSearch:
    @staticmethod
    def extract_search_id_from_url(url: str):
        match = re.search(r'(SID=)(\w+)(?!\w)', url)
        if match is None or len(match.groups()) != 2:
            raise RuntimeError(f'cannot extract search ID from url [{url}]')
        return match.groups()[-1]

    @staticmethod
    def make_new_search():
        logger.info("making a new search...")
        session = requests.Session()
        req = session.get(_config.url.index, headers=_config.headers.base.dict)
        if req.status_code != 200:
            raise RuntimeError(f'failed making a new search: status code [{req.status_code}]')
        sid = WokSearch.extract_search_id_from_url(req.url)
        return WokSearch(sid, req.url, session)

    def __init__(self,
                 search_id: str, search_url: str, session: requests.Session):
        self.search_id = search_id
        self.session = session
        self.search_headers = self.assemble_search_headers()
        self.search_url = search_url
        logger.info(f"created new search with SID [{self.search_id}]")

    def assemble_search_headers(self):
        search_headers: Dict[str, str] = _config.headers.base.dict.copy()
        search_headers.update(_config.headers.search.dict)
        search_headers['Referer'] = search_headers['Referer'].format(search_id=self.search_id)
        return search_headers

    def assemble_search_form(self, term: str):
        form: Dict[str, str] = _config.form.search.dict.copy()
        form['SID'] = self.search_id
        form['value(input1)'] = term
        return form

    @staticmethod
    def parse_error_message(root: etree):
        error_message_node = root.xpath('//div[@id="searchErrorMessage"]/div[@class="errorText"]//text()')
        if error_message_node is None or not error_message_node:
            return None
        return error_message_node[0]

    def search(self, term: str):
        logger.info(f"searching for [{term}]...")
        req = self.session.post(_config.url.search,
                                data=self.assemble_search_form(term),
                                headers=self.search_headers)
        req.encoding = req.apparent_encoding

        # try to parse the response text
        root = etree.parse(StringIO(req.text),
                           parser=etree.HTMLParser(recover=True, encoding=req.encoding))
        result_url = root.xpath('//a[@id="hitCount"]/@href')
        result_count = root.xpath('//a[@id="hitCount"]//text()')
        if len(result_url) != 1 or len(result_count) != 1:
            error_message = self.parse_error_message(root)
            if error_message is None:
                # logger.error(f"invalid search response: {req.content}")
                logger.critical("PROGRAM TERMINATED")
                raise RuntimeError('invalid response')
            else:
                logger.error(f"search failed: {error_message}")
                raise RuntimeError(f'invalid search term: {error_message}')

        result_url = result_url[0]
        result_count = int(result_count[0].replace(',', ''))
        logger.info(f"found {result_count} matches for search [{term}]")

        return WokSearchResult(result_url, result_count,
                               self.search_id, term,
                               self.session, self.search_headers)


if __name__ == "__main__":
    # with open('test.txt', mode='r', encoding='utf-8') as test_file:
    #     plist = WoKPrintList(test_file)
    #     count = 0
    #     for g in plist.find_all_articles():
    #         print(g)
    #         count += 1
    #         # for i in g.attributes:
    #         # print(i)
    #     print(f"scanned {count} articles")

    search = WokSearch.make_new_search()
    result = search.search(
        "TS=((China OR PRC) AND (Guangzhou))")
    count = 0
    for print_list in result.request_all_print_lists(-500, 27):
        # logger.debug(print_list)
        for article in print_list.find_all_articles(range(2010, 2020)):
            # logger.info(article)
            count += 1
    logger.info(f"found {count}/{result.result_count} articles")
