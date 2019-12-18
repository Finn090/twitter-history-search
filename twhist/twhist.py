import time
from datetime import datetime, date, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta

import re

from selenium import webdriver
# from selenium.common.exceptions import (
# NoSuchElementException,
# WebDriverException)
from selenium.webdriver.chrome.options import Options


class Twhist():

    def __init__(self, headless=True):
        self.headless = headless
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        self.wd = webdriver.Chrome(options=options)

    def get(self, query: str, start: str, end: str, limit_search=True, intervall='day'):

        start = parser.parse(start).date()
        end = parser.parse(end).date()

        allowed_date_range = timedelta(days=7)

        if intervall == 'day':
            intervall = relativedelta(days=1)
        elif intervall == 'month':
            intervall = relativedelta(months=1)
        elif intervall == 'year':
            intervall = relativedelta(years=1)
        else:
            print('Supported intervalls are: day, month, year')
            return

        if end <= start:
            print ('End date needs to be at least one day after start date.')
            return

        if limit_search and (end-start > allowed_date_range):
            print ('Allowed date range of 7 days exceeded.')
            return

        query_start = start
        
        results = []
        while query_start < end:
            if query_start+intervall < end:
                query_end = query_start+intervall
            else:
                query_end = end

            results.extend(self.call(query, query_start, query_end))
            query_start = query_end
        return results


    
    def call(self, query, query_start, query_end):    

        query = query.replace(' ', '%20')

        search_url = (
            f'https://twitter.com/search?src=typd&q={query}'
            f'%20since%3A{query_start}%20until%3A{query_end}'
        )

        print(search_url)

        self.wd.get(search_url)

        script = (
            'window.scrollTo(0, document.body.scrollHeight);'
            'var lenOfPage=document.body.scrollHeight;'
            'return lenOfPage;'
        )

        lenOfPage = self.wd.execute_script(script)
        match = False
        while not match:
            print('.', end='')
            lastCount = lenOfPage
            time.sleep(3)
            lenOfPage = self.wd.execute_script(script)
            if lastCount == lenOfPage:
                match = True
       
        links = self.wd.find_elements_by_tag_name('a')

        regex = r'https?:\/\/twitter.com\/(\w+)\/status\/(\d+)'

        results = []
        for a in links:
            href = a.get_attribute('href')
            group = None
            match = re.match(regex, str(href))
            if match:
                results.append(match.group(2))
        return results
    
