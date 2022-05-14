from requests.exceptions import RequestException
from dirhunt.sessions import Sessions
from dirhunt.sources.base import Source


CRTSH_URL = 'https://crt.sh/'
TIMEOUT = 10


class CrtSh(Source):

    def callback(self, domain):
        session = Sessions().get_session()
        try:
            with session.get(CRTSH_URL, params={'q': domain, 'output': 'json'},
                             timeout=TIMEOUT, stream=True) as response:
                response.raise_for_status()
                certs = response.json()
                common_names = {cert['common_name'] for cert in certs}
                for common_name in common_names:
                    self.add_result('https://{}/'.format(common_name))
        except RequestException:
            return
