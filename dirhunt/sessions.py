import random
import threading
import warnings
from queue import Queue

import requests


def lock(fn):
    def wrap(self: 'Session', *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        finally:
            self.sessions.add_available(self)
    return wrap


class Session(object):
    def __init__(self, sessions, proxy):
        self.sessions = sessions
        self.proxy = proxy
        self.session = requests.Session()

    @lock
    def get(self, url, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = self.session.get(url, **kwargs)
        return response


class Sessions(object):
    def __init__(self, proxies=None, delay: float=0):
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
