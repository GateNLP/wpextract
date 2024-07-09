"""Copyright (c) 2018-2020 Mickaël "Kilawyn" Walter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import random
import time
from http.cookies import SimpleCookie
from typing import Tuple, Union

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib3 import Retry

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"


class ConnectionCouldNotResolve(Exception):
    pass


class ConnectionReset(Exception):
    pass


class ConnectionRefused(Exception):
    pass


class ConnectionTimeout(Exception):
    pass


class HTTPError400(Exception):
    pass


class HTTPErrorInvalidPage(Exception):
    pass


class HTTPError401(Exception):
    pass


class HTTPError403(Exception):
    pass


class HTTPError404(Exception):
    pass


class HTTPError500(Exception):
    pass


class HTTPError502(Exception):
    pass


class HTTPError(Exception):
    pass


class HTTPTooManyRedirects(Exception):
    pass


RETRY_AFTER_STATUS = frozenset(
    [
        # Standard HTTP
        413,  # Payload Too Large
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout,
        # Cloudflare
        520,  # Web Server Returned an Unknown Error
        522,  # Connection Timed Out
        524,  # A Timeout Occurred
    ]
)

ERROR_NAMES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
}
EXCEPTION_CLS = {
    400: HTTPError400,
    401: HTTPError401,
    403: HTTPError403,
    404: HTTPError404,
    500: HTTPError500,
    502: HTTPError502,
}


def _handle_status(url, status_code, n_tries=None):
    if 300 <= status_code < 400:
        logging.error(
            f'Too many redirects (status code {status_code}) while fetching "{url}"'
        )
        raise HTTPTooManyRedirects

    if status_code in ERROR_NAMES:
        log_msg = (
            f'Error {status_code} ({ERROR_NAMES[status_code]}) while fetching "{url}"'
        )
    else:
        log_msg = f'Error {status_code} while fetching "{url}"'

    if n_tries is not None:
        log_msg += f" after {n_tries} tries"

    if status_code in EXCEPTION_CLS or status_code > 400:
        if status_code == 404:
            logging.debug(log_msg)
        else:
            logging.error(log_msg)

        if status_code in EXCEPTION_CLS:
            raise EXCEPTION_CLS[status_code]
        else:
            raise HTTPError


class RequestWait:
    def __init__(self, wait: float = None, random_wait: bool = False):
        """Create a new waiting instance.

        Args:
            wait: The base time to wait in seconds
            random_wait: If true, the wait duration will be multiplied by a random factor between 0.5 and 1.5.
        """
        self.wait_s = wait or 0
        self.random_wait = random_wait

    def wait(self):
        """Perform the specified wait."""
        if self.wait is None:
            return

        wait_factor = 1
        if self.random_wait:
            wait_factor = random.uniform(0.5, 1.5)

        time.sleep(self.wait_s * wait_factor)


AuthorizationType = Union[Tuple[str, str], HTTPBasicAuth, HTTPDigestAuth]


class RequestSession:
    """Wrapper to handle the requests library with session support"""

    def __init__(
        self,
        proxy: str = None,
        cookies: str = None,
        authorization: AuthorizationType = None,
        timeout: float = 30,
        wait: float = None,
        random_wait: bool = False,
        max_retries: int = 10,
        backoff_factor: float = 0.1,
        max_redirects: int = 20,
    ):
        """Creates a new RequestSession instance

        Args:
            proxy: a dict containing a proxy server string for HTTP and/or HTTPS connection
            cookies: a string in the format of the Cookie header
            authorization: a tuple containing login and password or [`requests.auth.HTTPBasicAuth`][requests.auth.HTTPBasicAuth] for basic authentication or [`requests.auth.HTTPDigestAuth`][requests.auth.HTTPDigestAuth] for NTLM-like authentication
            timeout: maximum time in seconds to wait for a response before giving up
            wait: wait time in seconds between requests, None to not wait
            random_wait: If true, the wait time between requests is multiplied by a random factor between 0.5 and 1.5
            max_retries: the maximum number of retries before failing
            backoff_factor: Factor to wait between successive retries
            max_redirects: maximum number of redirects to follow
        """
        self.s = requests.Session()
        if proxy is not None:
            self.set_proxy(proxy)
        if cookies is not None:
            self.set_cookies(cookies)
        if authorization is not None and (
            type(authorization) is tuple
            and len(authorization) == 2
            or type(authorization) is HTTPBasicAuth
            or type(authorization) is HTTPDigestAuth
        ):
            self.s.auth = authorization
        self.wait = wait
        self.timeout = timeout
        self._mount_retry(backoff_factor, max_redirects, max_retries)
        self.waiter = RequestWait(wait, random_wait)

    def _mount_retry(self, backoff_factor, max_redirects, max_retries):
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            redirect=max_redirects,
            status_forcelist=RETRY_AFTER_STATUS,
            raise_on_redirect=False,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.s.mount("http://", adapter)
        self.s.mount("https://", adapter)

    def get(self, url):
        """Calls the get function from requests but handles errors to raise proper exception following the context."""
        return self.do_request("get", url)

    def post(self, url, data=None):
        """Calls the post function from requests but handles errors to raise proper exception following the context."""
        return self.do_request("post", url, data)

    def do_request(self, method, url, data=None, stream=False):
        """Helper class to regroup requests and handle exceptions at the same location."""
        headers = {"User-Agent": DEFAULT_UA}
        response = None
        try:
            if method == "post":
                response = self.s.post(url, data, headers=headers, timeout=self.timeout)
            else:
                response = self.s.get(
                    url, headers=headers, timeout=self.timeout, stream=stream
                )
        except requests.ConnectionError as e:
            if "Errno -5" in str(e) or "Errno -2" in str(e) or "Errno -3" in str(e):
                logging.error("Could not resolve host %s" % url)
                raise ConnectionCouldNotResolve from e
            elif "Errno 111" in str(e):
                logging.error("Connection refused by %s" % url)
                raise ConnectionRefused from e
            elif "RemoteDisconnected" in str(e):
                logging.error("Connection reset by %s" % url)
                raise ConnectionReset from e
            else:
                print(e)
                raise e
        except requests.Timeout as e:
            logging.error(f"Request timed out fetching {url}")
            raise ConnectionTimeout from e

        # If this is an HTTP 400 due to an invalid page, raise this special error early
        if response.status_code == 400 and "application/json" in response.headers.get(
            "content-type", ""
        ):
            json_body = response.json()
            if "code" in json_body and "invalid_page_number" in json_body["code"]:
                logging.debug(
                    "Received HTTP 400 error which appears to be an invalid page error, probably reached the end."
                )
                raise HTTPErrorInvalidPage

        n_tries = None
        if hasattr(response.raw, "retries"):
            # initial request + n retires = n+1 tries
            n_tries = len(response.raw.retries.history) + 1

        _handle_status(url, response.status_code, n_tries)

        self.waiter.wait()
        return response

    def set_cookies(self, cookies):
        """Sets new cookies from a string"""
        c = SimpleCookie()
        c.load(cookies)
        for key, m in c.items():
            self.s.cookies.set(key, m.value)

    def get_cookies(self):  # noqa: D102
        return self.s.cookies.get_dict()

    def set_proxy(self, proxy):  # noqa: D102
        prot = "http"
        if proxy[:5].lower() == "https":
            prot = "https"
        self.s.proxies = {prot: proxy}

    def get_proxies(self):  # noqa: D102
        return self.s.proxies

    def set_creds(self, credentials):  # noqa: D102
        self.s.auth = credentials

    def get_creds(self):  # noqa: D102
        return self.s.auth
