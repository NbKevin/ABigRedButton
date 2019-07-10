"""
This script offers utilities for synchronisation issue.

Bin Ni. kevin.ni@nyu.edu.
"""


def thread_safe(lock):
    """
    Make a function thread safe. This is done by ensuring that the function is
    non-reentrant. A lock or a similar object must be provided, with an "acquire"
    and a "release" function.

    :param lock: a lock or lock like object
    :return: partially initialised wrapper
    """

    def wrapper(wrapped_function):
        """
        Partial wrapper that is aware of the lock object provided.

        :param wrapped_function: the function to be wrapped and made thread safe
        :return: the actual thread safe function wrapper
        """

        def thread_safe_function(*args, **kwargs):
            """
            The actual thread safe wrapper of the original function.

            :return: whatever the original function returns
            """
            with lock:
                return wrapped_function(*args, **kwargs)

        return thread_safe_function

    return wrapper
