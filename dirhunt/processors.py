# -*- coding: utf-8 -*-
import re

from bs4 import Comment
from colorama import Fore, Back

from dirhunt.colors import status_code_colors
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.url import Url
from dirhunt.url_loop import is_url_loop
from dirhunt.utils import colored

INDEX_FILES = ['index.php', 'index.html', 'index.html']
ACCEPTED_PROTOCOLS = ['http', 'https']


def full_url_address(address, url):
    """

    :type url: Url
    :type address: str
    :rtype :Url

    """
    if address is None:
        return
    protocol_match = address.split(':', 1)[0] if ':' in address else ''
    protocol_match = re.match('^([A-z0-9\\-]+)$', protocol_match)
    if protocol_match and protocol_match.group(1) not in ACCEPTED_PROTOCOLS:
        return
    # TODO: mejorar esto. Aceptar otros protocolos  a rechazar
    if address.startswith('//'):
        address = address.replace('//', '{}://'.format(url.protocol), 1)
    if '://' not in address or address.startswith('/'):
        url = url.copy()
        url.path = address
        return url
    url = Url(address)
    if url.is_valid():
        return url


class ProcessBase(object):
    name = ''
    key_name = ''
    index_file = None
    status_code = 0

    def __init__(self, response, crawler_url):
        """

        :type crawler_url: CrawlerUrl
        """
        # TODO: hay que pensar en no pasar response, text y soup por aquí para establecerlo en self,
        # para no llenar la memoria. Deben ser cosas "volátiles".
        if response is not None:
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
            future = self.crawler_url.crawler.add_url(
                CrawlerUrl(crawler, url, self.crawler_url.depth - 1, self, None, 'document',
                           timeout=self.crawler_url.timeout), True)
            if self.crawler_url.crawler.closing:
                return
            result = future.result()
            if result.exists:
                self.index_file = url
                break

    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        raise NotImplementedError

    def process(self, text, soup=None):
        raise NotImplementedError

    @property
    def flags(self):
        return {self.key_name}

    def maybe_directory(self):
        return self.crawler_url.maybe_directory()

    def url_line(self):
        body = colored('[{}]'.format(self.status_code), status_code_colors(self.status_code))
        body += ' {} '.format(self.crawler_url.url.url)
        body += colored(' ({})'.format(self.name or self.__class__.__name__), Fore.LIGHTYELLOW_EX)
        return body

    def add_url(self, url, depth=3, **kwargs):
        if is_url_loop(url):
            return
        return self.crawler_url.crawler.add_url(CrawlerUrl(self.crawler_url.crawler, url, depth, self.crawler_url,
                                                           timeout=self.crawler_url.timeout, **kwargs))

    def __str__(self):
        body = self.url_line()
        if self.index_file:
            body += colored('\n    Index file found: ', Fore.BLUE)
            body += '{}'.format(self.index_file.name)
        return body


class Error(ProcessBase):

    name = 'Error'
    key_name = 'error'

    def __init__(self, crawler_url, error):
        super(Error, self).__init__(None, crawler_url)
        self.error = error

    def process(self, text, soup=None):
        pass

    def __str__(self):
        body = colored('[ERROR]', Back.LIGHTRED_EX, Fore.LIGHTWHITE_EX)
        body += ' {} '.format(self.crawler_url.url.url)
        body += colored('({})'.format(self.error), Fore.LIGHTYELLOW_EX)
        return body

    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        pass


class GenericProcessor(ProcessBase):
    name = 'Generic'
    key_name = 'generic'

    def process(self, text, soup=None):
        self.search_index_files()


class ProcessRedirect(ProcessBase):
    name = 'Redirect'
    key_name = 'redirect'
    redirector = None

    def __init__(self, response, crawler_url):
        super(ProcessRedirect, self).__init__(response, crawler_url)
        self.redirector = full_url_address(response.headers.get('Location'), self.crawler_url.url)

    def process(self, text, soup=None):
        if not self.crawler_url.crawler.not_allow_redirects:
            self.add_url(self.redirector)

    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        return 300 <= request.status_code < 400

    def __str__(self):
        body = super(ProcessRedirect, self).__str__()
        body += colored('\n    Redirect to: ', Fore.BLUE)
        body += '{}'.format(self.redirector.address)
        return body


