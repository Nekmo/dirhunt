from dirhunt.sources.commoncrawl import CommonCrawl
from dirhunt.sources.crtsh import CrtSh
from dirhunt.sources.google import Google
from dirhunt.sources.robots import Robots
from dirhunt.sources.ssl import CertificateSSL
from dirhunt.sources.virustotal import VirusTotal
from dirhunt.sources.wayback import Wayback

SOURCE_CLASSES = [
    Robots,
    VirusTotal,
    Google,
    CommonCrawl,
    CrtSh,
    CertificateSSL,
    Wayback,
]


def get_source_name(cls):
    return cls.__name__.lower()


class Sources(object):

    def __init__(self, callback, error_callback, excluded_sources=()):
        self.callback = callback
        self.error_callback = error_callback
        self.sources = [cls(self.callback, error_callback)
                        for cls in SOURCE_CLASSES if get_source_name(cls) not in excluded_sources]

    def add_domain(self, domain):
        for source in self.sources:
            source.add_domain(domain)

    def finished(self):
        for source in self.sources:
            if source.is_running():
                return False
        return True
