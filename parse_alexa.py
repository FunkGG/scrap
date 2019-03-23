from crawl_function import Downloader, normalize, get_robots
from io import StringIO
from zipfile import ZipFile
import csv
from cache import MongoCache, MongoQueue
from queue import deque
import datetime
import time
import threading
from multiprocessing import Process, Manager


def link_crawler(seed_url, link_regex=None, delay=0, num_retries=-1, max_depth=-1,
                 max_urls=100, user_agent='wasp', proxies=None, scrape_callback=None, cache=MongoCache()):
    crawl_queue = seed_url  # 待爬取队列
    num_urls = 0           #
    download = Downloader(delay, user_agent, proxies, num_retries, cache=cache)
    while crawl_queue:
        url = crawl_queue.pop()
        # rp = get_robots(url)

        try:
            html = download(url)
        except ConnectionResetError as crerror:
            print(crerror)
        # else:
        #     print('Blocked by robots.txt:', url)


def threaded_crawler(seed_url, max_threads=5):
    threads = []
    while threads or seed_url:
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
        while len(threads) < max_threads and seed_url:
            thread = threading.Thread(target=link_crawler, args=(seed_url,))
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        time.sleep(1)


def get_urls():
    # D = Downloader()
    # zipped_data = D('http://s3.amazonaws.com/alexa-static/top-1m.csv.zip')
    file = 'top-1m.csv'
    urls = []
    with open(file) as f:
        reader = csv.reader(f)
        for _, website in reader:
            urls.append('http://' + website)
            if len(urls) == 40:
                break
    return urls


if __name__ == '__main__':
    MongoCache().clear()
    urls = get_urls()
    print(len(urls))
    urls_man = Manager().list(urls)
    time1 = datetime.datetime.now()
    # link_crawler(urls_man)  # 串行113s
    # threaded_crawler(urls_man)  # 多线程 28s
    # 多进程35s windows下，创建进程必须在 if __name__...下
    num_cpus = 4
    # pool = multiprocessing.Pool(processes=num_cpus)
    processes = []
    for i in range(num_cpus):
        p = Process(target=threaded_crawler, args=(urls_man,))
        # parsed = pool.apply_async(threaded_link_crawler, args, kwargs)
        p.start()
        processes.append(p)
    # wait for processes to complete
    for p in processes:
        p.join()
    time2 = datetime.datetime.now()
    print((time2-time1).seconds)
