# -*- coding: utf-8 -*-

from __future__ import print_function

import multiprocessing
import re
import click as click
import os

import sys

from click import BadOptionUsage

from dirhunt.crawler import Crawler
from dirhunt.exceptions import DirHuntError
from dirhunt.output import output_urls
from dirhunt.sources import SOURCE_CLASSES, get_source_name
from dirhunt.utils import lrange, catch_keyboard_interrupt, force_url
from colorama import init

init(autoreset=True)

STATUS_CODES = lrange(100, 102+1) + lrange(200, 208+1) + [226] + lrange(300, 308+1) + lrange(400, 418+1) + \
               lrange(421, 426+1) + [428, 429, 431, 451] + lrange(500, 511+1)
INTERESTING_EXTS = ['php', 'zip', 'sh', 'asp', 'csv', 'log']
INTERESTING_FILES = ['access_log', 'error_log', 'error', 'logs', 'dump']
STDOUT_FLAGS = ['blank', 'not_found.fake', 'html']


def latest_release(package):
    if sys.version_info > (3,):
        from xmlrpc import client
    else:
        import xmlrpclib as client
    pypi = client.ServerProxy('https://pypi.python.org/pypi')
    available = pypi.package_releases(package)
    if not available:
        # Try to capitalize pkg name
        available = pypi.package_releases(package.capitalize())
    if not available:
        return
    return available[0]


def comma_separated(ctx, param, value):
    return (value).split(',') if value else []


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


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    import dirhunt
    from dirhunt import __version__
    latest = latest_release('dirhunt')
    release = ('This is the latest release' if latest == __version__
               else 'There is a new version available: {}. Upgrade it using: '
                    'sudo pip install -U dirhunt'.format(latest))
    click.echo('You are running Dirhunt v{} using Python {}.\n{}\n'
               'Installation path: {}\n'
               'Current path: {}\n'.format(
        __version__, sys.version.split()[0], release, os.path.dirname(dirhunt.__file__), os.getcwd()
    ))
    ctx.exit()


def welcome():
    from dirhunt import __version__
    click.secho('Welcome to Dirhunt v{} using Python {}'.format(__version__, sys.version.split()[0]),
                fg='cyan')


def flags_range(flags):
    for code in tuple(flags):
        match = re.match('^(\d{3})-(\d{3})$', code)
        if match:
            flags.remove(code)
            flags += list(map(str, status_code_range(*map(int, match.groups()))))
    return flags



@click.command()
@click.argument('urls', nargs=-1, type=force_url)
@click.option('-t', '--threads', type=int, default=(multiprocessing.cpu_count() or 1) * 5,
              help='Number of threads to use.')
@click.option('-x', '--exclude-flags', callback=comma_separated_files,
              help='Exclude results with these flags. See documentation.')
@click.option('-i', '--include-flags', callback=comma_separated_files,
              help='Only include results with these flags. See documentation.')
@click.option('-e', '--interesting-extensions', callback=comma_separated_files, default=','.join(INTERESTING_EXTS),
              help='The files found with these extensions are interesting')
@click.option('-f', '--interesting-files', callback=comma_separated_files, default=','.join(INTERESTING_FILES),
              help='The files with these names are interesting')
@click.option('--stdout-flags', callback=comma_separated_files, default=','.join(STDOUT_FLAGS),
              help='Return only in stdout the urls of these flags')
@click.option('--progress-enabled/--progress-disabled', default=None)
@click.option('--timeout', default=10)
@click.option('--max-depth', default=3, help='Maximum links to follow without increasing directories depth')
@click.option('--not-follow-subdomains', is_flag=True, help='The subdomains will be ignored')
@click.option('--exclude-sources', callback=comma_separated_files,
              help='Exclude source engines. Possible options: {}'.format(', '.join(
                  [get_source_name(src) for src in SOURCE_CLASSES])
              ))
@click.option('--not-allow-redirects', is_flag=True, help='Redirectors will not be followed')
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def hunt(urls, threads, exclude_flags, include_flags, interesting_extensions, interesting_files, stdout_flags,
         progress_enabled, timeout, max_depth, not_follow_subdomains, exclude_sources, not_allow_redirects):
    """Find web directories without bruteforce
    """
    if exclude_flags and include_flags:
        raise BadOptionUsage('--exclude-flags and --include-flags are mutually exclusive.')
    welcome()
    if not urls:
        click.echo('•_•) OOPS! Add urls to analyze.\nFor example: dirhunt http://domain/path\n\n'
                   'Need help? Then use dirhunt --help', err=True)
        return
    exclude_flags, include_flags = flags_range(exclude_flags), flags_range(include_flags)
    progress_enabled = (sys.stdout.isatty() or sys.stderr.isatty()) if progress_enabled is None else progress_enabled
    crawler = Crawler(max_workers=threads, interesting_extensions=interesting_extensions,
                      interesting_files=interesting_files, std=sys.stdout if sys.stdout.isatty() else sys.stderr,
                      progress_enabled=progress_enabled, timeout=timeout, depth=max_depth,
                      not_follow_subdomains=not_follow_subdomains, exclude_sources=exclude_sources,
                      not_allow_redirects=not_allow_redirects)
    crawler.add_init_urls(*urls)
    try:
        catch_keyboard_interrupt(crawler.print_results, crawler.restart)(set(exclude_flags), set(include_flags))
    except SystemExit:
        crawler.close()
    crawler.print_urls_info()
    if not sys.stdout.isatty():
        output_urls(crawler, stdout_flags)