class ProcessNotFound(ProcessBase):
    name = 'Not Found'
    key_name = 'not_found'

    def process(self, text, soup=None):
        self.search_index_files()

    @classmethod
    def is_applicable(cls, request, text, crawler_url, soup):
        return request.status_code == 404

    def __str__(self):
        body = self.url_line()
        if self.crawler_url.exists:
            body += colored(' (FAKE 404)', Fore.YELLOW)
        if self.index_file:
            body += '\n    Index file found: {}'.format(self.index_file.name)
        return body

    @property
    def flags(self):
        flags = super(ProcessNotFound, self).flags
        if self.crawler_url.exists:
            flags.update({'{}.fake'.format(self.key_name)})
        return flags


class ProcessHtmlRequest(ProcessBase):
    name = 'HTML document'
    key_name = 'html'

    def process(self, text, soup=None):
        self.assets(soup)
        self.links(soup)
        self.search_index_files()

    def links(self, soup):
        links = [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                 for link in soup.find_all('a')]
        for link in filter(bool, links):
            url = Url(link)
            if not url.is_valid():
                continue
            depth = self.crawler_url.depth
            if url.domain != self.crawler_url.url.domain or \
                    not url.path.startswith(self.crawler_url.url.directory_path):
                depth -= 1
            if depth <= 0:
                continue
            self.add_url(link, depth)

    def assets(self, soup):
        assets = [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                   for link in soup.find_all('link')]
        assets += [full_url_address(script.attrs.get('src'), self.crawler_url.url)
                   for script in soup.find_all('script')]
        assets += [full_url_address(img.attrs.get('src'), self.crawler_url.url)
                   for img in soup.find_all('img')]
        for asset in filter(bool, assets):
            self.analyze_asset(asset)
            self.add_url(asset, type='asset')

    def analyze_asset(self, asset):
        """

        :type asset: Url
        """
        if 'wordpress' not in self.crawler_url.flags and 'wp-content' in asset.path:
            self.crawler_url.flags.update({'wordpress'})
            # Override type always except for root path
            self.crawler_url.type = 'rewrite' if self.crawler_url.type != 'directory' else 'directory'
            self.crawler_url.depth -= 1

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        return response.headers.get('Content-Type', '').lower().startswith('text/html') and response.status_code < 300 \
               and soup is not None


class ProcessIndexOfRequest(ProcessHtmlRequest):
    name = 'Index Of'
    key_name = 'index_of'
    files = None
    index_titles = ('index of', 'directory listing for')

    def process(self, text, soup=None):
        links = [full_url_address(link.attrs.get('href'), self.crawler_url.url)
                   for link in soup.find_all('a')]
        for link in filter(lambda x: x.url.endswith('/'), links):
            self.add_url(link, type='directory')
        self.files = [Url(link) for link in links]

    def interesting_ext_files(self):
        return filter(lambda x: x.name.split('.')[-1] in self.crawler_url.crawler.interesting_extensions, self.files)

    def interesting_name_files(self):
        return filter(lambda x: x.name in self.crawler_url.crawler.interesting_files, self.files)

    def interesting_files(self):
        for iterator in [self.interesting_ext_files(), self.interesting_name_files()]:
            for file in iterator:
                yield file

    def __str__(self):
        body = super(ProcessIndexOfRequest, self).__str__()
        ext_files = list(self.interesting_ext_files())
        name_files = list(self.interesting_name_files())
        if ext_files:
            body += colored('\n    Interesting extension files:', Fore.BLUE)
            body += ' {}'.format(', '.join(map(lambda x: x.name, ext_files)))
        if name_files:
            body += colored('\n    Interesting file names:', Fore.MAGENTA)
            body += ' {}'.format(', '.join(map(lambda x: x.name, name_files)))
        if not ext_files and not name_files:
            body += colored(' (Nothing interesting)', Fore.LIGHTYELLOW_EX)
        return body

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if not super(ProcessIndexOfRequest, cls).is_applicable(response, text, crawler_url, soup):
            return False
        title = soup.find('title')
        if not title:
            return False
        title = title.text.lower()
        for index_title in cls.index_titles:
            if title.startswith(index_title):
                return True
        return False

    @property
    def flags(self):
        flags = super(ProcessHtmlRequest, self).flags
        try:
            next(self.interesting_files())
        except StopIteration:
            flags.update({'{}.nothing'.format(self.key_name)})
        return flags


class ProcessBlankPageRequest(ProcessHtmlRequest):
    name = 'Blank page'
    key_name = 'blank'

    @classmethod
    def is_applicable(cls, response, text, crawler_url, soup):
        if not super(ProcessBlankPageRequest, cls).is_applicable(response, text, crawler_url, soup):
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
    ProcessRedirect,
    ProcessNotFound,
    ProcessIndexOfRequest,
    ProcessBlankPageRequest,
    ProcessHtmlRequest,
]
