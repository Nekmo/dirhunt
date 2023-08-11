# -*- coding: utf-8 -*-
import asyncio
import datetime
import functools
import json
import os
from asyncio import Semaphore, Task
from collections import defaultdict
from concurrent.futures.thread import _python_exit
from hashlib import sha256
from threading import Lock, ThreadError
from typing import Optional, Set, Coroutine, Any, Dict

import humanize as humanize
from click import get_terminal_size
from rich.console import Console
from rich.text import Text

from dirhunt import __version__
from dirhunt._compat import queue, Queue, unregister
from dirhunt.configuration import Configuration
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.exceptions import (
    IncompatibleVersionError,
)
from dirhunt.json_report import JsonReportEncoder
from dirhunt.processors import ProcessBase
from dirhunt.sessions import Session
from dirhunt.sources import Sources
from dirhunt.url_info import UrlsInfo

"""Flags importance"""


resume_dir = os.path.expanduser("~/.cache/dirhunt/")


class DomainSemaphore:
    """Asyncio Semaphore per domain."""

    def __init__(self, concurrency: int):
        """Initialize DomainSemaphore."""
        self.concurrency = concurrency
        self.semaphores = {}

    async def acquire(self, domain: str):
        """Acquire semaphore for domain."""
        if domain not in self.semaphores:
            self.semaphores[domain] = Semaphore(self.concurrency)
        await self.semaphores[domain].acquire()

    def release(self, domain: str):
        """Release semaphore for domain."""
        self.semaphores[domain].release()


