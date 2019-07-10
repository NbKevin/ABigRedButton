"""
This file loads and initiates the flask application.
Do not run this script directly unless you know what you are doing.
Otherwise always run "run.py".

Kevin Ni, kevin.ni@nyu.edu.
"""

from flask import Flask
from _a_big_red_button.support.configuration import BOOT_CFG
from _a_big_red_button.crawler._original_crawler_script import WoKSpider

# main application
app = Flask(BOOT_CFG.flask.application_name)
