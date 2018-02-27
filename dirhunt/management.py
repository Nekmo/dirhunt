from __future__ import print_function
import re
import click as click
import os

import sys

from dirhunt.crawler import Crawler
from dirhunt.output import output_urls
from dirhunt.utils import lrange, catch_keyboard_interrupt, force_url
from colorama import init

init(autoreset=True)

STATUS_CODES = lrange(100, 102+1) + lrange(200, 208+1) + [226] + lrange(300, 308+1) + lrange(400, 418+1) + \
               lrange(421, 426+1) + [428, 429, 431, 451] + lrange(500, 511+1)
INTERESTING_EXTS = ['php', 'zip', 'sh', 'asp', 'csv', 'log']
INTERESTING_FILES = ['access_log', 'error_log', 'error', 'logs', 'dump']
STDOUT_FLAGS = ['blank', 'not_found.fake', 'html']


def comma_separated(ctx, param, value):
    return (value or '').split(',')


def comma_separated_files(ctx, param, value):
    values = comma_separated(ctx, param, value)
    items = []
    for value in values:
        if value.startswith('/') or value.startswith('./'):
            lines = [line.rstrip('\n\r') for line in open(value).readlines()]
            items += [line for line in lines if line]
        else:
            items.append(value)
    return items


def status_code_range(start, end):
    return list(filter(lambda x: start <= x <= end, STATUS_CODES))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@click.command()
@click.argument('urls', nargs=-1, type=force_url)
@click.option('-t', '--threads', type=int, default=(os.cpu_count() or 1) * 5,
              help='Number of threads to use.')
@click.option('-x', '--exclude-flags', callback=comma_separated_files,
              help='Exclude results with these flags. See documentation.')
@click.option('-e', '--interesting-extensions', callback=comma_separated_files, default=','.join(INTERESTING_EXTS),
              help='The files found with these extensions are interesting')
@click.option('-f', '--interesting-files', callback=comma_separated_files, default=','.join(INTERESTING_FILES),
              help='The files with these names are interesting')
@click.option('--stdout-flags', callback=comma_separated_files, default=','.join(STDOUT_FLAGS),
              help='Return only in stdout the urls of these flags')
@click.option('--progress-enabled/--progress-disabled', default=None)
def hunt(urls, threads, exclude_flags, interesting_extensions, interesting_files, stdout_flags, progress_enabled):
    """

    :param int threads:
    :type exclude_flags: list
    """
    for code in tuple(exclude_flags):
        match = re.match('^(\d{3})-(\d{3})$', code)
        if match:
            exclude_flags.remove(code)
            exclude_flags += list(map(str, status_code_range(*map(int, match.groups()))))
    progress_enabled = (sys.stdout.isatty() or sys.stderr.isatty()) if progress_enabled is None else progress_enabled
    crawler = Crawler(max_workers=threads, interesting_extensions=interesting_extensions,
                      interesting_files=interesting_files, std=sys.stdout if sys.stdout.isatty() else sys.stderr,
                      progress_enabled=progress_enabled)
    crawler.add_init_urls(*urls)
    try:
        catch_keyboard_interrupt(crawler.print_results, crawler.restart)(set(exclude_flags))
    except SystemExit:
        crawler.close()
    if not sys.stdout.isatty():
        output_urls(crawler, stdout_flags)
