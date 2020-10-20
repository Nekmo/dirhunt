# -*- coding: utf-8 -*-
import socket

from bs4 import BeautifulSoup
from requests import RequestException
from urllib3.exceptions import ReadTimeoutError

from dirhunt.url import Url
from dirhunt.url_loop import is_url_loop

MAX_RESPONSE_SIZE = 1024 * 512
FLAGS_WEIGHT = {
    'blank': 4,
    'not_found.fake': 3,
    'html': 2,
}


class CrawlerUrl(object):
    def __init__(self, crawler, url, depth=3, source=None, exists=None, type=None, timeout=10):
        """

        :type crawler: Crawler
        :type depth: int Máxima recursión sin haber subido respecto esta url
        """
        self.flags = set()
        self.depth = depth
        if not isinstance(url, Url):
            url = Url(url)
        if url.is_valid():
            url.query = ''
            url.fragment = ''
        self.url = url
        self.crawler = crawler
        self.source = source
        self.exists = exists
        self.type = type
        self.timeout = timeout
        if url.is_valid() and (not url.path or url.path == '/'):
            self.type = 'directory'
        self.resp = None
        self.processor_data = None

    def add_self_directories(self, exists=None, type_=None):
        for url in self.url.breadcrumb():
            self.crawler.add_url(CrawlerUrl(self.crawler, url, self.depth - 1, self, exists, type_,
                                            timeout=self.timeout))
            # TODO: si no se puede añadir porque ya se ha añadido, establecer como que ya existe si la orden es exists

    def start(self):
        from dirhunt.processors import get_processor, GenericProcessor, Error, ProcessIndexOfRequest

        session = self.crawler.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, verify=False, timeout=self.timeout, allow_redirects=False)
        except RequestException as e:
            self.crawler.current_processed_count += 1
            self.crawler.results.put(Error(self, e))
            self.close()
            return self

        self.set_type(resp.headers.get('Content-Type'))
        self.flags.add(str(resp.status_code))

        text = ''
        soup = None
        processor = None
        if resp.status_code < 300 and self.must_be_downloaded(resp):
            try:
                text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
            except (RequestException, ReadTimeoutError, socket.timeout) as e:
                self.crawler.current_processed_count += 1
                self.crawler.results.put(Error(self, e))
                self.close()
                return self
            soup = BeautifulSoup(text, 'html.parser') if resp.headers.get('Content-Type') == 'text/html' else None
        if self.must_be_downloaded(resp):
            processor = get_processor(resp, text, self, soup) or GenericProcessor(resp, self)
            processor.process(text, soup)
            self.flags.update(processor.flags)
        if self.maybe_directory():
            self.crawler.results.put(processor)
        if processor is not None:
            self.processor_data = processor.json()
        if processor and isinstance(processor, ProcessIndexOfRequest):
            self.crawler.index_of_processors.append(processor)
        else:
            self.crawler.current_processed_count += 1
        # TODO: Podemos fijarnos en el processor.index_file. Si existe y es un 200, entonces es que existe.
        if self.exists is None and resp.status_code < 404:
            self.exists = True
        self.add_self_directories(True if (not self.maybe_rewrite() and self.exists) else None,
                                  'directory' if not self.maybe_rewrite() else None)
        self.close()
        return self

    def set_type(self, content_type):
        from dirhunt.processors import INDEX_FILES
        if not self.type and not (content_type or '').startswith('text/html'):
            self.type = 'asset'
        if not self.type and (content_type or '').startswith('text/html') and self.url.name in INDEX_FILES:
            self.type = 'document'

    def maybe_rewrite(self):
        return self.type not in ['asset', 'directory']

    def must_be_downloaded(self, response):
        """The file must be downloaded to obtain information.
        """
        return self.maybe_directory() or (response.headers.get('Content-Type') in [
            'text/css', 'application/javascript'
        ])

    def maybe_directory(self):
        return self.type not in ['asset', 'document', 'rewrite'] or self.type in ['directory']

    def result(self):
        # Cuando se ejecuta el result() de future, si ya está processed, devolverse a sí mismo
        return self

    def weight(self):
        value = sum([FLAGS_WEIGHT.get(flag, 0) for flag in self.flags])
        if self.url and self.url.is_valid():
            value -= len(list(self.url.breadcrumb())) * 1.5
        return value

    def close(self):
        self.crawler.processed[self.url.url] = self
        del self.crawler.processing[self.url.url]

    def json(self):
        return {
            'flags': self.flags,
            'depth': self.depth,
            'url': self.url,
            'type': self.type,
            'exists': self.exists,
        }
