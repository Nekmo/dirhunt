import socket
import ssl
import sys

from dirhunt.sources.base import Source


if sys.version_info < (3,):
    ConnectionError = socket.error


DEFAULT_SSL_PORT = 443


def get_url(protocol, domain, path):
    path = path.lstrip('/')
    return '{protocol}://{domain}/{path}'.format(**locals())



class CertificateSSL(Source):
    def callback(self, domain):
        ctx = ssl.create_default_context()
        cert = None
        try:
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.connect((domain, DEFAULT_SSL_PORT))
                cert = s.getpeercert()
        except (ConnectionError, ssl.SSLError, ValueError, socket.error):
            pass
        if cert is None:
            return
        alt_names = cert.get('subjectAltName') or ()
        for alt_name in alt_names:
            alt_name_domain = alt_name[1]
            if alt_name_domain.startswith('*.'):
                alt_name_domain = alt_name_domain.replace('.*', '', 1)
            self.add_result('https://{}/'.format(alt_name_domain))
