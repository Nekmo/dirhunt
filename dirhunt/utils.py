import click
from click import Abort
from colorama import Fore, Back

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
