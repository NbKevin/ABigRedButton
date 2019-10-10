"""
This script implements a simple console synchronisation mechanism
that synchronises standard output and standard error streams to
a given client.

Kevin Ni, kevin.ni@nyu.edu.
"""

from queue import Queue, Empty
from threading import Lock, Thread
from typing import List
from flask import Flask, jsonify
from logging import LogRecord
from _a_big_red_button.support.log import BufferedHandler
from _a_big_red_button.support.response import *


# create the buffered handler
CONSOLE_SYNC_HANDLER = BufferedHandler(1000)


# class LogCollectingThread(Thread):
#     def __init__(self):
#         super().__init__()
#         self.mutex = Lock()
#         self.buffer = []
#
#     def run(self) -> None:
#         while True:
#             try:
#                 record = CONSOLE_SYNC_HANDLER.queue.get(block=True, timeout=5)
#             except Empty:
#                 # simply means no available logs at the moment
#                 # print("no record read in 5 seconds")
#                 pass
#             else:
#                 self.mutex.acquire()
#                 self.buffer.append(record)
#                 self.mutex.release()
#                 # print("dequeued log record")
#
#
# __COLLECTING_THREAD = LogCollectingThread()


def extract_logs():
    return good(new_logs=list(record.getMessage() for record in CONSOLE_SYNC_HANDLER.extract_all()))


def register_console_sync(app: Flask):
    # __COLLECTING_THREAD.start()
    app.route('/poll/log/')(extract_logs)
