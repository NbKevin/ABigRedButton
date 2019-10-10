"""
Implements analyser functions for Social Network Analysis.

Kevin Ni, kevin.ni@nyu.edu.
"""

import json
from pathlib import Path
from typing import *
import subprocess
import sys
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.support.singleton import Singleton
from _a_big_red_button.support.directory import DEPLOYMENT_ROOT

# prepare the logger
logger = get_logger('analyser')


class WokAnalyser(metaclass=Singleton):
    def __init__(self):
        self.file: Optional[Path] = None

    def select_file(self):
        # show a file selection dialogue
        completed_process = subprocess.run(
            [sys.executable, "-m",
             "_a_big_red_button.support.select_file"],
            cwd=DEPLOYMENT_ROOT, capture_output=True)
        if completed_process.returncode != 0:
            logger.error(f"cannot select file: error code "
                         f"{completed_process.returncode}")
            return False
        output = completed_process.stdout.decode()
        if not output:
            logger.error(f"cannot select file: unknown error")
            return False
        if output[0] == 'E':
            logger.error(f"cannot select file: {output[2:]}")
            return False
        elif output[0] == 'S':
            self.file = Path(output[2:])
            logger.info(f"selected file: {self.file}")
            return True
        else:
            logger.error(f"cannot select file: {output[2:]}")
            return False

    def analyse(self):
        assert self.file is not None
        binary = json.load(self.file)['data']
        try:
            logger.info("read ")
        except:
            pass


class SNACrawlerOutput:
    def __init__(self, file: Union[str, Path]):
        self.file = file if isinstance(file, Path) else Path(file)
        self.data: Optional[Dict[str, Union[str, int, float, List[str]]]] = None
        self.validate_output()

    def validate_output(self):
        if not self.file.name.lower().endswith('.epz'):
            logger.warning(f"not analysing an EPZ file, "
                           f"unexpected errors may occur")
        with open(self.file, mode='r', encoding='utf-8') as file:
            raw_file: dict = json.load(file)
            self.data = raw_file['data']

    def generate_gephi_data(self, field: str):
        assert self.data is not None
        d = {}
        for entry in self.data:
            entry: dict
            if 'cauthor' not in entry:
                pass
            processed_authors = list(map(lambda e: e[:-1].split('(')[-1], entry['author']))
            first_author, other_authors = processed_authors[0], processed_authors[1:]
            if first_author not in d:
                d[first_author] = {}
            for other_author in other_authors:
                if other_author not in d[first_author]:
                    d[first_author][other_author] = 0
                d[first_author][other_author] += 1
        return d

    def export_for_gephi(self, dest: Union[str, Path]):
        dest = dest if isinstance(dest, Path) else Path(dest)
        with open(dest, mode='w', encoding='utf-8') as file:
            file.write(self.generate_gephi_data('p'))


def analyse_sna_crawler_output():
    logger.debug(f"analysing file: {0}")


if __name__ == '__main__':
    d = SNACrawlerOutput('Y:/TEST.json').generate_gephi_data('EVE')
    with open("Y:/TEST.csv", mode='w', encoding='utf-8') as file:
        file.write('Source; Target; Weight\n')
        for man, mates in d.items():
            for mate, count in mates.items():
                # if mate not in d:
                #     continue
                file.write(f'{man}; {mate}; {count}\n')