class Crawler:
    urls_info = None

    def __init__(self, configuration: Configuration, loop: asyncio.AbstractEventLoop):
        """Initialize Crawler.
        :param configuration: Configuration instance
        :param loop: asyncio loop
        """
        self.configuration = configuration
        self.loop = loop
        self.tasks: Set[Task] = set()
        self.crawler_urls: Set[CrawlerUrl] = set()
        self.domains: Set[str] = set()
        self.console = Console(highlight=False)
        self.session = Session(self)
        self.domain_semaphore = DomainSemaphore(configuration.concurrency)
        self.results = Queue()
        self.index_of_processors = []
        self.processed = {}
        self.add_lock = Lock()
        self.start_dt = datetime.datetime.now()
        self.current_processed_count: int = 0
        self.sources = Sources(self)
        self.domain_protocols: Dict[str, set] = defaultdict(set)

    async def start(self):
        """Add urls to process."""
        for url in self.configuration.urls:
            crawler_url = CrawlerUrl(self, url, depth=self.configuration.max_depth)
            await self.add_domain(crawler_url.url.domain)
            await self.add_crawler_url(crawler_url)
            self.add_domain_protocol(crawler_url)

        while self.tasks:
            await asyncio.wait(self.tasks)
        await self.session.close()

    async def add_crawler_url(self, crawler_url: CrawlerUrl) -> Optional[asyncio.Task]:
        """Add crawler_url to tasks"""
        if crawler_url in self.crawler_urls or not self.in_domains(
            crawler_url.url.domain
        ):
            return
        self.current_processed_count += 1
        self.crawler_urls.add(crawler_url)
        return self.add_task(
            crawler_url.retrieve(), name=f"crawlerurl-{self.current_processed_count}"
        )

    async def add_domain(self, domain: str):
        """Add domain to domains."""
        if domain in self.domains:
            return
        self.domains.add(domain)
        await self.sources.add_domain(domain)

    @functools.lru_cache(maxsize=128)
    def in_domains(self, target_domain):
        if target_domain in self.domains:
            return True
        if self.configuration.not_follow_subdomains:
            return False
        for domain in self.domains:
            if target_domain.endswith(f".{domain}"):
                self.domains.add(target_domain)
                return True
        return False

    def print_error(self, message: str):
        """Print error message to console."""
        text = Text()
        text.append("[ERROR] ", style="red")
        text.append(message)
        self.console.print(text)

    def print_processor(self, processor: ProcessBase):
        """Print processor to console."""
        if 300 > processor.status >= 200:
            self.add_domain_protocol(processor.crawler_url)
        self.console.print(processor.get_text())

    def add_domain_protocol(self, crawler_url: "CrawlerUrl"):
        """Add domain protocol"""
        self.domain_protocols[crawler_url.url.domain].add(crawler_url.url.protocol)

    def add_init_urls(self, *urls):
        """Add urls to queue."""
        self.initial_urls.extend(urls)
        for crawler_url in urls:
            if not isinstance(crawler_url, CrawlerUrl):
                crawler_url = CrawlerUrl(
                    self, crawler_url, depth=self.depth, timeout=self.timeout
                )
            self.add_domain(crawler_url.url.only_domain)
            self.add_url(crawler_url, lock=False)

    def add_task(
        self, coro: Coroutine[Any, Any, Any], name: Optional[str] = None
    ) -> Task:
        task = self.loop.create_task(coro, name=name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    def add_message(self, body):
        from dirhunt.processors import Message

        self.results.put(Message(body))

    def echo(self, body):
        if self.std is None:
            return
        # TODO: remove ANSI chars on is not tty
        self.std.write(str(body))
        self.std.write("\n")

    def erase(self):
        if self.std is None or not self.std.isatty():
            return
        CURSOR_UP_ONE = "\x1b[1A"
        ERASE_LINE = "\x1b[2K"
        # This can be improved. In the future we may want to define stdout/stderr with an cli option
        # fn = sys.stderr.write if sys.stderr.isatty() else sys.stdout.write
        self.std.write(CURSOR_UP_ONE + ERASE_LINE)

    def print_progress(self, finished=False):
        if not self.progress_enabled:
            # Cancel print progress on
            return
        self.echo(
            "{} {} {}".format(
                next(self.spinner),
                "Finished after" if finished else "Started",
                (humanize.naturaldelta if finished else humanize.naturaltime)(
                    datetime.datetime.now() - self.start_dt
                ),
            )
        )

    def print_results(self, exclude=None, include=None):
        exclude = exclude or set()
        self.echo("Starting...")
        while True:
            result = None
            try:
                result = self.results.get(timeout=0.5)
            except queue.Empty:
                pass
            self.erase()
            if (
                result
                and result.maybe_directory()
                and not (result.crawler_url.flags & exclude)
                and (not include or (include & result.crawler_url.flags))
            ):
                self.echo(result)
            self.print_progress()
            if (
                (self.sources.finished() and not self.processing)
                or self.current_processed_count >= self.limit
                and self.limit
            ):
                # Ended
                if self.current_processed_count >= self.limit and self.limit:
                    # Force shutdown
                    self.closing = True
                    self.erase()
                    self.echo(
                        "Results limit reached ({}). Finishing...".format(self.limit)
                    )
                    self.shutdown()
                self.erase()
                self.print_progress(True)
                return

    def print_urls_info(self):
        if not self.index_of_processors:
            self.echo(r"No interesting files detected ¯\_(ツ)_/¯")
            return
        self.echo("━" * get_terminal_size()[0])
        self.urls_info = UrlsInfo(
            self.index_of_processors,
            self.sessions,
            self.std,
            self._max_workers,
            self.progress_enabled,
            self.timeout,
            bool(self.to_file),
        )
        self.urls_info.start()

    def restart(self):
        try:
            self.add_lock.release()
        except (ThreadError, RuntimeError):
            pass

    def options(self):
        return {
            "interesting_extensions": self.interesting_extensions,
            "interesting_files": self.interesting_files,
            "interesting_keywords": self.interesting_keywords,
            "timeout": self.timeout,
            "depth": self.depth,
            "not_follow_subdomains": self.not_follow_subdomains,
            "exclude_sources": self.exclude_sources,
            "not_allow_redirects": self.not_allow_redirects,
            "proxies": self.proxies,
            "delay": self.delay,
            "limit": self.limit,
            "initial_urls": self.initial_urls,
        }

    @property
    def options_file(self):
        checksum = sha256(
            json.dumps(self.options(), sort_keys=True).encode("utf-8")
        ).hexdigest()
        return os.path.join(resume_dir, checksum)

    def get_resume_file(self):
        return self.to_file or self.options_file

    def close(self, create_resume=False):
        self.closing = True
        self.shutdown(False)
        if create_resume:
            self.create_report(self.get_resume_file())
        unregister(_python_exit)

    def create_report(self, to_file):
        """Write to a file a report with current json() state. This file can be read
        to continue an analysis."""
        to_file = os.path.abspath(to_file)
        directory = os.path.dirname(to_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        data = self.json()
        with open(to_file, "w") as f:
            json.dump(data, f, cls=JsonReportEncoder, indent=4, sort_keys=True)

    def resume(self, path):
        resume_data = json.load(open(path))
        file_version = resume_data.get("version")
        if file_version != __version__:
            raise IncompatibleVersionError(
                "Analysis file incompatible with the current version of dirhunt. "
                "Dirhunt version: {}. File version: {}".format(
                    __version__, file_version
                )
            )
        for data in resume_data["processed"]:
            crawler_url_data = data["crawler_url"]
            url = crawler_url_data["url"]["address"]
            crawler_url = CrawlerUrl(
                self,
                url,
                crawler_url_data["depth"],
                None,
                crawler_url_data["exists"],
                crawler_url_data["type"],
            )
            crawler_url.flags = set(crawler_url_data["flags"])
            crawler_url.processor_data = data
            self.processed[url] = crawler_url
            self.echo(data["line"])
        for url in resume_data["processing"]:
            self.add_url(url, lock=False)

    def json(self):
        urls_infos = self.urls_info.urls_info if self.urls_info else []
        urls_infos = [urls_info.json() for urls_info in urls_infos]
        return {
            "version": __version__,
            "current_processed_count": self.current_processed_count,
            "domains": self.domains,
            "index_of_processors": self.index_of_processors,
            "processing": list(self.processing.keys()),
            "processed": list(
                filter(
                    bool,
                    [processed.processor_data for processed in self.processed.values()],
                )
            ),
            "urls_infos": urls_infos,
        }
