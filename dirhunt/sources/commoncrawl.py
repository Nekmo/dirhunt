import json
from json import JSONDecodeError

from requests.exceptions import RequestException
from dirhunt.sessions import Sessions
from dirhunt.sources.base import Source


COMMONCRAWL_URL = 'https://index.commoncrawl.org/collinfo.json'


class CommonCrawl(Source):
    def get_latest_craw_index(self):
        url = COMMONCRAWL_URL
        session = Sessions().get_session()
        try:
            response = session.get(url)
            response.raise_for_status()
            crawl_indexes = response.json()
        except (RequestException, ValueError, JSONDecodeError):
            return
        if not crawl_indexes:
            return
        latest_crawl_index = crawl_indexes[0]
        return latest_crawl_index['cdx-api']


    def callback(self, domain):
        latest_crawl_index = self.get_latest_craw_index()
        if not latest_crawl_index:
            return
        session = Sessions().get_session()
        response = session.get(
            latest_crawl_index,
            params={'url': '*.{}'.format(domain), 'output': 'json'},
            stream=True
        )
        for line in filter(bool, response.iter_lines()):
            data = json.loads(line)
            self.add_result(data['url'])
