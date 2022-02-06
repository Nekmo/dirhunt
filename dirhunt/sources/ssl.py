import socket
import ssl

from dirhunt.sources.base import Source


def get_url(protocol, domain, path):
    path = path.lstrip('/')
    return '{protocol}://{domain}/{path}'.format(**locals())



class CertificateSSL(Source):
    def callback(self, domain):
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.connect((domain, 443))
            cert = s.getpeercert()
            alt_names = cert.get('subjectAltName') or ()
        for alt_name in alt_names:
            self.add_result('https://{}/'.format(alt_name[1]))
