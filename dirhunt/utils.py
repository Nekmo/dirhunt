from colorama import Fore, Back


def lrange(start, end):
    return list(range(start, end))


def colored(text, *colors):
    return ''.join(colors) + text + Fore.RESET + Back.RESET
