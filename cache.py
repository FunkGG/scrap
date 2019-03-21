from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.binary import Binary
import os
import re
import urllib.parse
import pickle
import zlib


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
        self.client = MongoClient('localhost', 27017) if client is None else client
        # 创建collection(集合)储存缓存页面
        self.db = client.cache
        self.db.webpage.create_index('timestamp',
                                     expireAfterSeconds=expire.total_seconds())

    def __getitem__(self, url):
        record = self.db.webpage.find_one({'_id':url})
        if record:
            return pickle.loads(zlib.decompress(['result']))
        else:
            raise KeyError(url + 'does not exist')

    def __setitem__(self, url, result):
        record = {'result': Binary(zlib.compress(pickle.dumps(result))),
                  'timestamp': datetime.utcnow()}
        self.db.webpage.update({'_id': url}, {'$set': record}, upsert=True)





