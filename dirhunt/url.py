from ipaddress import ip_address
from urllib.parse import urlparse

import os


class Url(object):
    _urlparsed = None

    def __init__(self, address):
        self.address = address

    def is_ip(self):
        try:
            ip_address(self.only_domain)
        except ValueError:
            return False
        else:
            return True

    @property
    def urlparsed(self):
        if not self._urlparsed:
            self._urlparsed = urlparse(self.address)
            self._urlparsed = list(self._urlparsed) if self._urlparsed.scheme and self._urlparsed.netloc else None
        return self._urlparsed

    @property
    def protocol_domain(self):
        return '://'.join(self.urlparsed[:2])

    @property
    def protocol(self):
        return self.urlparsed[0] if self.urlparsed else None

    @property
    def is_absolute(self):
        """Si es sólo un path o una dirección entera
        """
        return bool(self.urlparsed.netloc) if self.urlparsed else False

    @property
    def domain_port(self):
        """Dominio con el puerto si lo hay
        """
        netloc = getattr(self.urlparsed, 'netloc', '')
        return netloc.split('@', 1)[-1] or None

    @property
    def only_domain(self):
        """Dominio sin el puerto
        """
        return (self.domain_port or '').split(':')[0] or None

    @property
    def domain(self):
        return self.only_domain

    @property
    def port(self):
        if not self.domain_port or ':' not in self.domain_port:
            return {'http': 80, 'https': 443}.get(self.protocol)
        else:
            return int(self.domain_port.split(':')[-1])

    @property
    def full_path(self):
        path = self.urlparsed[2] or '/'
        path += (';' if self.urlparsed[3] else '') + self.urlparsed[3]
        path += ('?' if self.urlparsed[4] else '') + self.urlparsed[4]
        path += ('#' if self.urlparsed[5] else '') + self.urlparsed[5]
        return path

    @property
    def path(self):
        return self.urlparsed[2]

    @path.setter
    def path(self, new_value):
        """

        :type new_value: str
        """
        # TODO: abs path para urls ../../
        if not new_value.startswith('/'):
            new_value = self.directory_path + new_value
        self.urlparsed[2] = new_value

    @property
    def directory_path(self):
        if self.path.endswith('/'):
            return self.path
        return os.path.dirname(self.path)[0]

    @property
    def url(self):
        return self.urlparsed[0] + '://' + self.urlparsed[1] + self.full_path

    @property
    def query(self):
        return self.urlparsed[4]

    @query.setter
    def query(self, new_value):
        self.urlparsed[4] = new_value

    @property
    def fragment(self):
        return self.urlparsed[5]

    @fragment.setter
    def fragment(self, new_value):
        self.urlparsed[5] = new_value

    def breadcrumb(self):
        directories = self.urlparsed[2].split('/')
        for level in range(len(directories)):
            url = self.copy()
            url.path = '/'.join(directories[:level]) + '/'
            yield url

    def copy(self):
        return Url(self.url)

    def json(self):
        return {
            'address': self.address,
            'domain': self.domain,
        }

    def __str__(self):
        return '<Url {}>'.format(self.url)
