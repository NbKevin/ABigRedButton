"""
This is the log module which prepares logging service and
offer it to various other components.

Bin Ni. bn628@nyu.edu.
"""

import logging
import logging.handlers
import os
from threading import RLock
from _a_big_red_button.support.configuration import BOOT_CFG, get_logger_config
from _a_big_red_button.support.synchronisation import thread_safe
from _a_big_red_button.support.directory import DEPLOYMENT_ROOT


# records known loggers
__KNOWN_LOGGERS = {}

# load base logger configuration
__BASE_CFG = get_logger_config('__base')

# logging level for this session
__LOGGING_LEVEL = __BASE_CFG.level.debug if BOOT_CFG.flask.debug else __BASE_CFG.level.release

# formatter
__FORMATTER = logging.Formatter(__BASE_CFG.formatter)

# whether to ignore all handlers other than the std.err one
__IGNORE_NON_STD_ERR_HANDLER = BOOT_CFG.flask.debug and __BASE_CFG.ignore_non_std_err_handler

# mutex protecting the known logger lists
__mutex = RLock()


@thread_safe(__mutex)
def get_logger(identifier: str) -> logging.Logger:
    """
    Get a properly set up, ready-to-go logger associated with the given identifier.
    
    :param identifier: The identifier.
    :return: The logger associated with it.
    """
    # first check if this identifier is known
    if identifier in __KNOWN_LOGGERS:
        return __KNOWN_LOGGERS[identifier]

    # otherwise create a new one
    # first load the formatter and configuration
    logger = logging.getLogger(identifier)
    try:
        config = get_logger_config(identifier)
    except FileNotFoundError:
        raise FileNotFoundError('Could not find configuration file for logger <%s>' %
                                identifier) from None

    # change working directory so that log files go where they are assigned
    old_working_dir = os.getcwd()
    os.chdir(str(DEPLOYMENT_ROOT.joinpath(__BASE_CFG.directory)))

    for handler_config in config.handlers:
        if __IGNORE_NON_STD_ERR_HANDLER:
            if handler_config.type != 'StreamHandler' or handler_config.arguments.stream is not None:
                continue

        if hasattr(logging, handler_config.type):
            handler = getattr(logging, handler_config.type)(**handler_config.arguments.dict)
        elif hasattr(logging.handlers, handler_config.type):
            handler = getattr(logging.handlers, handler_config.type)(**handler_config.arguments.dict)
        else:
            raise TypeError("Could not find handler type <%s> for logger <%s>" %
                            (handler_config.type, identifier))

        handler.setFormatter(__FORMATTER if not hasattr(handler_config, 'formatter') else
                             logging.Formatter(getattr(handler_config, 'formatter')))
        logger.setLevel(__LOGGING_LEVEL)
        logger.addHandler(handler)

    # restore working directory in prevention of confusion
    os.chdir(old_working_dir)

    # log some test output
    __test_log(logger)

    __KNOWN_LOGGERS[identifier] = logger
    return logger


def __test_log(logger: logging.Logger):
    """
    Log some test content to make sure that the logger works properly.

    :param logger: Target logger.
    """
    if __IGNORE_NON_STD_ERR_HANDLER:
        logger.warning('Running under debug mode, ignoring any '
                       'handler not targeting standard error stream...')
    logger.debug('Logger up and ready')
