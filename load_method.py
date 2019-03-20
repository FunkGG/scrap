from download_version_x import download_v1_2
import itertools  # 无限迭代器
import re


def craw_sitemap(url):  # 网站地图爬虫
    sitemap = download_v1_2(url+'/sitemap.xml')
    links = re.findall('<loc>(.*?)</loc>', sitemap.decode('utf-8'))  # 正则表达式
    for link in links:
        download_v1_2(link)


def craw_id(url, max_errors=5):   # ID遍历爬虫
    num_errors = 0
    for page in itertools.count(1):
        url_crawl = url+'view/-{}'.format(page)
        html = download_v1_2(url_crawl)
        if html is None:
            num_errors += 1
            if num_errors == max_errors:
                break
        else:
            num_errors = 0

