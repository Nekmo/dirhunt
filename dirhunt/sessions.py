import random
import sys
import threading
import warnings

from aiohttp import ClientSession
from multidict import CIMultiDict
from requests import Timeout
from requests.adapters import HTTPAdapter
from requests.exceptions import ProxyError
from typing_extensions import TYPE_CHECKING

from dirhunt._compat import Queue

import requests
from proxy_db.proxies import ProxiesList
from proxy_db.models import Proxy

from dirhunt.agents import get_random_user_agent


if TYPE_CHECKING:
    from dirhunt.crawler import Crawler


MAX_NEGATIVE_VOTES = -3
# https://dev.maxmind.com/geoip/legacy/codes/iso3166/
COUNTRIES = [
    "a1",
    "a2",
    "o1",
    "ad",
    "ae",
    "af",
    "ag",
    "ai",
    "al",
    "am",
    "ao",
    "ap",
    "aq",
    "ar",
    "as",
    "at",
    "au",
    "aw",
    "ax",
    "az",
    "ba",
    "bb",
    "bd",
    "be",
    "bf",
    "bg",
    "bh",
    "bi",
    "bj",
    "bl",
    "bm",
    "bn",
    "bo",
    "bq",
    "br",
    "bs",
    "bt",
    "bv",
    "bw",
    "by",
    "bz",
    "ca",
    "cc",
    "cd",
    "cf",
    "cg",
    "ch",
    "ci",
    "ck",
    "cl",
    "cm",
    "cn",
    "co",
    "cr",
    "cu",
    "cv",
    "cw",
    "cx",
    "cy",
    "cz",
    "de",
    "dj",
    "dk",
    "dm",
    "do",
    "dz",
    "ec",
    "ee",
    "eg",
    "eh",
    "er",
    "es",
    "et",
    "eu",
    "fi",
    "fj",
    "fk",
    "fm",
    "fo",
    "fr",
    "ga",
    "gb",
    "gd",
    "ge",
    "gf",
    "gg",
    "gh",
    "gi",
    "gl",
    "gm",
    "gn",
    "gp",
    "gq",
    "gr",
    "gs",
    "gt",
    "gu",
    "gw",
    "gy",
    "hk",
    "hm",
    "hn",
    "hr",
    "ht",
    "hu",
    "id",
    "ie",
    "il",
    "im",
    "in",
    "io",
    "iq",
    "ir",
    "is",
    "it",
    "je",
    "jm",
    "jo",
    "jp",
    "ke",
    "kg",
    "kh",
    "ki",
    "km",
    "kn",
    "kp",
    "kr",
    "kw",
    "ky",
    "kz",
    "la",
    "lb",
    "lc",
    "li",
    "lk",
    "lr",
    "ls",
    "lt",
    "lu",
    "lv",
    "ly",
    "ma",
    "mc",
    "md",
    "me",
    "mf",
    "mg",
    "mh",
    "mk",
    "ml",
    "mm",
    "mn",
    "mo",
    "mp",
    "mq",
    "mr",
    "ms",
    "mt",
    "mu",
    "mv",
    "mw",
    "mx",
    "my",
    "mz",
    "na",
    "nc",
    "ne",
    "nf",
    "ng",
    "ni",
    "nl",
    "no",
    "np",
    "nr",
    "nu",
    "nz",
    "om",
    "pa",
    "pe",
    "pf",
    "pg",
    "ph",
    "pk",
    "pl",
    "pm",
    "pn",
    "pr",
    "ps",
    "pt",
    "pw",
    "py",
    "qa",
    "re",
    "ro",
    "rs",
    "ru",
    "rw",
    "sa",
    "sb",
    "sc",
    "sd",
    "se",
    "sg",
    "sh",
    "si",
    "sj",
    "sk",
    "sl",
    "sm",
    "sn",
    "so",
    "sr",
    "ss",
    "st",
    "sv",
    "sx",
    "sy",
    "sz",
    "tc",
    "td",
    "tf",
    "tg",
    "th",
    "tj",
    "tk",
    "tl",
    "tm",
    "tn",
    "to",
    "tr",
    "tt",
    "tv",
    "tw",
    "tz",
    "ua",
    "ug",
    "um",
    "us",
    "uy",
    "uz",
    "va",
    "vc",
    "ve",
    "vg",
    "vi",
    "vn",
    "vu",
    "wf",
    "ws",
    "ye",
    "yt",
    "za",
    "zm",
    "zw",
] + ["random"]
POOL_CONNECTIONS = 40


def lock(fn):
    def wrap(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        finally:
            self.sessions.add_available(self)

    return wrap


def normalize_proxy(proxy, sessions):
    if proxy is not None and proxy.lower() == "none":
        return None
    elif proxy is not None and proxy.lower() == "tor":
        return "socks5://127.0.0.1:9150"
    elif proxy is not None and proxy.lower() in COUNTRIES:
        return next(sessions.proxies_lists[proxy], None)
    return proxy


class RandomProxies(object):
    def __init__(self):
        self.proxies_lists = {}

    def __getitem__(self, item):
        """

        :type item: str
        """
        item = item.lower()
        item = {"random": ""}.get(item, item)
        if item not in self.proxies_lists:
            self.proxies_lists[item] = ProxiesList(item or None)
        return self.proxies_lists[item]


class Session(ClientSession):
    def __init__(self, crawler: "Crawler", **kwargs):
        headers = kwargs.pop("headers", {})
        headers = CIMultiDict(headers)
        if "User-Agent" not in headers:
            headers["User-Agent"] = (
                crawler.configuration.user_agent or get_random_user_agent()
            )
        super().__init__(headers=headers, **kwargs)


class Sessions(object):
    def __init__(
        self, proxies=None, delay=0, user_agent=None, cookies=None, headers=None
    ):
        self.availables = Queue()
        self.proxies_lists = RandomProxies()
        self.delay = delay
        self.user_agent = user_agent
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.sessions = self.create_sessions(proxies or [None])
        for session in self.sessions:
            self.availables.put(session)

    def add_available(self, session):
        if self.delay:
            threading.Timer(self.delay, self.availables.put, [session]).start()
        else:
            self.availables.put(session)

    def create_sessions(self, proxies):
        return [
            Session(self, proxy, self.user_agent, self.cookies, self.headers)
            for proxy in proxies
        ]

    def get_random_session(self):
        return random.choice(self.sessions)

    def get_session(self):
        if not self.delay and self.availables.empty():
            return self.get_random_session()
        return self.availables.get()
