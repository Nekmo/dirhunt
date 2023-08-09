# -*- coding: utf-8 -*-
import re
import sys
from itertools import chain
from typing import List, Type, Iterator, Optional

from aiohttp.web_response import Response
from rich.text import Text

from dirhunt.directory_lists import get_directory_list

if sys.version_info < (3,):
    reload(sys)
    sys.setdefaultencoding("utf-8")

from bs4 import Comment
from colorama import Fore, Back

from dirhunt.colors import status_code_colors
from dirhunt.crawler_url import CrawlerUrl, CrawlerUrlRequest
from dirhunt.url import Url, full_url_address
from dirhunt.url_loop import is_url_loop
from dirhunt.utils import colored

INDEX_FILES = ["index.php", "index.html", "index.htm"]
# Regex for JS. Source: https://github.com/GerbenJavado/LinkFinder/blob/master/linkfinder.py
TEXT_PLAIN_PATH_STRING_REGEX = r"""

  (?:"|')                               # Start newline delimiter

  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path

    |

    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be

    |

    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/]{1,}                 # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

  )

  (?:"|')                               # End newline delimiter

"""


class ProcessBase:
    name = ""
    key_name = ""
    index_file = None
    status_code = 0  # TODO: rename to status
    requires_content = False
    # If the processor has descendants, use get_processor after retrieve the content
    # to get the correct processor
    has_descendants = False

    def __init__(self, crawler_url_request: "CrawlerUrlRequest"):
        """
        :type crawler_url_request: CrawlerUrlRequest
        """
        if crawler_url_request.response is not None:
            self.status_code = crawler_url_request.response.status
        # The crawler_url_request takes a lot of memory, so we don't save it
        self.crawler_url = crawler_url_request.crawler_url
        self.keywords_found = set()

    async def search_index_files(self):
        """Search for index files in the directory. For example index.php, index.html, etc."""
        if self.crawler_url.url_type not in ["directory", None]:
            return
        crawler = self.crawler_url.crawler
        for index_file in INDEX_FILES:
            url = self.crawler_url.url.copy()
            url.set_children(index_file)
            sub_crawler_url = CrawlerUrl(
                crawler,
                url,
                self.crawler_url.depth - 1,
                self.crawler_url,
                None,
                "index_file",
            )
            await self.crawler_url.crawler.add_crawler_url(sub_crawler_url)
            if sub_crawler_url.exists and sub_crawler_url.processor.status_code == 200:
                self.index_file = url
                break

    def search_keywords(self, text):
        for keyword in self.crawler_url.crawler.configuration.interesting_keywords:
            if keyword in text:
                self.keywords_found.add(keyword)

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest"):
        raise NotImplementedError

    async def process(self, crawler_url_request: "CrawlerUrlRequest"):
        raise NotImplementedError

    @property
    def flags(self):
        return {self.key_name}

    def maybe_directory(self):
        return self.crawler_url.maybe_directory()

    def get_url_line_text(self):
        """Return a Text object with the url info in a line."""
        text = Text()
        text.append(
            "[{}]".format(self.status_code), status_code_colors(self.status_code)
        )
        text.append(" {} ".format(self.crawler_url.url.url))
        text.append(" ({})".format(self.name or self.__class__.__name__), "gold1")
        return text

    async def add_url(self, url: Url, depth: int = 3, **kwargs) -> None:
        """Add a new url to the crawler.

        :param url: Url to add
        :param depth: Depth of the url
        """
        if is_url_loop(url):
            return
        await self.crawler_url.crawler.add_crawler_url(
            CrawlerUrl(
                self.crawler_url.crawler, str(url), depth, self.crawler_url, **kwargs
            )
        )

    def get_text(self) -> Text:
        """Return a Text object with the info of the processor."""
        text = self.get_url_line_text()
        if self.index_file:
            text.append("\n    Index file found: ", "blue1")
            text.append("{}".format(self.index_file.name))
        if self.keywords_found:
            text.append("\n    Keywords found: ", "blue1")
            text.append(", ".join(self.keywords_found))
        return text

    def json(self) -> dict:
        return {
            "processor_class": "{}".format(self.__class__.__name__),
            "status_code": self.status_code,
            "crawler_url": self.crawler_url.json(),
            "line": str(self),
        }


