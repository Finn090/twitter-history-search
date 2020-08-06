import re
import requests
import random
import urllib
import time
import datetime as dt
from datetime import timedelta
from itertools import cycle
from bs4 import BeautifulSoup
from billiard.pool import Pool
from functools import partial

#constant variables
proxy_url = "https://free-proxy-list.net/"
HEADERS_LIST = [
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; x64; fr; rv:1.9.2.13) Gecko/20101203 Firebird/3.6.13',
    'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
    'Mozilla/5.0 (Windows NT 5.2; RW; rv:7.0a1) Gecko/20091211 SeaMonkey/9.23a1pre'
]
INIT_URL = 'https://twitter.com/search?f=tweets&vertical=default&q={q}&l={lang}'
RELOAD_URL = 'https://twitter.com/i/search/timeline?f=tweets&vertical=' \
             'default&include_available_features=1&include_entities=1&' \
             'reset_error_state=false&src=typd&max_position={pos}&q={q}&l={lang}'

class Twhist():
    """

    """
    def __init__(self, query:str, since:str, until:str, limit:int=0):
        """

        """
        self.query = query
        for day in (since, until):
            if type(day) != dt.date:
                self.since = self.valid_date(since)
                self.until = self.valid_date(until)
            else:
                self.since = since
                self.until = until
        if limit:
            self.limit = int(limit)
        else:
            self.limit = 0

        self.error = False
        self.error_message = ""

        self.proxy_list = self.get_proxies()
        self.proxy_pool = cycle(self.proxy_list)
        self.used = []

    def valid_date(self, d):
        """

        """
        try:
            date = dt.datetime.strptime(d, "%Y-%m-%d").date()
            return date
        except ValueError:
            self.error = True
            self.error_message = f"Not a valid date: {d}."
            return None

    def get_proxies(self):
        """

        """
        try:
            response = requests.get(proxy_url)
            soup = BeautifulSoup(response.text, 'lxml')
            table = soup.find('table',id='proxylisttable')
            list_tr = table.find_all('tr')
            list_td = [elem.find_all('td') for elem in list_tr]
            list_td = list(filter(None, list_td))
            list_ip = [elem[0].text for elem in list_td]
            list_ports = [elem[1].text for elem in list_td]
            list_proxies = [':'.join(elem) for elem in list(zip(list_ip, list_ports))]            
            return list_proxies

        except:
            self.error = True
            self.error_message = "Something went wrong while getting the list of proxies"
            return None

    def choose_proxy(self):
        """

        """
        print(self.used)
        proxy = next(self.proxy_pool)
        #if len(used) == len(self.proxy_list):
            #used = []
        while proxy in self.used:
            proxy = next(self.proxy_pool)
        self.used.append(proxy)
        print(self.used)
        return proxy

    def build_queries(self):
        """

        """
        day_list = []
        queries = []
        #fill day_list
        delta = self.until - self.since
        for i in range(delta.days):
            period = (self.since + timedelta(days=i), self.since + timedelta(days=i+1))
            day_list.append(period)
        #fill queries
        for day in day_list:
            query = self.query.replace(' ', '%20').replace('#', '%23').replace(':', '%3A').replace('&', '%26')
            queries.append(f"{query} since:{day[0]} until:{day[1]}")
        return queries

    def build_url(self, query, pos):
        """

        """
        if pos is None:
            return INIT_URL.format(q=query, lang="")
        else:
            return RELOAD_URL.format(q=query, pos=pos, lang="")

    def start_query(self):
        """

        """
        results = []
        queries = self.build_queries()
        pool = Pool(len(queries))
        print(dt.datetime.now())
        try:
            for result in pool.imap_unordered(partial(self.query_tweets), queries):
                results.append(result)
                print(len(result["results"]))
        except KeyboardInterrupt:
            print("interrupted by user")
        pool.close()
        pool.join()
        print(dt.datetime.now())
        print(self.used)
        return results

    def query_tweets(self, query):
        """

        """
        #first search to get min_id and max_id
        time.sleep(random.uniform(0,0.5))
        initial_tweets = []
        header = {'User-Agent': random.choice(HEADERS_LIST), 'X-Requested-With': 'XMLHttpRequest'}
        proxy = self.choose_proxy()
        url = self.build_url(query, None)
        data = {"time":str(dt.datetime.now()), "query":query, "header":header, "proxy":proxy, "results":[]}
        print(data["query"], data["proxy"])

        #try:
        response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=60)
        html = response.text
        soup = BeautifulSoup(html, "lxml")
        tweets = soup.find_all("li", "js-stream-item")
        if len(tweets) > 0:
            for tweet in tweets:
                dic = self.tweet_dic(tweet)
                initial_tweets.append(dic)
            pos = f"TWEET-{initial_tweets[-1]['tweet_id']}-{initial_tweets[0]['tweet_id']}"
        else:
            print("got 0 tweets in first search--weird query?")
            return data
        #except:
            #print(data)
            #return data

        #continous search
        if self.limit > 0:
            for i in range(self.limit//20):
                url = self.build_url(query, pos)
                response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=60)
                if response.json():
                    html = response.json().get("items_html")
                    if html:
                        soup = BeautifulSoup(html, "lxml")
                        tweets = soup.find_all("li", "js-stream-item")
                        if len(tweets) > 0:
                            for tweet in tweets:
                                dic = self.tweet_dic(tweet)
                                data["results"].append(dic)
                            if response.json()["has_more_items"]:
                                pos = urllib.parse.quote(response.json()["min_position"])
                                time.sleep(random.uniform(0.5,1.25))
                            else:
                                print("Twitter said: no more items")
                                break
                        else:
                            print("got 0 tweets")
                            break
                    else:
                        print("got no html", response.json())
                        break
                else:
                    print("got no response.json", response)
                    break
        else:
            while True:
                url = self.build_url(query, pos)
                response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=60)
                if response.json():
                    html = response.json().get("items_html")
                    if html:
                        soup = BeautifulSoup(html, "lxml")
                        tweets = soup.find_all("li", "js-stream-item")
                        if len(tweets) > 0:
                            for tweet in tweets:
                                dic = self.tweet_dic(tweet)
                                data["results"].append(dic)
                            if response.json()["has_more_items"]:
                                pos = urllib.parse.quote(response.json()["min_position"])
                                time.sleep(random.uniform(0.5,1.25))
                            else:
                                print("Twitter said: no more items")
                                break
                        else:
                            print("got 0 tweets")
                            break
                    else:
                        print("got no html", response.json())
                        break
                else:
                    print("got no response.json", response)
                    break
        return data

    def tweet_dic(self, tweet):
        """

        """
        dic = {"screen_name" : "", "username" : "", "user_id" : "", "tweet_id" : "", "tweet_url" : "", "timestamp" : "", "timestamp_epochs" : "", "text" : "", 
        "text_html" : "", "links" : "", "hashtags" : "", "has_media" : "", "img_urls" : "", "video_url" : "", "likes" : "", "retweets" : "", "replies" : "",
        "is_reply_to" : "", "parent_tweet_id" : "", "reply_to_users" : ""
        }

        tweet_div = tweet.find('div', 'tweet')

        dic["screen_name"] = tweet_div["data-screen-name"].strip('@')
        dic["username"] = tweet_div["data-name"]
        dic["user_id"] = tweet_div["data-user-id"]  
        dic["tweet_id"] = tweet_div["data-tweet-id"]
        dic["tweet_url"] = tweet_div["data-permalink-path"]

        timestamp_epochs = int(tweet.find('span', '_timestamp')['data-time'])
        timestamp = dt.datetime.utcfromtimestamp(timestamp_epochs)
        dic["timestamp"] = str(timestamp)
        dic["timestamp_epochs"] = timestamp_epochs 

        soup_html = tweet_div.find('div', 'js-tweet-text-container').find('p', 'tweet-text')
        text = soup_html.text or ""
        dic["text"] = soup_html.text or None
        dic["text_html"] = str(soup_html) or None
        dic["links"] = [atag.get('data-expanded-url', atag['href']) 
                        for atag in soup_html.find_all('a', class_='twitter-timeline-link')
                        if 'pic.twitter' not in atag.text]
        dic["hashtags"] = [tag.strip('#') for tag in re.findall(r'#\w+', text)] 

        soup_imgs = tweet_div.find_all('div', 'AdaptiveMedia-photoContainer')
        dic["img_urls"] = [img['data-image-url'] for img in soup_imgs] if soup_imgs else []  

        video_div = tweet_div.find('div', 'PlayableMedia-container')
        dic["video_url"] = ""
        if video_div:
            try:
                video_id = re.search(r"https://pbs.twimg.com/tweet_video_thumb/(.*)\.jpg", str(video_div)).group(1)
                dic["video_url"] = f"https://video.twimg.com/tweet_video/{video_id}.mp4"
            except:
                #print("error scraping the video_url, maybe it is because of a long video: https://github.com/taspinar/twitterscraper/pull/285"
                      #" , tweet_url will be used instead to make finding the video possible")
                dic["video_url"] = tweet_div["data-permalink-path"]
        dic["has_media"] = True if dic["img_urls"] or dic["video_url"] else False
        dic["links"] = list(filter(lambda x: x != dic["video_url"], dic["links"])) 

        action_div = tweet_div.find('div', 'ProfileTweet-actionCountList')
        dic["likes"] = int(action_div.find('span', 'ProfileTweet-action--favorite').find('span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0')
        dic["retweets"] = int(action_div.find('span', 'ProfileTweet-action--retweet').find('span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0')
        dic["replies"] = int(action_div.find('span', 'ProfileTweet-action--reply u-hiddenVisually').find('span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0')

        dic["parent_tweet_id"] = tweet_div['data-conversation-id']
        if dic["tweet_id"] == dic["parent_tweet_id"]:
            dic["is_reply_to"] = False
            dic["parent_tweet_id"] = None
            dic["reply_to_users"] = []
        else:
            dic["is_reply_to"] = True
            soup_reply_to = tweet_div.find('div', 'ReplyingToContextBelowAuthor')
            if soup_reply_to:
                soup_reply_to_users = soup_reply_to.find_all('a')
                dic["reply_to_users"] = [{'screen_name': user.text.strip('@'),'user_id': user['data-user-id']} for user in soup_reply_to_users]
            #else:
                #print("data-conversation-id is different from tweet_id, but something went wrong scraping for the users which was replied to.")

        return dic