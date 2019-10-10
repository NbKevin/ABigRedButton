"""
Predefined filters and operation upon filters for manipulating mongodb.

Bin Ni. kevin.ni@nyu.edu.
"""

from bson.objectid import ObjectId


def aggregate_filters(*filters: dict):
    """
    Aggregate a series of filters. The result will be the union of all filters provided.
    Filters with the same key would be overwritten by ones proceeding them in the argument
    list.

    :param filters: filters
    :return: the aggregated filter
    """
    new_filter = {}
    for filter in filters:
        new_filter.update(filter)
    return new_filter


def or_filters(*filters: dict):
    """
    Connect a series of filters with $or logical operator.

    :param filters: filters
    :return: the combined filter
    """
    return {"$or": list(filters)}


def and_filters(*filters: dict):
    """
    Connect a series of filters with $and logical operator.

    :param filters: filters
    :return: the combined filter
    """
    return {"$and": list(filters)}


def filter_by_object_id(object_id: ObjectId):
    """
    Create a filter targeting one particular object id.

    :param object_id: target object id, can also be a string
    :return: the filter
    """
    return {"_id": object_id if isinstance(object_id, ObjectId) else ObjectId(object_id)}


def update(content: dict):
    """
    Create an update command.

    :param content: content to be updated
    :return: the command
    """
    return {"$set": content}
