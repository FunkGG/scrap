import urllib.request  # request 请求，这是一个发送http请求的模块
import urllib.error    # error 错误，接收所有urllib.request产生的异常
import urllib.parse

def download_v1(url):   # 这是一个最基本的下载网页函数
    print('Download:',url)
    return urllib.request.urlopen(url).read()


def download_v1_1(url):  # 添加捕捉异常功能
    print('Download:', url)
    try:
        html = urllib.request.urlopen(url).read()
    except urllib.error.URLError as e:
        print('Download error:', e.reason)
        html = None
    return html


def download_v1_2(url, num_retries=2):  # 添加重试下载功能
    print('Download:',url)
    try:
        html = urllib.request.urlopen(url).read()
    except urllib.error.URLError as e:
        print('Download error:', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download_v1_2(url, num_retries - 1)  # 多个return，运行到第一个return即返回，不再执行其他代码
    return html


def download_v1_3(url, user_agent='wswp', num_retries=2):  # 设置用户代理
    print('Download:',url)
    headers = {'User-agent':user_agent}
    request = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(request).read()
    except urllib.error.URLError as e:
        print('Download error:', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download_v1_2(url, num_retries - 1)  # 多个return，运行到第一个return即返回，不再执行其他代码
    return html


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



if __name__ == '__main__':
    url = 'http://example.webscraping.com/'
    url = 'http://httpstat.us/500'
    download_v1_2(url)


