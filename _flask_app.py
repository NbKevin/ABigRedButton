"""
This file loads and initiates the flask application.
Do not run this script directly unless you know what you are doing.
Otherwise always run "run.py".

Kevin Ni, kevin.ni@nyu.edu.
"""

from flask import Flask, render_template
from _a_big_red_button.support.configuration import BOOT_CFG
from _a_big_red_button.consolesync import register_console_sync
from _a_big_red_button.crawler import register_crawler_function
import logging

# disable werkzeug logging
log = logging.getLogger('werkzeug')
log.disabled = True

# main application
app = Flask(BOOT_CFG.flask.application_name)

# register console sync
register_console_sync(app)

# register crawler function
register_crawler_function(app)
