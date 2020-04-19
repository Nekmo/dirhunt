# -*- coding: utf-8 -*-
import re
import string

import click
import requests
from click import Abort
from colorama import Fore, Back
from requests import RequestException

from ._compat import urlparse


SCHEMES = ['http', 'https']
DEFAULT_SCHEME = 'http'
ARGUMENT_MULT = re.compile('(.+)\*(\d+)$')


def lrange(start, end):
    return list(range(start, end))


def colored(text, *colors):
    return ''.join(colors) + text + Fore.RESET + Back.RESET


def confirm_close():
    try:
        click.confirm(colored('\n\nDo you want to continue?', Fore.LIGHTRED_EX), abort=True)
    except (KeyboardInterrupt, Abort):
        raise SystemExit


def confirm_choices_close(choices, default_choice):
    choices_descriptions = ['  [{}]{}'.format(choice[0].upper() if default_choice == choice[0] else choice[0],
                                              choice[1:])
                            for choice in choices]
    choices_letters = [choice[0].upper() if default_choice == choice[0] else choice[0] for choice in choices]
    choice = click.prompt(colored('\n\nAn interrupt signal has been detected. what do you want to do?\n\n' +
                                  '\n'.join(choices_descriptions) +
                                  '\nEnter a choice [{}]'.format('/'.join(choices_letters)),
                                  Fore.LIGHTRED_EX), default=default_choice, show_default=False)
    if not next(iter(filter(lambda x: x == choice.lower(), map(lambda x: x.lower(), choices_letters))), None):
        return default_choice
    return choice.lower()


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


def catch_keyboard_interrupt_choices(fn, choices, default_choice):
    def wrap(*args, **kwargs):
        while True:
            try:
                return fn(*args, **kwargs)
            except KeyboardInterrupt:
                return confirm_choices_close(choices, default_choice)
    return wrap


def value_is_file_path(value):
    return value.startswith('/') or value.startswith('./')


def read_file_lines(file):
    lines = [line.rstrip('\n\r') for line in open(file).readlines()]
    return [line for line in lines if line]


def force_url(url):
    """Transform domain.com to http://domain.com

    Try the most common protocols until you get an answer.
    Check the destination url in case the server is
    redirecting the response to invalidate it.

    :type url: str
    """
    url = url.lstrip()
    if urlparse(url).scheme:
        return url
    if value_is_file_path(url):
        return [force_url(sub_url) for sub_url in read_file_lines(url)]
    for scheme in SCHEMES:
        new_url = '{}://{}'.format(scheme, url)
        try:
            r = requests.get(new_url, timeout=15, verify=False)
        except RequestException:
            continue
        if r.url.startswith('{}:'.format(scheme)):
            return new_url
    return '{}://{}'.format(DEFAULT_SCHEME, url)


def remove_ansi_escape(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def flat_list(values):
    items = []
    for value in values:
        if isinstance(value, (list, tuple)):
            items.extend(value)
        else:
            items.append(value)
    return items


def multiplier_arg(argument):
    matchs = ARGUMENT_MULT.match(argument)
    if matchs is None:
        return argument
    return [matchs.group(1)] * int(matchs.group(2))


def multiplier_args(arguments):
    return flat_list([multiplier_arg(argument) for argument in arguments])
