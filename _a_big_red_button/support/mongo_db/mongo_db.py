"""
This script offers connectivity to backend mongodb server and
abstraction of basic mongodb structures.

Bin Ni. kevin.ni@nyu.edu.
"""

from _a_big_red_button.support.configuration import get_config, BOOT_CFG, RUNNING_IN_DEV_ENV
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.support.python_object_bridge import PyObjectLike, json_object_to_py_object, \
    py_object_to_json_object
from pymongo import MongoClient
from pymongo.collection import Collection
from bson.objectid import ObjectId
from .filters import filter_by_object_id, update

# prepare the logger
__logger = get_logger('db')

# load the configuration
CONFIG = get_config('db')

# parse configuration
__CONNECTION_PARAMETERS = CONFIG.connection.debug if BOOT_CFG.flask.debug else CONFIG.connection.deploy
HOST = __CONNECTION_PARAMETERS.host
PORT = __CONNECTION_PARAMETERS.port

# mongo client
if not RUNNING_IN_DEV_ENV:
    mongo_connection = MongoClient(host=HOST, port=PORT)
    __logger.info('Running in deployment environment, connected to mongodb')
else:
    mongo_connection = MongoClient(host=HOST, port=PORT)
    __logger.info('Running in development environment, connected to mongodb as guest')
__logger.info('Connected to database at %s:%s' % (HOST, PORT))


class MongoDocumentAsPyObject(PyObjectLike):
    """
    Delegates one mongodb document to an python object and offers
    utilities to convert to and back from its document representation.
    """

    def __init__(self, src: dict):
        # type annotations
        self._id: ObjectId = None

        json_object_to_py_object(src, self)
        self.__mongodb_document_src = src

    @staticmethod
    def __create_custom_serialisation_filter(for_saving=False):
        """
        Create a filter that filters out all non-public fields other than the "_id" one.
        Intended as the additional filter for serialisation.

        :param for_saving: if the serialisation is for saving to the database
        :return: the filter function
        """

        def wrapped_filter(obj, attribute_name: str):
            """
            The actual filter.

            :param obj: the object that is being serialised
            :param attribute_name: the name of the attribute
            :return: if the attribute should be skipped during serialisation
            """
            if attribute_name.startswith('_'):
                if attribute_name == "_id" and not for_saving:
                    return False
                return True
            return False

        return wrapped_filter

    @property
    def dict(self):
        new_dict = {}
        py_object_to_json_object(self, new_dict,
                                 self.__create_custom_serialisation_filter())
        return new_dict

    @property
    def dict_for_saving(self):
        new_dict = {}
        py_object_to_json_object(self, new_dict,
                                 self.__create_custom_serialisation_filter(for_saving=True))
        return new_dict

    def save(self, target_collection: Collection):
        """
        Save this document into a collection.

        :param target_collection: target collection to save this document
        """
        if self.object_id is None:
            result = target_collection.insert_one(self.dict_for_saving)
            self._id = result.inserted_id
        else:
            result = target_collection.update_one(
                filter_by_object_id(self.object_id), update(self.dict_for_saving))

        return result

    @property
    def object_id(self):
        return self._id

    def drop(self, from_collection: Collection):
        """
        Drop this entry from a collection.

        :param from_collection: source collection to drop this entry from
        """
        if self.object_id is None:
            return

        return from_collection.delete_one(filter_by_object_id(self.object_id))
