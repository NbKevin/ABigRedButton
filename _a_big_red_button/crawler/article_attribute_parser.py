"""
This script implements a series of parsers for the various attributes
of an article as it is represented on a print page.

Kevin Ni, kevin.ni@nyu.edu.
"""


def take_first(function):
    def actual_function(array):
        return function(array[0])

    return actual_function


def as_int(text: str):
    return int(text)


def split_by(delimiter: str = ";"):
    def actual_function(text: str):
        return list(map(lambda t: t.strip(), text.split(delimiter)))
    return actual_function
