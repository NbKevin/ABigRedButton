"""
This scripts implements a bridge between the selenium web drivers
and the crawler.

Kevin Ni, kevin.ni@nyu.edu.
"""

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys


class SeleniumHeadless:
    @staticmethod
    def make_new_firefox():
        return SeleniumHeadless(webdriver.Firefox())

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get(self, path: str):
        return self.driver.get(path)

    def __getattr__(self, item):
        return getattr(self.driver, item)
