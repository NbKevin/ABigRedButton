"""
This script implements features related to meta information of
local sessions.

Kevin NI, kevin.ni@nyu.edu.
"""

import base64
import datetime
from threading import Lock
from typing import Dict, Union

from pymongo.collection import Collection

from _a_big_red_button.crawler.db import config, WokPersistentSession, WokPersistentStorage
from _a_big_red_button.support.mongo_db import MongoDocumentAsPyObject
from _a_big_red_button.support.mongo_db.searching import MongoSearchMixin
from _a_big_red_button.support.python_object_bridge import PyObjectLike


class RangeExt:
    """A range that is inclusive on both ends."""

    def __init__(self, start: int, stop: int):
        self.start, self.stop = start, stop

    @staticmethod
    def from_python_range(python_range: range):
        return RangeExt(python_range.start, python_range.stop - 1)

    @staticmethod
    def from_dict(dict_: Dict[str, int]):
        if isinstance(dict_, PyObjectLike):
            dict_ = dict_.dict

        start, end = None, None
        for keyword in ('start', 'from'):
            for key in dict_:
                if keyword in key:
                    start = dict_[key]
                    break
        for keyword in ('end', 'stop'):
            for key in dict_:
                if keyword in key:
                    end = dict_[key]
                    break
        if start is None or end is None:
            raise ValueError(f'cannot extract range from dict [{dict_}]')
        return RangeExt(start, end)

    @property
    def as_python_range(self):
        return range(self.start, self.stop + 1)

    def intersect(self, other: 'RangeExt'):
        return (self.start <= other.stop and self.stop >= other.start) or (
                self.stop >= other.start and self.start <= other.stop)

    def __repr__(self):
        return f'_IntRange({self.start} -> {self.stop})'

    def __add__(self, other: 'RangeExt'):
        if not self.intersect(other):
            raise ValueError('cannot add two ranges that do not intersect')
        return RangeExt(min(self.start, other.start),
                        max(self.stop, other.stop))

    def __iadd__(self, other):
        if not self.intersect(other):
            return self
        new_range = self + other
        self.start, self.stop = new_range.start, new_range.stop
        return self


class WokPersistentSessionMeta(MongoDocumentAsPyObject,
                               MongoSearchMixin):
    _collection = WokPersistentStorage().database.get_collection(
        config.collections.session_metadata)

    @staticmethod
    def all_metadata():
        return WokPersistentSessionMeta.search()

    def save(self, target_collection: Collection = None):
        if target_collection is None:
            super(WokPersistentSessionMeta, self).save(self._collection)
        else:
            super(WokPersistentSessionMeta, self).save(target_collection)

    def drop(self, whatever_other_collection: Collection = None):
        if whatever_other_collection is None:
            super().drop(self._collection)
        else:
            super().drop(whatever_other_collection)
        return WokPersistentSessionMeta.find_by_session_id(self.collection_name) is None

    def __init__(self, src: dict):
        super(WokPersistentSessionMeta, self).__init__(src)
        self._lock = Lock()

    @staticmethod
    def make_new_for_session(session: WokPersistentSession):
        new_metadata = WokPersistentSessionMeta(
            {'collection_name': session.session_id,
             'last_searched': datetime.datetime.utcfromtimestamp(0),
             'crawled_ranges_raw': []})
        return new_metadata

    def __repr__(self):
        return f'WokPersistentSessionMeta(term="{self.term}")'

    @staticmethod
    def find_by_session_id(session_id: str):
        result = WokPersistentSessionMeta.find_one(collection_name=session_id)
        return result

    collection_name: str

    @property
    def session_id(self):
        return self.collection_name

    @property
    def term(self):
        return base64.urlsafe_b64decode(self.collection_name.encode('utf-8')).decode('utf-8')

    @staticmethod
    def find_by_session(session: 'WokPersistentSession'):
        return WokPersistentSessionMeta.find_by_session_id(session.session_id)

    def update_last_searched(self, when: datetime.datetime = None):
        with self._lock:
            if when is None:
                when = datetime.datetime.now()
            self.last_searched = when
            self.save(self._collection)

    @property
    def crawled_ranges(self):
        with self._lock:
            for raw_range in self.crawled_ranges_raw:
                yield range(raw_range.start, raw_range.stop + 1)

    def merge_adjacent_ranges(self):
        if len(self.crawled_ranges_raw) <= 1:
            return
        new_ranges = []
        i = 0
        merge_happened = False
        while i < len(self.crawled_ranges_raw) - 1:
            merge_happened = False
            this_range = RangeExt.from_dict(self.crawled_ranges_raw[i])
            next_range = RangeExt.from_dict(self.crawled_ranges_raw[i + 1])
            while this_range.intersect(next_range):
                merge_happened = True
                this_range += next_range
                i += 1
                if i + 1 >= len(self.crawled_ranges_raw):
                    break
                next_range = RangeExt.from_dict(self.crawled_ranges_raw[i + 1])
            new_ranges.append(this_range)
            i += 1
        if not merge_happened:
            # this means the last range is valid
            new_ranges.append(RangeExt.from_dict(self.crawled_ranges_raw[-1]))

        self.crawled_ranges_raw = \
            [{'start': r.start, 'stop': r.stop} for r in new_ranges]
        self.save(self._collection)

    def add_range(self, new_range: Union[range, RangeExt]):
        with self._lock:
            # parse new range
            if isinstance(new_range, range):
                new_range = RangeExt.from_python_range(new_range)

            for raw_range in self.crawled_ranges_raw:
                old_range = RangeExt.from_dict(raw_range)

                if old_range.intersect(new_range):
                    old_range += new_range
                    raw_range.start, raw_range.stop = \
                        old_range.start, old_range.stop
                    break
            else:
                # make sure new range is inserted at the right place
                # such that the entire list is sorted
                self.crawled_ranges_raw.append({'start': new_range.start,
                                                'stop': new_range.stop})
                self.crawled_ranges_raw.sort(key=lambda r: r['start'])
            self.save(self._collection)
            self.merge_adjacent_ranges()
            self.save(self._collection)


class WokPersistentSessionTermMeta(MongoDocumentAsPyObject, MongoSearchMixin):
    _collection = WokPersistentStorage().database.get_collection("SessionTerms")

    def __init__(self, source: dict):
        super().__init__(source)

    def save(self, alternate_collection: Collection = None):
        super().save(self._collection if alternate_collection is None else alternate_collection)

    @staticmethod
    def find_by_session_id(session_id: str):
        return WokPersistentSessionTermMeta.find_one(session_id=session_id)

    @staticmethod
    def make_new_for_session(session: 'WokPersistentSession'):
        return WokPersistentSessionTermMeta({
            'term': session.term,
            'session_id': session.session_id
        })
