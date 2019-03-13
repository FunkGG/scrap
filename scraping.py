
import urllib.robotparser as robotparser
import re
import urllib.request
import urllib.parse as urlparse
import datetime
import time
from collections import deque


class Throttle:
    def __init__(self, delay):
        self.delay = delay
        self.domains = {}

    def wait(self,url):
        domain = urlparse.urlparse(url).netloc  # netloc 域名
        last_accessed = self.domains.get(domain)

        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay-(datetime.datetime.now()-last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.datetime.now()


def download(url, headers, proxy=None, num_retries=1, data=None):
    print('Downliading:', url)
    request=urllib.request.Request(url, data, headers)
    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urlparse.urlparse(url).scheme: proxy}
        opener.add_handler(urllib.request.ProxyHandler(proxy_params))
    try:
        response = opener.open(request)
        html = response.read()
    except urllib.request.URLError as e:
        print('Download error:',e.reason)
        html = None
        if hasattr(e, 'code'):
            code = e.code
            if num_retries > 0 and 500 <= code < 600:
                return download(url, headers, proxy, num_retries - 1, data)
    return html


def normalize(seed_url, link):
    link, _ = urlparse.urldefrag(link)
    return urlparse.urljoin(seed_url, link)


def same_domain(url1, url2):
    return urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc


def get_robots(url):
    rp = robotparser.RobotFileParser()
    rp.set_url(urlparse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp


def get_links(html):
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    return webpage_regex.findall(html.decode('utf-8'))


def link_crawler(seed_url, link_regex=None, delay=5, num_retries=1, max_depth=-1,
                 max_urls=-1, user_agent='FunkGG', proxy=None, scrape_callback=None):
    crawl_queue = deque([seed_url])
    seen = {seed_url:0}
    num_urls = 0
    rp = get_robots(seed_url)
    throttle = Throttle(delay)
    headers = {}
    if user_agent:
        headers['User_agent'] = user_agent
    while crawl_queue:
        url = crawl_queue.pop()
        if rp.can_fetch(user_agent,url):
            throttle.wait(url)
            html = download(url, headers, proxy=proxy, num_retries=num_retries)
            depth = seen[url]
            links = []
            if scrape_callback:
                links.extend(scrape_callback(url,html) or [])
            if depth != max_depth:
                if link_regex:
                    links.extend(link for link in get_links(html) if re.match(link_regex,link))
            for link in links:
                link = normalize(seed_url, link)#创建绝对链接
                if link not in seen:
                    seen[link] = depth+1
                    if same_domain(seed_url, link):
                        crawl_queue.append(link)
            num_urls +=1
            if num_urls == max_urls:
                break
        else:
            print('Blocked by robots.txt:', url)


if __name__ == '__main__':
    # link_crawler('http://example.webscraping.com', '/places/default/(index|view)',
    #               delay=5, num_retries=1, user_agent='BadCrawler')
    link_crawler('http://example.webscraping.com', '/places/default/(index|view)',
                 delay=5, num_retries=1, max_depth=1, user_agent='GoodCrawler')
