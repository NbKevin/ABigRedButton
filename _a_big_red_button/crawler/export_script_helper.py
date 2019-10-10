"""
This module implements advisory functions concerning
export scripts, such as listing, creating new, exporting
with a selected script, etc.

Kevin Ni, kevin.ni@nyu.edu.
"""

import os
from pathlib import Path
import importlib
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.support.configuration import get_config
from _a_big_red_button.crawler.export_helper import WokPersistentSessionExportHelper
from _a_big_red_button.crawler.db import WokPersistentSession

# prepare the logger
logger = get_logger('export')

# parse config
config = get_config('export')

# resolve the path to all the export scripts
EXPORT_SCRIPT_DIR: Path = Path(__file__).parent.joinpath('export')


class WokPersistentSessionExportScript:
    def __init__(self, name: str):
        script_full_path = EXPORT_SCRIPT_DIR.joinpath(f'{name}.py')
        if not script_full_path.exists():
            raise RuntimeError(f'the requested export script does not exist: '
                               f'{name} => {script_full_path}')

        self.name = name
        self.qualified_name = f'_a_big_red_button.crawler.export.{name}'
        self.script = importlib.import_module(self.qualified_name)

    def validate_script(self):
        if not hasattr(self.script, 'export'):
            raise RuntimeError(f'invalid export script {self.name}: '
                               f'no export function')

        export_function = self.script.export
        if not callable(export_function):
            raise RuntimeError(f'invalid export script {self.name}: '
                               f'export function is not callable')

        # we leave the inspect of the function signature to run time

    def run(self, session: WokPersistentSessionExportHelper):
        logger.info(f'running export script [{self.name}] for {session}...')
        try:
            self.script.export(session)
        except Exception as e:
            logger.warning(f'failed running export script [{self.name}] for {session}, error detailed as follow:')
            logger.warning(f'{e}')
        else:
            logger.info(f'finished running export script [{self.name}] for {session}')

    def __str__(self):
        return f'WokPersistentSessionExportScript(name={self.name})'


def available_export_scripts(name_only=True):
    logger.info("finding available export scripts...")
    for _, dirs, files in os.walk(str(EXPORT_SCRIPT_DIR)):
        count = 0
        for file in files:
            if not file.endswith('.py'):
                logger.debug(f'skipped file {file}: '
                             f'invalid extension name')
                continue

            file_name = file[:-3]
            if file_name in config.invalid_names:
                logger.debug(f'skipped file {file}: '
                             f'invalid name')
                continue

            if name_only:
                yield file_name
            else:
                yield WokPersistentSessionExportScript(file_name)
            count += 1

        logger.info(f'found {count} export scripts')
        break


def get_export_script(name: str):
    if name in config.invalid_names:
        logger.debug(f'cannot get export script {name}: invalid name')
        return None
    if name not in available_export_scripts(name_only=True):
        logger.debug(f'cannot get export script {name}: does not exist')
        return None
    return WokPersistentSessionExportScript(name)
