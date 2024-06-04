import requests
import json
import re
import requests
from bs4 import BeautifulSoup
import json
import logging
import numpy as np

def scrape_subito(keyword):
   
    response = requests.get('https://www.subito.it/annunci-italia/vendita/usato/?q={}'.format(keyword))
    response.raise_for_status()

    content = response.text

    results = re.findall(r'<h3 class="title"><a href="(.+)">(.+)</a>', content)

    for result in results:
        url = result[0]
        name = result[1]
        print('URL: {}, Name: {}'.format(url, name))

if __name__ == '__main__':
    keyword = ('god of war ragnarok')
    scrape_subito(keyword)
