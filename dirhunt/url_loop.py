# -*- coding: utf-8 -*-

from dirhunt.url import Url

MATCHS_LOOP_NUM = 5


def is_url_loop(url, ignore_end=True):
    url = url if isinstance(url, Url) else Url(url)
    directories = list(filter(bool, url.directories))
    directories.reverse()
    for i in range(1, (len(directories) // MATCHS_LOOP_NUM) + 1):
        groups = [tuple(directories[j:j+i]) for j in range(0, MATCHS_LOOP_NUM * i, i)]
        if len(set(groups)) == 1 and len(groups) >= MATCHS_LOOP_NUM:
            return True
    if ignore_end:
        return is_url_loop(url.parent(), False)
    return False
