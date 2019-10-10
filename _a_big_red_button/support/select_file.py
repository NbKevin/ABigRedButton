"""
This script simply asks for a file as input, then print
the result into stdout. It is meant to be used in corporation
with multithreaded application where Tkinter does not work
properly most of the time.

Kevin Ni, kevin.ni@nyu.edu.
"""

import tkinter
from tkinter.filedialog import asksaveasfilename
from pathlib import Path
import subprocess
import sys


def select_file(title, *file_types):
    # we do the import here because we don't want the initialisation
    # output to scramble with the output
    from _a_big_red_button.support.directory import DEPLOYMENT_ROOT
    from _a_big_red_button.support.log import get_logger

    # prepare logger
    logger = get_logger('export')

    # assemble select arguments and run the selecting script
    completed_process = subprocess.run(
        [sys.executable, "-m",
         "_a_big_red_button.support.select_file",
         title, *[item for file_type in file_types for item in file_type]],
        cwd=DEPLOYMENT_ROOT, capture_output=True)

    # parse the result
    if completed_process.returncode != 0:
        logger.error(f"cannot select file: error code "
                     f"{completed_process.returncode}")
        return None

    # parse the return code
    output = completed_process.stdout.decode()
    if not output:
        logger.error(f"cannot select file: unknown error")
        return None
    if output[0] == 'E':
        logger.error(f"cannot select file: {output[2:]}")
        return None
    elif output[0] == 'S':
        file = Path(output[2:].strip())
        logger.info(f"selected file: {file}")
        return file
    else:
        logger.error(f"cannot select file: unrecognised output: {output[2:]}")
        return None


if __name__ == '__main__':
    # parse arguments
    source_arguments = sys.argv[1:]
    if not source_arguments or len(source_arguments) < 3:
        print(f"E;invalid selecting argument: {sys.argv}")
        exit()
    title, file_types = source_arguments[0], source_arguments[1:]
    if len(file_types) % 2 != 0:
        print(f"E;invalid file types, must be pairs of description and extension name")
        exit()

    root = tkinter.Tk()
    root.withdraw()

    # configure dialogue options

    options = {
        'title': title,
        'filetypes': list(zip(*(iter(file_types),) * 2)),
        'defaultextension': file_types[0][1]
    }

    try:
        file_name = asksaveasfilename(**options)
    except Exception as e:
        print(f"E;{e}")
    else:
        if not file_name:
            print(f"E;invalid file name or user did not select")
        else:
            print(f"S;{file_name}")
