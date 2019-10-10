"""
This module implements a wrapper on top of the export script interface
and allows for a convenient asynchronous call to the export scripts.

Kevin Ni, kevin.ni@nyu.edu.
"""

import threading
from _a_big_red_button.crawler.export_script_helper import *
from _a_big_red_button.support.log import get_logger

# prepare logger
logger = get_logger('export')


class WokPersistentSessionExportScriptThreadedRunner(threading.Thread):
    def __init__(self,
                 export_script: WokPersistentSessionExportScript,
                 session: WokPersistentSession,
                 file: Path):
        super().__init__()

        self.__lock = threading.Lock()
        self.__finished = False
        self.export_script = export_script
        self.session = session
        self.export_file = file
        logger.debug(f'initialised {self}')

    @property
    def finished(self):
        with self.__lock:
            return self.__finished

    def __str__(self):
        return f'WokPersistentSessionExportScriptThreadedRunner(' \
               f'session={self.session}, export_script={self.export_script}, ' \
               f'to_file={self.export_file})'

    def run(self):
        export_helper = WokPersistentSessionExportHelper(
            self.session, self.export_file)
        self.export_script.run(export_helper)

        with self.__lock:
            self.__finished = True

        logger.info(f'finished {self}')
