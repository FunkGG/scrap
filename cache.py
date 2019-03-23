from datetime import datetime, timedelta
from pymongo import MongoClient, errors
from bson.binary import Binary
import os
import re
import urllib.parse
import pickle
import zlib
from scraping import link_crawler


class DiskCache:
    def __init__(self, cache_dir='cache', expires=timedelta(days=1), compress=True):
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress

    def url_to_path(self, url):
        components = urllib.parse.urlsplit(url)
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += '/index.html'
        filename = components.netloc + path + components.query
        filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        return os.path.join(self.cache_dir, filename)

    def __getitem__(self, url):
        path = self.url_to_path(url)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                data = fp .read()
                if self.compress:
                    data = zlib.decompress(data)
                result, timestamp = pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url + 'has expired')
                return result
        else:
            raise KeyError(url + 'does not exist')

    def __setitem__(self, url, result):
        path = self.url_to_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        data = pickle.dumps((result, datetime.utcnow()))
        if self.compress:
            data = zlib.compress(data)
        with open(path, 'wb') as fp:
            fp.write(data)

    def has_expired(self, timestamp):
        return datetime.utcnow() > timestamp + self.expires


class MongoCache:
    def __init__(self, client=None, expire=timedelta(days=5)):
        # 如果没传入client，连接默认的MongoClient
        self.client = MongoClient("mongodb://localhost:27017/") if client is None else client
        # 创建collection(集合)储存缓存页面
        self.db = self.client.cache
        self.db.webpage.create_index('timestamp',
                                     expireAfterSeconds=expire.total_seconds())

    def __getitem__(self, url):
        record = self.db.webpage.find_one({'_id':url})
        if record:
            return pickle.loads(zlib.decompress(record['result']))
        else:
            raise KeyError(url + 'does not exist')

    def __setitem__(self, url, result):
        record = {'result': Binary(zlib.compress(pickle.dumps(result))),
                  'timestamp': datetime.utcnow()}
        self.db.webpage.update({'_id': url}, {'$set': record}, upsert=True)

    def __contains__(self, url):
        try:
            self[url]
        except KeyError:
            return False
        else:
            return True

    def clear(self):
        self.db.webpage.drop()


class MongoQueue:
    OUTSTANDING, PROCESSING, COMPLETE = range(3)
    """
    OUTSTANDING:当添加一个新URL时
    PROCRSSING:URL从队列中取出准备下载
    COMPLETE:下载结束后
    """
    def __init__(self, client=None, timeout=300):
        """
        timeout: 超时URL状态重设为OUTSTANDING
        """
        self.client = MongoClient("mongodb://localhost:27017/") if client is None else client
        self.db = self.client.cache
        self.timeout = timeout

    def __nonzero__(self):
        """Returns True if there are more jobs to process
        """
        record = self.db.crawl_queue.find_one(
            {'status': {'$ne': self.COMPLETE}}
        )
        return True if record else False

    def push(self, url):
        """Add new URL to queue if does not exist
        """
        try:
            self.db.crawl_queue.insert({'_id': url, 'status': self.OUTSTANDING})
        except errors.DuplicateKeyError as e:
            pass  # this is already in the queue

    def pop(self):
        """Get an outstanding URL from the queue and set its status to processing.
        If the queue is empty a KeyError exception is raised.
        """
        record = self.db.crawl_queue.find_and_modify(
            query={'status': self.OUTSTANDING},
            update={'$set': {'status': self.PROCESSING, 'timestamp': datetime.now()}}
        )
        if record:
            return record['_id']
        else:
            self.repair()
            raise KeyError()

    def peek(self):
        record = self.db.crawl_queue.find_one({'status': self.OUTSTANDING})
        if record:
            return record['_id']

    def complete(self, url):
        self.db.crawl_queue.update({'_id': url}, {'$set': {'status': self.COMPLETE}})

    def repair(self):
        """Release stalled jobs
        """
        record = self.db.crawl_queue.find_and_modify(
            query={
                'timestamp': {'$lt': datetime.now() - timedelta(seconds=self.timeout)},
                'status': {'$ne': self.COMPLETE}
            },
            update={'$set': {'status': self.OUTSTANDING}}
        )
        if record:
            print
            'Released:', record['_id']

    def clear(self):
        self.db.crawl_queue.drop()


if __name__ == '__main__':
    link_crawler('http://example.webscraping.com/', '/places/default/(index|view)', cache=MongoCache(),
                 max_depth=-1, max_urls=10)
    # link_crawler('http://example.webscraping.com/', '/places/default/(index|view)', cache=MongoCache())