class Error(ProcessBase):
    name = "Error"
    key_name = "error"

    def __init__(
        self, crawler_url_request: "CrawlerUrlRequest", error
    ):  # TODO: remove error?
        super(Error, self).__init__(crawler_url_request)
        self.error = error

    def process(self, text, soup=None):
        pass

    def __str__(self):
        body = colored("[ERROR]", Back.LIGHTRED_EX, Fore.LIGHTWHITE_EX)
        body += " {} ".format(self.crawler_url.url.url)
        body += colored("({})".format(self.error), Fore.LIGHTYELLOW_EX)
        return body

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest"):
        pass


# TODO: remove this class
class Message(Error):
    def __init__(self, error, level="ERROR"):
        super(Error, self).__init__(None, CrawlerUrl(None, ""))
        self.error = error
        self.level = level

    def __str__(self):
        body = colored("[{}]".format(self.level), Back.LIGHTRED_EX, Fore.LIGHTWHITE_EX)
        body += colored(" {}".format(self.error), Fore.LIGHTYELLOW_EX)
        return body

    def maybe_directory(self):
        return True


class GenericProcessor(ProcessBase):
    """Generic processor. It's used when the processor is not found.
    It's the last processor to be executed. It's always applicable.
    """

    name = "Generic"
    key_name = "generic"

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for index files
        in the directory.
        """
        await self.search_index_files()

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """This processor is always applicable."""
        return True


class ProcessRedirect(ProcessBase):
    """Processor for redirects. It's applicable when the response status code is 3xx."""

    name = "Redirect"
    key_name = "redirect"
    redirector = None

    def __init__(self, crawler_url_request: "CrawlerUrlRequest"):
        """Initialize the processor."""
        super(ProcessRedirect, self).__init__(crawler_url_request)
        self.redirector = full_url_address(
            crawler_url_request.response.headers.get("Location"), self.crawler_url.url
        )

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will add the redirector url to the crawler."""
        if not self.crawler_url.crawler.configuration.not_allow_redirects:
            await self.add_url(self.redirector)

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """This processor is applicable when the response status code is 3xx."""
        return (
            crawler_url_request.response is not None
            and 300 <= crawler_url_request.response.status < 400
            # if we are searching for index files, we don't want to follow redirects
            and crawler_url_request.crawler_url.url_type != "index_file"
        )

    def get_text(self) -> Text:
        """Return a Text object with the info of the processor."""
        text = super(ProcessRedirect, self).get_text()
        text.append("\n    Redirect to: ", "blue1")
        text.append("{}".format(self.redirector))
        return text


class ProcessNotFound(ProcessBase):
    """Processor for 404 errors. It's applicable when the response status code is 404."""

    name = "Not Found"
    key_name = "not_found"

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for index files."""
        await self.search_index_files()

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> None:
        """This processor is applicable when the response status code is 404."""
        return (
            crawler_url_request.response is not None
            and crawler_url_request.response.status == 404
        )

    def get_text(self) -> Text:
        """Return a Text object with the info of the processor."""
        text = self.get_url_line_text()
        if self.crawler_url.exists:
            text.append(" (FAKE 404)", "gold1")
        if self.index_file:
            text.append(
                "\n    Index file found: {}".format(self.index_file.name), "blue1"
            )
        return text

    @property
    def flags(self):
        flags = super(ProcessNotFound, self).flags
        if self.crawler_url.exists:
            flags.update({"{}.fake".format(self.key_name)})
        return flags


class ProcessCssStyleSheet(ProcessBase):
    """Processor for CSS stylesheets. It's applicable when the response content type is text/css."""

    name = "CSS StyleSheet"
    key_name = "css"
    requires_content = True

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for urls in the CSS stylesheet."""
        self.search_keywords(crawler_url_request.content)
        urls = [
            full_url_address(url, self.crawler_url.url)
            for url in re.findall(
                ": *url\([\"']?(.+?)[\"']?\)", crawler_url_request.content
            )
        ]
        for url in urls:
            await self.add_url(url, depth=0, url_type="asset")

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """This processor is applicable when the response content type is text/css."""
        return (
            crawler_url_request.response is not None
            and crawler_url_request.response.headers.get("Content-Type", "")
            .lower()
            .startswith("text/css")
            and crawler_url_request.response.status < 300
        )


class ProcessJavaScript(ProcessBase):
    """Processor for JavaScript files. It's applicable when the response content type is application/javascript."""

    name = "JavaScript"
    key_name = "js"
    requires_content = True

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for urls in the JavaScript file."""
        self.search_keywords(crawler_url_request.content)
        urls = [
            full_url_address(url[0], self.crawler_url.url)
            for url in re.findall(
                TEXT_PLAIN_PATH_STRING_REGEX, crawler_url_request.content, re.VERBOSE
            )
        ]
        for url in urls:
            await self.add_url(url, depth=0, url_type="asset")

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """This processor is applicable when the response content type is application/javascript."""
        return (
            crawler_url_request.response is not None
            and crawler_url_request.response.headers.get("Content-Type", "")
            .lower()
            .startswith("application/javascript")
            and crawler_url_request.response.status < 300
        )


class ProcessHtmlRequest(ProcessBase):
    """Processor for HTML documents. It's applicable when the response content type is text/html."""

    name = "HTML document"
    key_name = "html"
    requires_content = True
    has_descendants = True

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for urls in the HTML document."""
        self.search_keywords(crawler_url_request.content)
        await self.assets(crawler_url_request.soup)
        await self.links(crawler_url_request.soup)
        await self.search_index_files()

    async def links(self, soup) -> None:
        """Search for links in the HTML document and add them to Crawler."""
        links = [
            full_url_address(link.attrs.get("href"), self.crawler_url.url)
            for link in soup.find_all("a")
        ]
        metas = filter(
            lambda meta: meta.attrs.get("http-equiv", "").lower() == "refresh",
            soup.find_all("meta"),
        )
        metas = filter(lambda meta: "=" in meta.attrs.get("content", ""), metas)
        links += list(
            map(
                lambda meta: full_url_address(
                    meta.attrs["content"].split("=", 1)[1], self.crawler_url.url
                ),
                metas,
            )
        )
        for link in filter(bool, links):
            url = Url(link)
            if not url.is_valid():
                continue
            depth = self.crawler_url.depth
            if url.domain != self.crawler_url.url.domain or not url.path.startswith(
                self.crawler_url.url.directory_path
            ):
                depth -= 1
            if depth <= 0:
                continue
            await self.add_url(link, depth)

    async def assets(self, soup) -> None:
        """Search for assets in the HTML document and add them to Crawler."""
        assets = [
            full_url_address(link.attrs.get("href"), self.crawler_url.url)
            for link in soup.find_all("link")
        ]
        assets += [
            full_url_address(script.attrs.get("src"), self.crawler_url.url)
            for script in soup.find_all("script")
        ]
        assets += [
            full_url_address(img.attrs.get("src"), self.crawler_url.url)
            for img in soup.find_all("img")
        ]
        for asset in filter(bool, assets):
            self.analyze_asset(asset)
            await self.add_url(asset, url_type="asset")

    def analyze_asset(self, asset) -> None:
        """

        :type asset: Url
        """
        if "wordpress" not in self.crawler_url.flags and "wp-content" in asset.path:
            self.crawler_url.flags.update({"wordpress"})
            # Override type always except for root path
            self.crawler_url.type = (
                "rewrite" if self.crawler_url.type != "directory" else "directory"
            )
            self.crawler_url.depth -= 1

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        return (
            crawler_url_request.response is not None
            and crawler_url_request.response.headers.get("Content-Type", "")
            .lower()
            .startswith("text/html")
            and crawler_url_request.response.status < 300
        )


class ProcessIndexOfRequest(ProcessHtmlRequest):
    """Processor for Index Of pages. It's applicable when the response content
    type is text/html and the page contains a list of links to files and directories.
    """

    name = "Index Of"
    key_name = "index_of"
    files = None
    index_titles = ("index of", "directory listing for")
    requires_content = True
    has_descendants = False

    async def process(self, crawler_url_request: "CrawlerUrlRequest") -> None:
        """Process the request. This method will search for urls in the Index Of page."""
        self.search_keywords(crawler_url_request.content)
        directory_list = get_directory_list(
            crawler_url_request.content, self, crawler_url_request.soup
        )
        links = [
            link
            for link in directory_list.get_links(
                crawler_url_request.content, crawler_url_request.soup
            )
            if link.is_valid()
        ]
        for link in filter(lambda x: x.is_valid() and x.url.endswith("/"), links):
            await self.add_url(link, url_type="directory")
        self.files = links

    def interesting_ext_files(self) -> Iterator[Url]:
        """Return a list of files with interesting extensions."""
        return filter(
            lambda x: x.name.split(".")[-1]
            in self.crawler_url.crawler.configuration.interesting_extensions,
            self.files,
        )

    def interesting_name_files(self) -> Iterator[Url]:
        """Return a list of files with interesting names."""
        return filter(
            lambda x: x.name
            in self.crawler_url.crawler.configuration.interesting_files,
            self.files,
        )

    def interesting_files(self) -> Iterator[Url]:
        """Return a list of files with interesting extensions or names."""
        return chain(self.interesting_ext_files(), self.interesting_name_files())

    def get_text(self) -> Text:
        """Return the text to be displayed in the console."""
        text = super(ProcessIndexOfRequest, self).get_text()
        ext_files = list(self.interesting_ext_files())
        name_files = list(self.interesting_name_files())
        if ext_files:
            text.append("\n    Interesting extension files:", "blue1")
            text.append(
                " {}".format(", ".join(map(lambda x: self.repr_file(x), ext_files)))
            )
        if name_files:
            text.append("\n    Interesting file names:", "deep_sky_blue1")
            text.append(
                " {}".format(", ".join(map(lambda x: self.repr_file(x), name_files)))
            )
        if not ext_files and not name_files:
            text.append(" (Nothing interesting)", "gold1")
        return text

    @classmethod
    def repr_file(cls, file) -> str:
        """Return a string representation of a file."""
        body = file.name
        created_at, filesize = file.extra.get("created_at"), file.extra.get("filesize")
        if created_at or filesize:
            body += " ({})".format(" ⚫ ".join(filter(bool, [created_at, filesize])))
        return body

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """Return True if the request is applicable to this processor."""
        if (
            not super(ProcessIndexOfRequest, cls).is_applicable(crawler_url_request)
            or crawler_url_request.content is None
        ):
            return False
        title = crawler_url_request.soup.find("title")
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
            flags.update({"{}.nothing".format(self.key_name)})
        return flags


class ProcessBlankPageRequest(ProcessHtmlRequest):
    """Processor for blank pages. It's applicable when the response content is empty."""

    name = "Blank page"
    key_name = "blank"
    requires_content = True
    has_descendants = False

    @classmethod
    def is_applicable(cls, crawler_url_request: "CrawlerUrlRequest") -> bool:
        """Return True if the request is applicable to this processor."""
        if (
            not super(ProcessBlankPageRequest, cls).is_applicable(crawler_url_request)
            or crawler_url_request.content is None
        ):
            return False

        def tag_visible(element):
            if element.parent.name in [
                "style",
                "script",
                "head",
                "title",
                "meta",
                "[document]",
            ]:
                return False
            if isinstance(element, Comment):
                return False
            return True

        texts = crawler_url_request.soup.findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        for text in visible_texts:
            if text.strip():
                return False
        return True


def get_processor(crawler_url_request: "CrawlerUrlRequest") -> Optional["ProcessBase"]:
    """Return the processor for the given request."""
    for processor_class in PROCESSORS:
        if processor_class.is_applicable(crawler_url_request):
            return processor_class(crawler_url_request)


PROCESSORS: List[Type[ProcessBase]] = [
    ProcessRedirect,
    ProcessNotFound,
    ProcessCssStyleSheet,
    ProcessJavaScript,
    ProcessIndexOfRequest,
    ProcessBlankPageRequest,
    ProcessHtmlRequest,
    GenericProcessor,
]
