import re
import click as click
from dirhunt.crawler import Crawler
from dirhunt.utils import lrange

STATUS_CODES = lrange(100, 102+1) + lrange(200, 208+1) + [226] + lrange(300, 308+1) + lrange(400, 418+1) + \
               lrange(421, 426+1) + [428, 429, 431, 451] + lrange(500, 511+1)

def comma_separated(ctx, param, value):
    return value.split(',')


def status_code_range(start, end):
    return list(filter(lambda x: start <= x <= end, STATUS_CODES))


@click.command()
@click.argument('urls', nargs=-1)
@click.option('-x', '--exclude-flags', callback=comma_separated, help='Exclude results with these flags. See '
                                                                      'documentation.')
def hunt(urls, exclude):
    """

    :type exclude: list
    """
    for code in tuple(exclude):
        match = re.match('^(\d{3})-(\d{3})$', code)
        if match:
            exclude.remove(code)
            exclude += status_code_range(*map(int, match.groups()))
    crawler = Crawler()
    crawler.add_init_urls(*urls)
    crawler.print_results(set(exclude))
