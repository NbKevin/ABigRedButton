"""
This script offers bridge functions to convert from and to python objects
and their serialised form.

This script is authorised under the 3-Clause BSD code.
#TODO pick a proper licence for these libraries

Kevin Ni. kevin.ni@nyu.edu.
"""

import json
import yaml
from typing import Union
from itertools import islice


class PyObjectLike:
    """Instances of this class open their attributes to modification."""

    def __init__(self, source: dict = None):
        if source is not None:
            for key, value in source.items():
                setattr(self, key, value)

    @property
    def dict(self) -> dict:
        """
        Convert this instance to its equivalent dict form.

        :return: Its equivalent dict.
        """
        new_dict = dict()
        py_object_to_json_object(self, new_dict)
        return new_dict

    # new 11 Feb, 2019
    # use item subscription to access properties as well

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def clone(self):
        return type(self)(self.dict)

    def __str__(self):
        source = islice(self.dict.items(), 3)
        return f'PyObjectLike({", ".join(f"{pair[0]}={pair[1]}" for pair in source)})'


def json_list_to_py_list(source: list, py_list: list):
    """
    Convert a JSON list to python list.

    :param source: Source JSON list.
    :param py_list: Target python list where elements from JSON would be attached to.
    """
    for item in source:
        if isinstance(item, dict):
            py_object = PyObjectLike()
            py_list.append(py_object)
            json_object_to_py_object(item, py_object)
        elif isinstance(item, list):
            new_py_list = []
            py_list.append(new_py_list)
            json_list_to_py_list(item, new_py_list)
        else:
            py_list.append(item)


def json_object_to_py_object(source: dict, py_object: PyObjectLike):
    """
    Convert a JSON object to python object.

    :param source: Source JSON object.
    :param py_object: The python object the JSON fields will be attached to.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            setattr(py_object, key, PyObjectLike())
            json_object_to_py_object(value, getattr(py_object, key))
        elif isinstance(value, (list, set, frozenset)):
            setattr(py_object, key, list())
            json_list_to_py_list(value, getattr(py_object, key))
        else:
            setattr(py_object, key, value)


def py_list_to_json_list(source: Union[list, set, frozenset], json_list: list):
    """
    Convert a python list to JSON list.

    :param source: Source python list.
    :param json_list: Target JSON list where fields would be dumped into.
    """
    for item in source:
        if isinstance(item, PyObjectLike):
            new_json = {}
            py_object_to_json_object(item, new_json)
            json_list.append(new_json)
        elif isinstance(item, (list, set, frozenset)):
            new_list = []
            py_list_to_json_list(item, new_list)
            json_list.append(new_list)
        else:
            json_list.append(item)


def default_serialisation_filter(obj, attribute_name: str):
    """
    Mark generally unwanted fields for serialisation.
    More specifically, it marks following fields:

        - private and magic fields
        - callable fields
        - class fields

    :param obj: subject object
    :param attribute_name: name of the attribute to be tested
    :return: whether the attribute is marked
    """
    if attribute_name.startswith('__'):
        return True
    if hasattr(obj.__class__, attribute_name):
        attribute = getattr(obj.__class__, attribute_name)
        if callable(attribute) or isinstance(attribute, property):
            return True
    if hasattr(obj.__class__, attribute_name) and attribute_name not in obj.__dict__:
        return True
    if hasattr(obj, attribute_name):
        attribute = getattr(obj, attribute_name)
        if callable(attribute) or isinstance(attribute, property):
            return True
    return False


def py_object_to_json_object(source_object: PyObjectLike, json_object: dict,
                             additional_filter=None, disable_default_filter=False):
    """
    Convert a python object to JSON object.

    :param source_object: source python object
    :param json_object: target JSON object where fields would be dumped into
    :param additional_filter: an attribute filter that works on name of the attributes
    :param disable_default_filter: whether to disable the default filter
    """
    for attribute_name in dir(source_object):
        # if attribute.startswith('__') or attribute == 'dict':  # ignore magic methods
        #     continue

        # now a custom filter does the check of whether an attribute should be
        # serialised as well, in addition to a default filter
        if not disable_default_filter and default_serialisation_filter(source_object, attribute_name):
            continue
        if additional_filter is not None and additional_filter(source_object, attribute_name):
            continue
        attribute = getattr(source_object, attribute_name)

        if isinstance(attribute, PyObjectLike):
            new_dict = {}
            py_object_to_json_object(attribute, new_dict)
            json_object[attribute_name] = new_dict
        elif isinstance(attribute, (list, set, frozenset)):
            new_list = []
            py_list_to_json_list(attribute, new_list)
            json_object[attribute_name] = new_list
        else:
            json_object[attribute_name] = attribute


class JsonFileAsPyObject(PyObjectLike):
    """
    This mix-in delegates JSON fields to python object fields, making it
    easier to read configuration and to modify them.
    """

    def __init__(self, source: str):
        """
        Load from a JSON file and synchronise its content.

        :param source: JSON file name.
        """
        super().__init__()

        with open(str(source), encoding='utf-8') as source_json:
            json_dict = json.load(source_json)
        json_object_to_py_object(json_dict, self)
        self.__json_source = source

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        new_dict = {}
        py_object_to_json_object(self, new_dict)
        with open(self.__json_source, mode='wt', encoding='utf-8') as output:
            json.dump(output, new_dict)
            return False

    def save(self):
        return self


class YamlFileAsPyObject(PyObjectLike):
    """
    This class delegates YAML fields to a python object for easier
    access and modification.
    """

    def __init__(self, source: str):
        """
        Load a YAML file and synchronise its content.

        :param source: Path to the target file.
        """
        super().__init__()

        with open(str(source), mode='rt', encoding='utf-8') as source_fd:
            yaml_dict = yaml.safe_load(source_fd)
        json_object_to_py_object(yaml_dict, self)
        self.__yaml_source = source

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        new_yaml_dict = {}
        py_object_to_json_object(self, new_yaml_dict)
        with open(self.__yaml_source, mode='wt', encoding='utf-8') as dump_fd:
            yaml.safe_dump(new_yaml_dict, dump_fd, default_flow_style=False)
        return False

    def save(self):
        """
        A more sensible shorthand to the saving context.
        Modifications are saved to disk immediately after leaving the context.

        :return: The config object itself.
        """
        return self
