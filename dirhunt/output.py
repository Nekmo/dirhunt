# -*- coding: utf-8 -*-


def output_urls(crawler, stdout_flags):
    stdout_flags = set(stdout_flags)
    crawler_urls = filter(lambda x: x.maybe_directory(), crawler.processed.values())
    crawler_urls = list(filter(lambda x: x.flags & stdout_flags, crawler_urls))
    for crawler_url in sorted(crawler_urls, key=lambda x: x.weight(), reverse=True):
        print(crawler_url.url.url)
