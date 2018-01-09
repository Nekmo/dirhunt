from bs4 import BeautifulSoup, Comment

from dirhunt.crawler import CrawlerUrl
from dirhunt.url import Url

INDEX_FILES = ['index.php', 'index.html', 'index.html']
INTERESTING_EXTS = ['php']


def full_url_address(address, url):
    """

    :type url: Url
    :type address: str

    """
    # TODO: url relativa
    if address is None:
        return
    if ('://' not in address or address.startswith('/')) and not address.startswith('//'):
        url = url.copy()
        url.path = address
        return url.url
    return address


class ProcessBase(object):
    name = 'Base'

    def __init__(self, response, crawler_url):
        """

        :type crawler_url: CrawlerUrl
        """
        # TODO: hay que pensar en no pasar response, text y soup por aquí para establecerlo en self,
        # para no llenar la memoria. Deben ser cosas "volátiles".
        self.index_file = None
        self.status_code = response.status_code
        # TODO: procesar otras cosas (css, etc.)
        self.crawler_url = crawler_url

    def search_index_files(self):
        if self.crawler_url.type not in ['directory', None]:
            return
        crawler = self.crawler_url.crawler
        for index_file in INDEX_FILES:
            url = self.crawler_url.url.copy()
            url.set_children(index_file)
            future = self.crawler_url.crawler.add_url(CrawlerUrl(crawler, url, self.crawler_url.depth - 1, self,
                                                                 None, 'document'), True)
            result = future.result()
            if result.exists:
                self.index_file = url
                break

    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        raise NotImplementedError

    def process(self, text, soup=None):
        raise NotImplementedError

    def maybe_directory(self):
        return self.crawler_url.maybe_directory()

    def __str__(self):
        body = '[{}] {} ({})'.format(self.status_code, self.crawler_url.url.url, self.__class__.__name__)
        if self.index_file:
            body += '\n    Index file found: {}'.format(self.index_file.name)
        return body


class GenericProcessor(ProcessBase):
    name = 'Generic'

    def process(self, text, soup=None):
        pass


class ProcessHtmlRequest(ProcessBase):
    name = 'HTML document'

    def process(self, text, soup=None):
        self.assets(text, soup)
        self.search_index_files()

    def assets(self, text, soup):
        assets = []
        assets += [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                   for link in soup.find_all('link')]
        assets += [full_url_address(script.attrs.get('src'), self.crawler_url.url)
                   for script in soup.find_all('script')]
        assets += [full_url_address(img.attrs.get('src'), self.crawler_url.url)
                   for img in soup.find_all('img')]
        for asset in filter(bool, assets):
            self.crawler_url.crawler.add_url(CrawlerUrl(self.crawler_url.crawler, asset, 3, self.crawler_url,
                                                        type='asset'))

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        return response.headers.get('Content-Type', '').lower().startswith('text/html') and response.status_code < 300 \
               and soup is not None


class ProcessIndexOfRequest(ProcessHtmlRequest):
    name = 'Index Of'
    files = None

    def process(self, text, soup=None):
        links = [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                   for link in soup.find_all('a')]
        for link in filter(lambda x: x.endswith('/'), links):
            self.crawler_url.crawler.add_url(CrawlerUrl(self.crawler_url.crawler, link, 3, self.crawler_url,
                                                        type='directory'))
        self.files = [Url(link) for link in links]

    def __str__(self):
        body = super(ProcessIndexOfRequest, self).__str__()
        files = filter(lambda x: x.name.split('.')[-1] in INTERESTING_EXTS, self.files)
        body += '\n    Interesting extension files: {}'.format(', '.join(map(lambda x: x.name, files)))
        return body

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if not super(ProcessIndexOfRequest, cls).is_applicable(response, text, crawler_url, soup):
            return False
        title = soup.find('title')
        return title and title.text.lower().startswith('index of')


class ProcessWhitePageRequest(ProcessHtmlRequest):
    name = 'White page'

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if not super(ProcessWhitePageRequest, cls).is_applicable(response, text, crawler_url, soup):
            return False

        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, Comment):
                return False
            return True
        texts = soup.findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        for text in visible_texts:
            if text.strip():
                return False
        return True


def get_processor(response, text, crawler_url, soup):
    for processor_class in PROCESSORS:
        if processor_class.is_applicable(response, text, crawler_url, soup):
            # TODO: resp por None
            return processor_class(response, crawler_url)


PROCESSORS = [
    ProcessIndexOfRequest,
    ProcessWhitePageRequest,
    ProcessHtmlRequest,
]
