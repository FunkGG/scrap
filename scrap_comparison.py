from bs4 import BeautifulSoup
from scraping import download
import lxml.html
import time
import re


FIELDS = ('area', 'population', 'iso', 'country', 'capital', 'continent',
          'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format',
          'postal_code_regex', 'languages', 'neighbours')


def re_scraper(html):
    results = {}
    for field in FIELDS:
        results[field] = re.search('<tr id="places_%s__row">.*?'
                                   '<td class="w2p_fw">(.*?)</td>' %field, html).groups()[0]
    return results


def bs_scraper(html):
    soup = BeautifulSoup(html,'html.parser')
    results = {}
    for field in FIELDS:
        results[field] = soup.find('table').find('tr', id='places_%s__row'
                                                %field).find('td',class_='w2p_fw').text
    return results


def lxml_scraper(html):
    tree = lxml.html.fromstring(html)
    results = {}
    for field in FIELDS:
        results[field] = tree.cssselect('table > tr#places_%s__row > td.w2p_fw'
                                      %field)[0].text_content()
    return results


def main():
    NUM_ITERATION = 1000
    headers = {}
    headers['User_agent'] = 'FunkGG'
    html = download('http://example.webscraping.com/places/default/view/Afghanistan-1', headers=headers)
    html = html.decode('utf-8')
    for name, scaper in[('Refullar expressions', re_scraper),
                        ('BeautifulSoup', bs_scraper),
                        ('Lxml', lxml_scraper)]:
        start=time.time()
        for i in range(NUM_ITERATION):
            if scaper == re_scraper:
                re.purge()
            result = scaper(html)
            assert(result['area'] == '647,500 square kilometres')
        end = time.time()
        print('%s:%.2f seconds'%(name, end-start))


if __name__ == '__main__':
    main()
