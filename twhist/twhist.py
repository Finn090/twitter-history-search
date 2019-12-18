import time
# import calendar
# import datetime

from dateutil import parser

import re

from selenium import webdriver
# from selenium.common.exceptions import (
# NoSuchElementException,
# WebDriverException)
from selenium.webdriver.chrome.options import Options


class Twhist():

    def __init__(self, headless=True):
        self.headless = headless

    def get(self, query: str, since: str, until: str):

        regex = r'https?:\/\/twitter.com\/(\w+)\/status\/(\d+)'

        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        wd = webdriver.Chrome(options=options)

        since = str(parser.parse(since).date())
        until = str(parser.parse(until).date())

        query = query.replace(' ', '%20')

        search_url = (
            f'https://twitter.com/search?src=typd&q={query}'
            f'%20since%3A{since}%20until%3A{until}'
        )

        # TODO: limit to 7 days

        # old version from here

        print(search_url)

        wd.get(search_url)

        script = (
            'window.scrollTo(0, document.body.scrollHeight);'
            'var lenOfPage=document.body.scrollHeight;'
            'return lenOfPage;'
        )

        lenOfPage = wd.execute_script(script)
        match = False
        while not match:
            print('.', end='')
            lastCount = lenOfPage
            time.sleep(3)
            lenOfPage = wd.execute_script(script)
            if lastCount == lenOfPage:
                match = True

            links = wd.find_elements_by_tag_name('a')

            with open('ids7.txt', 'a') as f:
                for a in links:
                    href = a.get_attribute('href')

                    group = None
                    match = re.match(regex, str(href))
                    if match:
                        group = match.group(2)
                        print(group)

                        f.write(group + '\n')
