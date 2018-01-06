import click as click

from dirhunt.crawler import Crawler


@click.command()
@click.argument('urls', nargs=-1)
def hunt(urls):
    crawler = Crawler()
    crawler.add_urls(*urls)
