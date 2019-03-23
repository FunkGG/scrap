from crawl_function import *
from queue import deque


def link_crawler(seed_url, link_regex=None, delay=0, num_retries=1, max_depth=-1,
                 max_urls=-1, user_agent='FunkGG', proxies=None, scrape_callback=None, cache=None):
    crawl_queue = deque([seed_url])  # 待爬取队列
    seen = {seed_url:0}             # 记录以爬取过的网址和其深度
    num_urls = 0           #
    rp = get_robots(seed_url)   # 读取robots.txt的信息
    download = Downloader(delay, user_agent, proxies, num_retries, cache=cache)
    while crawl_queue:
        url = crawl_queue.pop()
        if rp.can_fetch(user_agent, url):
            html = download(url)
            depth = seen[url]
            links = []
            if scrape_callback:
                links.extend(scrape_callback(url, html) or [])  # 抓取数据

            # 没有达到设定深度，继续跟踪链接
            if depth != max_depth:
                if link_regex:
                    links.extend(link for link in get_links(html) if re.match(link_regex, link))
            for link in links:
                link = normalize(seed_url, link)  # 创建绝对链接
                if link not in seen:
                    seen[link] = depth+1
                    if same_domain(seed_url, link):
                        crawl_queue.append(link)    # 跟踪连接
            num_urls +=1
            if num_urls == max_urls:
                break
        else:
            print('Blocked by robots.txt:', url)


if __name__ == '__main__':
    # link_crawler('http://example.webscraping.com', '/places/default/(index|view)',
                  # delay = 0, num_retries=1, user_agent='BadCrawler')
    link_crawler('http://example.webscraping.com', '/places/default/(index|view)',
                 delay=0, num_retries=1, max_depth=1)
