from dirhunt.crawler import Crawler
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.sources import SOURCE_CLASSES, get_source_name


class CrawlerTestBase(object):
    url = 'http://domain.com/path/'

    def get_crawler(self, **kwargs):
        return Crawler(interesting_extensions=['php'], interesting_files=['error_log'],
                       exclude_sources=[get_source_name(src) for src in SOURCE_CLASSES],
                       **kwargs)

    def get_crawler_url(self):
         crawler = self.get_crawler()
         return CrawlerUrl(crawler, self.url)
