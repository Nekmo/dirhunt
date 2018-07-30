import warnings
import requests


class Session(object):
    def __init__(self, sessions):
        self.sessions = sessions
        self.session = requests.Session()

    def get(self, url, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = self.session.get(url, **kwargs)
        self.sessions.availables.add(self)
        return response


class Sessions(object):
    def __init__(self):
        self.availables = set()

    def get_session(self):
        if not self.availables:
            return self.create_session()
        # self.availables.pop()
        # Get a element without remove until slots available
        return next(iter(self.availables))

    def create_session(self):
        return Session(self)
