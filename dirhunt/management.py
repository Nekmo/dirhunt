import click as click
import time

from dirhunt.crawler import Crawler


@click.command()
@click.argument('urls', nargs=-1)
def hunt(urls):
    crawler = Crawler()
    crawler.add_urls(*urls)
    time.sleep(100000)
