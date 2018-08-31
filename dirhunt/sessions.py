import random
import threading
import warnings
from dirhunt._compat import Queue

import requests


def lock(fn):
    def wrap(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        finally:
            self.sessions.add_available(self)
    return wrap


def normalize_proxy(proxy):
    if proxy is not None and proxy.lower() == 'none':
        return None
    elif proxy is not None and proxy.lower() == 'tor':
        return 'socks5://127.0.0.1:9150'
    return proxy


class Session(object):
    def __init__(self, sessions, proxy):
        self.sessions = sessions
        self.proxy = normalize_proxy(proxy)
        self.session = requests.Session()

    @lock
    def get(self, url, **kwargs):
        if self.proxy:
            kwargs['proxies'] = {
                'http': self.proxy,
                'https': self.proxy,
            }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = self.session.get(url, **kwargs)
        return response


class Sessions(object):
    def __init__(self, proxies=None, delay=0):
        self.availables = Queue()
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
