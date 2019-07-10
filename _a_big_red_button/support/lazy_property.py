"""
Implements a lazy property that only evaluates upon
its first access.

Kevin Ni, kevin.ni@nyu.edu.
"""

from typing import TypeVar, Callable, Any


# noinspection PyPep8Naming
class lazy_property:
    """
    Implemented as a get only data descriptor such that all access apart
    from the first falls directly into the attributes itself, saving a
    function call.
    """
    # type variable
    T = TypeVar('T')

    def __init__(self, function: Callable[[Any], T],
                 name: str = None, doc: str = None):
        self.function = function
        self.__name__, self.__doc__ = \
            name or function.__name__, doc or function.__doc__

    def __get__(self, instance, owner) -> T:
        if instance is None:
            raise AttributeError('cannot extract attribute on None object')

        value = instance.__dict__.get(self.__name__, self)
        if value is self:
            value = self.function(instance)
            instance.__dict__[self.__name__] = value
        return value
