from crawl_function import *
from queue import deque


def link_crawler(seed_url, link_regex=None, delay=5, num_retries=1, max_depth=-1,
                 max_urls=-1, user_agent='FunkGG', proxy=None, scrape_callback=None):
    crawl_queue = deque([seed_url])  # 待爬取队列
    seen = {seed_url:0}             # 记录以爬取过的网址和其深度
    num_urls = 0           #
    rp = get_robots(seed_url)   # 读取robots.txt的信息
    throttle = Throttle(delay)  # 下载限速
    headers = {}
    if user_agent:
        headers['User_agent'] = user_agent  # 设置User_agent

    while crawl_queue:
        url = crawl_queue.pop()
        if rp.can_fetch(user_agent, url):
            throttle.wait(url)
            html = download(url, headers, proxy=proxy, num_retries=num_retries)
            depth = seen[url]
            links = []
            if scrape_callback:
                links.extend(scrape_callback(url, html) or [])
            if depth != max_depth:
                if link_regex:
                    links.extend(link for link in get_links(html) if re.match(link_regex, link))
            for link in links:
                link = normalize(seed_url, link) # 创建绝对链接
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
