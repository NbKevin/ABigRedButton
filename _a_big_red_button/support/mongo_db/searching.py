"""
Useful mix-ins for searching in a Mongo database.
"""

from typing import *
from pymongo.database import Database as MongoDatabase
from pymongo.collection import Collection as MongoCollection
from cached_property import threaded_cached_property
from _a_big_red_button.support.mongo_db import MongoDocumentAsPyObject
from _a_big_red_button.support.mongo_db.filters import aggregate_filters


class MongoSearchMixin:
    _T = TypeVar('_T')

    # wrapper class
    _clz: ClassVar[_T] = None

    # collection
    _collection: MongoCollection

    @staticmethod
    def _wrap_filters(**kwargs):
        return aggregate_filters(*({k: v} for k, v in kwargs.items()))

    @classmethod
    def _wrap_cursor_as_iter(cls, iterator, custom_type: type = None):
        if custom_type is not None:
            wrapped_type = custom_type
        elif cls._clz is None:
            wrapped_type = cls
        else:
            wrapped_type = cls._clz

        for item in iterator:
            yield wrapped_type(item)

    @classmethod
    def search(cls, no_wrapping=False, **kwargs):
        if no_wrapping:
            return cls._collection.find(filter=cls._wrap_filters(**kwargs))
        return cls._wrap_cursor_as_iter(
            cls._collection.find(filter=cls._wrap_filters(**kwargs)))

    @classmethod
    def find_one(cls, no_wrapping=False, **kwargs):
        result = cls.search(no_wrapping, **kwargs)
        for item in result:
            return item
        return None

    @classmethod
    def all(cls):
        return cls.search()

    @classmethod
    def count(cls):
        return cls._collection.count_documents({})
