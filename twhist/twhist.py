import re
import requests
import random
import urllib
import time
import datetime as dt
from datetime import timedelta
from datetime import timedelta
from bs4 import BeautifulSoup
from billiard.pool import Pool
from itertools import cycle

#constant variables
proxy_url = "https://free-proxy-list.net/"
HEADERS_LIST = [
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; x64; fr; rv:1.9.2.13) Gecko/20101203 Firebird/3.6.13',
    'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
    'Mozilla/5.0 (Windows NT 5.2; RW; rv:7.0a1) Gecko/20091211 SeaMonkey/9.23a1pre'
]
INIT_URL = 'https://twitter.com/i/search/timeline?f=tweets&vertical=' \
             'default&include_available_features=1&include_entities=1&' \
             'reset_error_state=false&src=typd&max_position=-1&q={q}&l={lang}'
RELOAD_URL = 'https://twitter.com/i/search/timeline?f=tweets&vertical=' \
             'default&include_available_features=1&include_entities=1&' \
             'reset_error_state=false&src=typd&max_position={pos}&q={q}&l={lang}'

wait_start = (0.1,0.25)
wait_between = (1,5)
wait_proxy_change = (5,7.5)

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

        self.search_duration = ""
        self.all_tweets = 0
        self.all_tweets_unique = 0

        self.proxy_list = get_proxies()

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

    def start_query(self):
        """

        """
        results = []
        queries_proxies = list(self.build_queries_proxies())
        pool = Pool(len(queries_proxies))
        start_time = dt.datetime.now()
        try:
            ids = []
            for result in pool.imap(self.query_tweets, queries_proxies):
                results.append(result)
                self.all_tweets += len(result["results"])
                ids.extend([x["tweet_id"] for x in result["results"]])
        except KeyboardInterrupt:
            print("interrupted by user")
        pool.close()
        pool.join()
        self.all_tweets_unique = len(set(ids))
        end_time = dt.datetime.now()
        self.search_duration = end_time - start_time
        return results


    def build_queries_proxies(self):
        """

        """
        day_list = []
        queries = []
        #fill day_list
        delta = self.until - self.since
        for i in range(delta.days):
            period = (self.since + timedelta(days=i), self.since + timedelta(days=i+1))
            day_list.append(period)

        #create queries plus proxy pools for each day
        x = len(self.proxy_list) // len(day_list)
        query_setup = self.query.replace(' ', '%20').replace('#', '%23').replace(':', '%3A').replace('&', '%26')
        for i, day in enumerate(day_list):  
            query = f"{query_setup} since:{day[0]} until:{day[1]}"        
            if i == 0:
                yield (query, self.proxy_list[:x])
            else:
                yield (query, self.proxy_list[x*i:x*(i+1)])

    def query_tweets(self, params):
        """

        """
        start_time = dt.datetime.now()
        proxy_counter = 1
        query = params[0]
        searching = True

        string = query.split()[1]
        start = string.find(":")+1
        date1_string = string[start:]
        date1 = dt.datetime.strptime(date1_string, "%Y-%m-%d").date()-timedelta(days=1)

        #first search to get min_id and max_id    
        initial_tweets = []
        proxy_pool = cycle(params[1])
        proxy = next(proxy_pool)
        header = {'User-Agent': random.choice(HEADERS_LIST), 'X-Requested-With': 'XMLHttpRequest'}
        url = self.build_url(query, None)

        data = {"query":query, "header":header, "proxy(s)":proxy_counter, "search_duration": "", "end_message": "Nichts",
                "wait_start": wait_start, "wait_between": wait_between, "wait_proxy_change": wait_proxy_change,
                "last_result": "", "results":[]}

        print(data["query"])
        time.sleep(random.uniform(wait_start[0], wait_start[1]))

        #try:
        response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=60)
        if response:
            html = response.json().get("items_html")
            if html:
                soup = BeautifulSoup(html, "lxml")
                tweets = soup.find_all("li", "js-stream-item")
                if len(tweets) > 0:
                    for tweet in tweets:
                        dic = tweet_dic(tweet)
                        initial_tweets.append(dic)
                    pos = f"TWEET-{initial_tweets[-1]['tweet_id']}-{initial_tweets[0]['tweet_id']}"
                else:
                    print("got 0 tweets in first search--weird query?")
                    return data
            else:
                print("got no html")
                return data
        else:
            print("got no response")
            return data
        #except:
            #print("something with the first search went wrong")
            #print(data)
            #return data

        #continous search
        if (self.limit > 0) and searching:
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
                                dic = tweet_dic(tweet)
                                if dic:
                                    date2 = dt.datetime.strptime(dic["timestamp"], "%Y-%m-%d %H:%M:%S").date()
                                    if date1 == date2:
                                        data["end_message"] = "reached_next_date"
                                        searching = False
                                        break
                                    data["results"].append(dic)
                            if response.json()["has_more_items"]:
                                pos = urllib.parse.quote(response.json()["min_position"])
                                time.sleep(random.uniform(wait_between[0], wait_between[1]))
                            else:
                                """
                                print("['has_more_items'] = False")
                                data["end_message"] = "['has_more_items'] = False"
                                break
                                """
                                pos = urllib.parse.quote(response.json()["min_position"])
                                data["proxy(s)"] += 1
                                proxy = next(proxy_pool)
                                header = {'User-Agent': random.choice(HEADERS_LIST), 'X-Requested-With': 'XMLHttpRequest'}
                                print("changing proxy..")
                                print(len(data["results"]), "tweets before proxy change", query)
                                time.sleep(random.uniform(wait_proxy_change[0], wait_proxy_change[1]))
                        else:
                            print("got 0 tweets")
                            data["end_message"] = "got 0 tweets"
                            break
                    else:
                        print("got no html", response.json())
                        data["end_message"] = response.json()
                        break
                else:
                    print("got no response.json", response)
                    data["end_message"] = "got no response.json"
                    break
            if data["end_message"] == "Nichts":
                data["end_message"] = "reached limit"
        else:
            while searching:
                url = self.build_url(query, pos)
                response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=60)
                if response.json():
                    html = response.json().get("items_html")
                    if html:
                        soup = BeautifulSoup(html, "lxml")
                        tweets = soup.find_all("li", "js-stream-item")
                        if len(tweets) > 0:
                            for tweet in tweets:
                                dic = tweet_dic(tweet)
                                if dic:
                                    date2 = dt.datetime.strptime(dic["timestamp"], "%Y-%m-%d %H:%M:%S").date()
                                    if date1 == date2:
                                        data["end_message"] = "reached_next_date"
                                        searching = False
                                        break
                                    data["results"].append(dic)
                            if response.json()["has_more_items"]:
                                pos = urllib.parse.quote(response.json()["min_position"])
                                time.sleep(random.uniform(wait_between[0], wait_between[1]))
                            else:
                                """
                                print("['has_more_items'] = False")
                                data["end_message"] = "['has_more_items'] = False"
                                break
                                """
                                pos = urllib.parse.quote(response.json()["min_position"])
                                data["proxy(s)"] += 1
                                proxy = next(proxy_pool)
                                header = {'User-Agent': random.choice(HEADERS_LIST), 'X-Requested-With': 'XMLHttpRequest'}
                                print("changing proxy..")
                                print(len(data["results"]), "tweets before proxy change", query)
                                time.sleep(random.uniform(wait_proxy_change[0], wait_proxy_change[1]))
                        else:
                            print("got 0 tweets")
                            data["end_message"] = "got 0 tweets"
                            break
                    else:
                        print("got no html", response.json())
                        data["end_message"] = response.json()
                        break
                else:
                    print("got no response.json", response)
                    data["end_message"] = "got no response.json"
                    break

        print(len(data["results"]))
        end_time = dt.datetime.now()
        data["search_duration"] = str(end_time - start_time)
        if len(data["results"]) > 0:
            data["last_result"] = data["results"][-1].get("timestamp")
        return data

    def build_url(self, query, pos):
        """

        """
        if pos is None:
            return INIT_URL.format(q=query, lang="")
        else:
            return RELOAD_URL.format(q=query, pos=pos, lang="")

def get_proxies():
    """

    """
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

def tweet_dic(tweet):
    """

    """
    dic = {"screen_name" : "", "username" : "", "user_id" : "", "tweet_id" : "", "tweet_url" : "", "timestamp" : "", "timestamp_epochs" : "", "text" : "", 
    "text_html" : "", "links" : "", "hashtags" : "", "has_media" : "", "img_urls" : "", "video_url" : "", "likes" : "", "retweets" : "", "replies" : "",
    "is_reply_to" : "", "parent_tweet_id" : "", "reply_to_users" : ""
    }

    try:
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
    except:
        print(tweet)
        return None
    