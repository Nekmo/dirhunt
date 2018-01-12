import re
import click as click
from dirhunt.crawler import Crawler
from dirhunt.utils import lrange

STATUS_CODES = lrange(100, 102+1) + lrange(200, 208+1) + [226] + lrange(300, 308+1) + lrange(400, 418+1) + \
               lrange(421, 426+1) + [428, 429, 431, 451] + lrange(500, 511+1)
INTERESTING_EXTS = ['php', 'zip', 'sh', 'asp', 'csv', 'log']
INTERESTING_FILES = ['access_log', 'error_log', 'error', 'logs', 'dump']


def comma_separated(ctx, param, value):
    return (value or '').split(',')


def status_code_range(start, end):
    return list(filter(lambda x: start <= x <= end, STATUS_CODES))


@click.command()
@click.argument('urls', nargs=-1)
@click.option('-x', '--exclude-flags', callback=comma_separated,
              help='Exclude results with these flags. See documentation.')
@click.option('-e', '--interesting-extensions', callback=comma_separated, default=','.join(INTERESTING_EXTS),
              help='The files found with these extensions are interesting')
@click.option('-f', '--interesting-files', callback=comma_separated, default=','.join(INTERESTING_FILES),
              help='The files with these names are interesting')
def hunt(urls, exclude_flags, interesting_extensions, interesting_files):
    """

    :type exclude_flags: list
    """
    for code in tuple(exclude_flags):
        match = re.match('^(\d{3})-(\d{3})$', code)
        if match:
            exclude_flags.remove(code)
            exclude_flags += list(map(str, status_code_range(*map(int, match.groups()))))
    crawler = Crawler(interesting_extensions=interesting_extensions, interesting_files=interesting_files)
    crawler.add_init_urls(*urls)
    crawler.print_results(set(exclude_flags))
