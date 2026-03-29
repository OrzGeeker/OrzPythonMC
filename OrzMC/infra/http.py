import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading

class HttpClient:
    def __init__(self, timeout = 10, retries = 3, backoff = 0.5, pool_connections = 32, pool_maxsize = 32):
        self.timeout = timeout
        retry = Retry(
            total = retries,
            connect = retries,
            read = retries,
            backoff_factor = backoff,
            status_forcelist = [429, 500, 502, 503, 504],
            allowed_methods = ["GET", "HEAD"]
        )
        self.adapter = HTTPAdapter(max_retries = retry, pool_connections = pool_connections, pool_maxsize = pool_maxsize)
        self.local = threading.local()

    def get(self, url, stream = False, headers = None, cookies = None):
        return self._session().get(url, stream = stream, timeout = self.timeout, headers = headers, cookies = cookies)

    def head(self, url, headers = None, cookies = None):
        return self._session().head(url, allow_redirects = True, timeout = self.timeout, headers = headers, cookies = cookies)

    def _session(self):
        sess = getattr(self.local, 'session', None)
        if sess:
            return sess
        sess = requests.Session()
        sess.mount("http://", self.adapter)
        sess.mount("https://", self.adapter)
        self.local.session = sess
        return sess
