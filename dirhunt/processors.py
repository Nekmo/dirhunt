from bs4 import BeautifulSoup, Comment

from dirhunt.crawler import CrawlerUrl


def full_url_address(address, url):
    """

    :type url: Url
    :type address: str

    """
    # TODO: url relativa
    if address is None:
        return
    if '://' not in address or address.startswith('/'):
        url = url.copy()
        url.path = address
        return url.url
    return address


class ProcessBase(object):
    def __init__(self, response, text, crawler_url, soup=None):
        """

        :type crawler_url: CrawlerUrl
        """
        self.response = response
        # TODO: procesar otras cosas (css, etc.)
        self.text = text
        self.soup = soup
        self.crawler_url = crawler_url


    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError

    def maybe_directory(self):
        return self.crawler_url.maybe_directory()

    def __str__(self):
        return '[{}] {} ({})'.format(self.response.status_code, self.crawler_url.url.url, self.__class__.__name__)


class GenericProcessor(ProcessBase):
    def process(self):
        pass


class ProcessHtmlRequest(ProcessBase):

    def process(self):
        assets = []
        assets += [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                   for link in self.soup.find_all('link')]
        assets += [full_url_address(script.attrs.get('src'), self.crawler_url.url)
                   for script in self.soup.find_all('script')]
        assets += [full_url_address(img.attrs.get('src'), self.crawler_url.url)
                   for img in self.soup.find_all('img')]
        for asset in filter(bool, assets):
            self.crawler_url.crawler.add_url(CrawlerUrl(self.crawler_url.crawler, asset, 3, self.crawler_url,
                                                        type='asset'))

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        return response.headers.get('Content-Type', '').lower().startswith('text/html')


class ProcessIndexOfRequest(ProcessHtmlRequest):

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if not super(ProcessIndexOfRequest, cls).is_applicable(response, text, crawler_url, soup):
            return False
        title = soup.find('title')
        return title and title.text.lower().startswith('Index Of')


class ProcessWhitePageRequest(ProcessHtmlRequest):

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if response.status_code >= 300:
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


def get_processor(response, text, crawler_url):
    soup = BeautifulSoup(text, 'html.parser')
    for processor_class in PROCESSORS:
        if processor_class.is_applicable(response, text, crawler_url, soup):
            return processor_class(response, text, crawler_url, soup)


PROCESSORS = [
    ProcessIndexOfRequest,
    ProcessWhitePageRequest,
    ProcessHtmlRequest,
]
