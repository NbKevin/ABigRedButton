"""
This is the configuration manager who provides access to externally
configurable settings.

Bin Ni. bn628@nyu.edu.
"""

import os
from _a_big_red_button.support.python_object_bridge import JsonFileAsPyObject, YamlFileAsPyObject
from _a_big_red_button.support.directory import *

# flags indicating the format of configuration files
USING_YAML_FOR_CONFIG_FILE = True
YAML_EXTENSION_NAME = '.yaml'
JSON_EXTENSION_NAME = '.json'
CONFIG_EXTENSION_NAME = YAML_EXTENSION_NAME if USING_YAML_FOR_CONFIG_FILE else JSON_EXTENSION_NAME
ConfigParser = YamlFileAsPyObject if USING_YAML_FOR_CONFIG_FILE else JsonFileAsPyObject

# configuration files are loaded as objects
# boot configuration is essential for virtually everything to go
BOOT_CFG = YamlFileAsPyObject(PROJECT_CONFIG_DIR.joinpath('bootstrap').with_suffix(CONFIG_EXTENSION_NAME))
print(f'[BOOTSTRAPPER] loaded bootstrapper config')

# tells if the instance is running on a local developing environment
# if boot_config.env.use_dev_env_variable is enabled, this would look for
# a environment variable called 'LOQYU_DEV_ENV'
RUNNING_IN_DEV_ENV = \
    os.getenv(BOOT_CFG.env.dev_env_variable_name, None) is not None \
        if BOOT_CFG.env.use_dev_env_variable \
        else os.name == 'nt'
if BOOT_CFG.env.use_dev_env_variable:
    if RUNNING_IN_DEV_ENV:
        print(f'[BOOTSTRAPPER] dev env detected through env variables')
elif RUNNING_IN_DEV_ENV:
    print(f'[BOOTSTRAPPER] dev env detected through OS name (NT)')

# auto detect deployment environment
if BOOT_CFG.flask.auto_detect_deploy_env:
    if not RUNNING_IN_DEV_ENV:
        BOOT_CFG.flask.debug = False
        print(f'[BOOTSTRAPPER] disabled debugging mode on deploy env')


def get_config(config_name: str):
    """
    Get the configuration associated with the given name. Configuration files must
    be places inside the directory defined in "PROJECT_CONFIG_DIR".

    :param config_name: configuration name
    :return: the configuration for it
    """
    return ConfigParser(PROJECT_CONFIG_DIR.joinpath(config_name).with_suffix(CONFIG_EXTENSION_NAME))


def get_logger_config(logger_identifier: str):
    """
    Get the configuration associated with the given logger identifier. Configuration
    files must be placed inside the directory defined in "LOGGER_CONFIG_DIR".

    :param logger_identifier: logger identifier
    :return: the configuration for it
    """
    return ConfigParser(LOGGER_CONFIG_DIR.joinpath(logger_identifier).with_suffix(CONFIG_EXTENSION_NAME))


def get_dispatcher_config(dispatcher_name: str):
    """
    Get the configuration associated with the given dispatcher. Configuration
    files must be placed inside the directory defined in "DISPATCHER_CONFIG_DIR".

    :param dispatcher_name: name of the dispatcher to get the configuration for, no extension needed
    :return: the configuration for it
    """
    return ConfigParser(DISPATCHER_CONFIG_DIR.joinpath(dispatcher_name).with_suffix(CONFIG_EXTENSION_NAME))


def parse_config_from_file(file_name: str):
    """
    Try parsing configuration from a given file.
    Added with the introduction of the versioning helper.

    :param file_name: file name
    :return: the configuration if a matching config parser is found
    """
    if file_name.endswith('.json'):
        return JsonFileAsPyObject(file_name)
    elif file_name.endswith('.yaml'):
        return YamlFileAsPyObject(file_name)
    else:
        raise NotImplementedError('no config parser found for the given file')
