"""
Implements a modern style, meta class based singleton mechanism.

Kevin Ni, kevin.ni@nyu.edu.
"""


class Singleton(type):
    """
    Implements a fairly simple yet effective singleton scheme.

    To use it, simply declare this class as the meta class of a
    singleton-to-be class.
    """
    instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]
