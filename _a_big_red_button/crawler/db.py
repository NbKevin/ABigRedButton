"""
Implements the database wrapper for the crawler.

Kevin Ni, kevin.ni@nyu.edu.
"""

from typing import *
import hashlib

from _a_big_red_button.crawler.db_article import WokArticleStub
from _a_big_red_button.support.singleton import Singleton
from _a_big_red_button.support.mongo_db import *
from _a_big_red_button.support.lazy_property import lazy_property
from pymongo.errors import DuplicateKeyError

# prepare logger
logger = get_logger('db')

# get config
config = get_config('db')

# check sql alchemy version
logger.info(f"using mongodb as backend")


class WokPersistentStorage(metaclass=Singleton):
    def __init__(self):
        self.database = mongo_connection.get_database(
            config.databases.crawler_persistent)

    @property
    def all_sessions(self):
        for collection in self.database.list_collections():
            if collection['name'].startswith('Session'):
                continue
            yield WokPersistentSession.find_by_session_id(collection['name'])

    @staticmethod
    def sanitise_metadata():
        """Removes metadata that no longer has an associated session."""
        from _a_big_red_button.crawler.db_meta import WokPersistentSessionMeta
        for metadata in WokPersistentSessionMeta.all_metadata():
            session = WokPersistentSession.find_by_session_id(metadata.session_id)
            if session is None:
                logger.info(f"metadata(session_id={metadata.session_id}) "
                            f"has been dropped because its associated session "
                            f"is not present")
                metadata.drop()

    def __getitem__(self, item):
        if isinstance(item, str):
            return WokPersistentSession(item)
        elif isinstance(item, Collection):
            return WokPersistentSession.find_by_collection(item)

        raise ValueError('term storage can by retrieved '
                         'either by the term or by the collection, '
                         f'not [{item}](type={type(item)})')

    def __repr__(self):
        return f'WokPersistentStorage(session_count={len(list(self.all_sessions))})'


class WokPersistentSession:
    _database = WokPersistentStorage().database

    # for compatibility reason we do not use MD5 but rather
    # a zip then base64 approach
    # okay this did not work so we actually switch to md5

    @staticmethod
    def encode_term(term: str):
        hasher = hashlib.sha1()
        hasher.update(term.encode('utf-8'))
        return hasher.hexdigest()
        # compressed_term = zlib.compress(term.encode('utf-8'), level=8)
        # return base64.urlsafe_b64encode(term.encode('utf-8')).decode('utf-8')
        # return base64.urlsafe_b64encode(compressed_term).decode('utf-8')

    @staticmethod
    def decode_term(encoded_term: str):
        raise RuntimeError("WARNING: DECODE TERM IS NO LONGER AVAILABLE")
        # compressed_term = base64.urlsafe_b64decode(encoded_term.encode('utf-8'))
        # return base64.urlsafe_b64decode(
        #    encoded_term.encode('utf-8')).decode('utf-8')
        # return zlib.decompress(compressed_term).decode('utf-8')

    @staticmethod
    def find_by_term(term: str):
        return WokPersistentSession(term)
        # session_id = WokPersistentSession.encode_term(term)
        # return WokPersistentSession.find_by_session_id(session_id)

    @staticmethod
    def find_by_collection(collection: Collection):
        from _a_big_red_button.crawler.db_meta import WokPersistentSessionTermMeta
        session_id = collection.name
        term_meta = WokPersistentSessionTermMeta.find_by_session_id(session_id)
        if term_meta is None:
            return None
        return WokPersistentSession(term_meta.term)
        # try:
        #     original_term = WokPersistentSession.decode_term(session_id)
        # except Exception as e:
        #     logger.error(f"cannot parse collection name [{session_id}]: {e}")
        # else:
        #     return WokPersistentSession(original_term)

    @staticmethod
    def find_by_session_id(session_id: str):
        for collection_name in WokPersistentSession._database.list_collection_names():
            if collection_name == session_id:
                session = WokPersistentSession._database.get_collection(session_id)
                return WokPersistentSession.find_by_collection(session)
                # term = WokPersistentSession.decode_term(collection_name)
                # return WokPersistentSession(term)
        return None

    def __repr__(self):
        return f'WokPersistentSession(term="{self.term}", count={len(self)})'

    def __init__(self, term: str):
        from _a_big_red_button.crawler.db_meta import WokPersistentSessionTermMeta
        self.term = term
        self.ensure_doi_index()
        if WokPersistentSessionTermMeta.find_by_session_id(self.session_id) is None:
            # then this is the first time this session is being created
            # we save its term meta information into the database
            term_meta = WokPersistentSessionTermMeta.make_new_for_session(self)
            term_meta.save()
            logger.info(f"created new persistent session (id-={self.session_id}, term={self.term})")

    def drop(self):
        self.collection.drop()
        return self.find_by_session_id(self.session_id) is None

    def ensure_doi_index(self):
        try:
            length = len(list(self.collection.list_indexes()))
        except SystemError as e:
            self.collection.create_index("doi", unique=True)
        else:
            if length <= 1:
                self.collection.create_index("doi", unique=True)

    @lazy_property
    def session_id(self):
        return self.encode_term(self.term)

    @property
    def collection(self):
        return self._database.get_collection(self.session_id)

    def insert(self, document: MongoDocumentAsPyObject):
        # note that PersistentSession are stored as collections
        # so no explicit save or create operation is required
        # the target collection will be created the first time
        # something is inserted into the document
        try:
            self.collection.insert_one(document)
        except DuplicateKeyError:
            logger.debug(f"document exists and has been ignored: "
                         f"{document}")

    def insert_many(self, documents: List[MongoDocumentAsPyObject]):
        for document in documents:
            self.insert(document)

    def __len__(self):
        return self.collection.count()

    @property
    def articles(self):
        for document in self.collection.find():
            yield WokArticleStub(document)
