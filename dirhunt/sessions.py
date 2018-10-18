import random
import threading
import warnings

from proxy_db.models import Proxy
from requests import Timeout
from requests.exceptions import ProxyError

from dirhunt._compat import Queue

import requests
from proxy_db.proxies import ProxiesList


MAX_NEGATIVE_VOTES = -3


def lock(fn):
    def wrap(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        finally:
            self.sessions.add_available(self)
    return wrap


def normalize_proxy(proxy, sessions):
    if proxy is not None and proxy.lower() == 'none':
        return None
    elif proxy is not None and proxy.lower() == 'tor':
        return 'socks5://127.0.0.1:9150'
    elif proxy is not None and proxy.startswith('~'):
        return sessions.proxies_lists[proxy].find_db_proxy()
    return proxy


class RandomProxies(object):
    def __init__(self):
        self.proxies_lists = {}

    def __getitem__(self, item):
        """

        :type item: str
        """
        item = item.lstrip('~')
        item = {'random': ''}.get(item, item).lower()
        if item not in self.proxies_lists:
            self.proxies_lists[item] = ProxiesList(item)
        return self.proxies_lists[item]


class Session(object):
    def __init__(self, sessions, proxy):
        self.sessions = sessions
        self.proxy_name = proxy
        self.proxy = normalize_proxy(self.proxy_name, sessions)
        self.session = requests.Session()

    @lock
    def get(self, url, **kwargs):
        is_proxy_db = False
        kw = kwargs.copy()
        if self.proxy and isinstance(self.proxy, Proxy):
            is_proxy_db = True
            kw['proxies'] = self.proxy
        elif self.proxy:
            kw['proxies'] = {
                'http': self.proxy,
                'https': self.proxy,
            }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                response = self.session.get(url, **kw)  # kwargs with proxies
            except (Timeout, ConnectionError, ProxyError):
                max_retries = kwargs.get('_max_retries', 3)
                if is_proxy_db and max_retries and self.proxy.get_updated_proxy().votes < MAX_NEGATIVE_VOTES:
                    # Use other random proxy (this proxy is down)
                    self.proxy = normalize_proxy(self.proxy_name, self.sessions)
                    max_retries -= 1
                    return self.get(url, _max_retries=max_retries, **kwargs)  # original kwargs
                else:
                    raise
        return response


class Sessions(object):
    def __init__(self, proxies=None, delay=0):
        self.availables = Queue()
        self.proxies_lists = RandomProxies()
        self.delay = delay
        self.sessions = self.create_sessions(proxies or [None])
        for session in self.sessions:
            self.availables.put(session)

    def add_available(self, session):
        if self.delay:
            threading.Timer(self.delay, self.availables.put, [session]).start()
        else:
            self.availables.put(session)

    def create_sessions(self, proxies):
        return [Session(self, proxy) for proxy in proxies]

    def get_random_session(self):
        return random.choice(self.sessions)

    def get_session(self):
        if not self.delay and self.availables.empty():
            return self.get_random_session()
        return self.availables.get()
