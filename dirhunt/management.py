import click as click
import time

from dirhunt.crawler import Crawler


@click.command()
@click.argument('urls', nargs=-1)
def hunt(urls):
    crawler = Crawler()
    crawler.add_urls(*urls)
    crawler.print_results()
