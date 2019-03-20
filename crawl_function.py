from download_version_x import download_v1_2
import urllib.parse  #解析url的模块
import urllib.robotparser as robotparser
import datetime
import time
import lxml.html
import csv
import re


class Throttle:
    def __init__(self, delay):
        self.delay = delay
        self.domains = {}  # 储存域名和其上次下载的时间

    def wait(self, url):
        domain = urllib.parse.urlparse(url).netloc  # netloc 域名，分析域名
        last_accessed = self.domains.get(domain)    # 读出上次访问时间

        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay-(datetime.datetime.now()-last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)  # 不满速速度，等待
        self.domains[domain] = datetime.datetime.now()  # 更新(记录)该域名的访问时间


def get_robots(url):
    rp = robotparser.RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp


def get_links(html):
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    return webpage_regex.findall(html.decode('utf-8'))

def normalize(seed_url, link):
    link, _ = urllib.parse.urldefrag(link)
    return urllib.parse.urljoin(seed_url, link)


def same_domain(url1, url2):
    return urllib.parse.urlparse(url1).netloc == urllib.parse.urlparse(url2).netloc


class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('countries.csv', 'w'))
        self.fields = ('area', 'population', 'iso', 'country', 'capital', 'continent',
                       'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format',
                       'postal_code_regex', 'languages', 'neighbours')
        self.writer.writerow(self.fields)

    def __call__(self, url, html):
        if re.search('/view/', url):
            tree = lxml.html.fromstring(html)
            row = []
            for field in self.fields:
                row.append(tree.cssselect('table > tr#places_{}__row > td.w2p_fw'.format(field))[0].text_content())
            self.writer.writerow(row)


def download(url, headers, proxy=None, num_retries=1, data=None):
    print('Downloading:', url)
    request = urllib.request.Request(url, data, headers)
    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urllib.parse.urlparse(url).scheme: proxy}
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











