# -*- coding: utf-8 -*-
from ipaddress import ip_address
from dirhunt._compat import urlparse, urljoin

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

    def is_valid(self):
        return self.urlparsed and self.urlparsed[0] and self.urlparsed[1]

    @property
    def urlparsed(self):
        address = self.address
        if isinstance(address, Url):
            address = address.url
        if not self._urlparsed:
            self._urlparsed = urlparse(address)
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
        if not self.urlparsed:
            return
        netloc = self.urlparsed[1]
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
    def directories(self):
        return self.path.split('/')

    @property
    def full_path(self):
        path = self.urlparsed[2] or '/'
        path += (';' if self.urlparsed[3] else '') + self.urlparsed[3]
        path += ('?' if self.urlparsed[4] else '') + self.urlparsed[4]
        path += ('#' if self.urlparsed[5] else '') + self.urlparsed[5]
        return path

    @property
    def path(self):
        return self.urlparsed[2] if self.urlparsed else ''

    def set_children(self, children):
        self.path = children

    @path.setter
    def path(self, new_value):
        """

        :type new_value: str
        """
        for symbol, i in [('#', 5), ('?', 4), (';', 3)]:
            if not symbol in new_value:
                continue
            new_value, self.urlparsed[i] = new_value.split(symbol, 1)
        new_value = new_value.replace('//', '/')
        self.urlparsed[2] = urljoin(self.path, new_value)

    @property
    def directory_path(self):
        if self.path.endswith('/'):
            return self.path
        if not self.path:
            return '/'
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

    # def is_valid(self):
    #     return bool(self.urlparsed)

    @property
    def fragment(self):
        return self.urlparsed[5]

    @fragment.setter
    def fragment(self, new_value):
        self.urlparsed[5] = new_value

    @property
    def name(self):
        path = self.urlparsed[2] or '/'
        path += (';' if self.urlparsed[3] else '') + self.urlparsed[3]
        return path.split('/')[-1]

    def breadcrumb(self):
        if self.urlparsed[2] == '/':
            directories = ['']
        else:
            directories = self.urlparsed[2].split('/')
        for level in range(len(directories)):
            url = self.copy()
            url.path = '/'.join(directories[:level]) + '/'
            yield url

    def parent(self):
        url = self.copy()
        url.path = url.path[:-1]
        return url

    def copy(self):
        return Url(self.url)

    def json(self):
        return {
            'address': self.address,
            'domain': self.domain,
        }

    def __eq__(self, other):
        if isinstance(other, Url):
            other = other.url
        return self.url == other

    def __str__(self):
        return '<Url {}>'.format(self.url)
