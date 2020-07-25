# Simple Python module for retrieving historic tweets.
# Copyright (C) 2019 Marcus Burkhardt and Jörn Preuß
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time
# import pandas as pd
from datetime import timedelta  # datetime, date,
from dateutil import parser
from dateutil.relativedelta import relativedelta
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from chromedriver_py import binary_path

class Twhist():

    def __init__(self, headless=True):
        self.headless = headless
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        self.wd = webdriver.Chrome(executable_path=binary_path, options=options)
        self.status = []

    def get(
            self, query: str, start: str, end: str,
            limit_search=True, intervall='day',
            csv_download_link: str='result.csv'):

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

        if len(query) == 0:
            print('Please enter a query.')
            return

        if end <= start:
            print('End date needs to be at least one day after start date.')
            return

        if limit_search and (end - start > allowed_date_range):
            print('Allowed date range of 7 days exceeded.')
            return

        query_start = start

        results = []
        while query_start < end:
            if query_start + intervall < end:
                query_end = query_start + intervall
            else:
                query_end = end

            results.extend(self.call(query, query_start, query_end))
            query_start = query_end

        columns = [
            'tid', 'uhandle', 'uid', 'content', 'date',
            'retweets', 'replies', 'favorites', 'hashtags',
            'text_link', 'attached_link']

        # results = pd.DataFrame(results, )

        with open(csv_download_link, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(columns)
            for line in results:
                csvwriter.writerow(line)

        return [columns] + results

    def call(self, query, query_start, query_end):
        query = query.replace(' ', '%20')

        search_url = (
            f'https://twitter.com/search?src=typd&q={query}'
            f'%20since%3A{query_start}%20until%3A{query_end}'
        )

        print('Retrieving: ' + search_url + ' ', end='')
        self.set_status('Retrieving: ' + search_url)

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
            self.set_status('.')
            lastCount = lenOfPage
            time.sleep(3)
            lenOfPage = self.wd.execute_script(script)
            if lastCount == lenOfPage:
                match = True
        print('\n')

        results = []

        soup = BeautifulSoup(self.wd.page_source, 'html.parser')

        for elem in soup.find_all(class_='tweet'):
            tid = elem.get('data-tweet-id')
            uhandle = elem.find(class_='username').text
            uid = elem.get('data-user-id')

            tweet_timestamp = elem.find(class_='tweet-timestamp')
            if tweet_timestamp.get('data-original-title'):
                date = tweet_timestamp.get('data-original-title')
            elif tweet_timestamp.get('title'):
                date = tweet_timestamp.get('title')
            else:
                date = tweet_timestamp

            if elem.find(class_='js-tweet-text').text:
                content = elem.find(class_='js-tweet-text').text
            else:
                content = ' '.join(str(item) for item in
                                   elem.find(class_='js-tweet-text').contents)

            hashtags = []
            for ht in elem.find_all(class_='twitter-hashtag'):
                hashtags.append(ht.text)

            if elem.find(class_='link'):
                text_link = elem \
                    .find(class_='twitter-timeline-link').get('href')
            else:
                text_link = 'None'

            if elem.find(class_='js-macaw-cards-iframe-container'):
                attached_link = elem \
                    .find(class_='js-macaw-cards-iframe-container') \
                    .get('data-card-url')
            else:
                attached_link = 'None'

            if elem.find(class_='ProfileTweet-action--retweet'):
                retweets = elem \
                    .find(class_='ProfileTweet-action--retweet') \
                    .find(class_='ProfileTweet-actionCount') \
                    .get('data-tweet-stat-count')
            else:
                retweets = 'None'

            if elem.find(class_='ProfileTweet-action--reply'):
                replies = elem \
                    .find(class_='ProfileTweet-action--reply') \
                    .find(class_='ProfileTweet-actionCount') \
                    .get('data-tweet-stat-count')
            else:
                replies = 'None'

            if elem.find(class_='ProfileTweet-action--favorite'):
                favorites = elem \
                    .find(class_='ProfileTweet-action--favorite') \
                    .find(class_='ProfileTweet-actionCount') \
                    .get('data-tweet-stat-count')
            else:
                favorites = 'None'

            results.append(
                [tid, uhandle, uid, content, date, retweets, replies,
                 favorites, hashtags, text_link, attached_link])

        return results

    def get_status(self, reset=True):
        status = self.status
        if reset:
            self.status
        return status

    def set_status(self, message):
        self.status.append(message)
