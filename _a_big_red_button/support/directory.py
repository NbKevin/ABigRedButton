"""
This module provides definition of important directories utilising the new "pathlib" introduced in Python 3.4.

Bin Ni. kevin.ni@nyu.edu.
"""

from pathlib import Path

# helper module directory
SUPPORT_DIR = Path(__file__).parent

# deployment directory, aka where all files are placed
DEPLOYMENT_ROOT = SUPPORT_DIR.parent.parent

# template directory
TEMPLATE_DIR = DEPLOYMENT_ROOT.joinpath('templates')

# project configuration directory
PROJECT_CONFIG_DIR = DEPLOYMENT_ROOT.joinpath('project.conf.d')

# dispatcher configuration directory
DISPATCHER_CONFIG_DIR = PROJECT_CONFIG_DIR.joinpath('dispatcher')

# logger configuration directory
LOGGER_CONFIG_DIR = PROJECT_CONFIG_DIR.joinpath('logger')

# patches directory
PATCH_DIR = DEPLOYMENT_ROOT.joinpath('patch')

# static resources directory
STATIC_RES_DIR = DEPLOYMENT_ROOT.joinpath('static')

# kotlin source directory
KOTLIN_SRC_DIR = DEPLOYMENT_ROOT.joinpath('kotlin')
