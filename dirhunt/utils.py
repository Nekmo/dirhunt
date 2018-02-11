import click
import requests
from click import Abort
from colorama import Fore, Back
from requests import RequestException

from ._compat import urlparse


SCHEMES = ['http', 'https']
DEFAULT_SCHEME = 'http'


def lrange(start, end):
    return list(range(start, end))


def colored(text, *colors):
    return ''.join(colors) + text + Fore.RESET + Back.RESET


def confirm_close():
    try:
        click.confirm(colored('\n\nDo you want to continue?', Fore.LIGHTRED_EX), abort=True)
    except (KeyboardInterrupt, Abort):
        raise SystemExit


def catch_keyboard_interrupt(fn, restart=None):
    def wrap(*args, **kwargs):
        while True:
            try:
                return fn(*args, **kwargs)
            except KeyboardInterrupt:
                confirm_close()
            if restart:
                restart()
    return wrap


def force_url(url):
    """Transform domain.com to http://domain.com

    Try the most common protocols until you get an answer.
    Check the destination url in case the server is
    redirecting the response to invalidate it.
    """
    if urlparse(url).scheme:
        return url
    for scheme in SCHEMES:
        new_url = '{}://{}'.format(scheme, url)
        try:
            r = requests.get(new_url, timeout=15)
        except RequestException:
            continue
        if r.url.startswith('{}:'.format(scheme)):
            return new_url
    return '{}://{}'.format(DEFAULT_SCHEME, url)
