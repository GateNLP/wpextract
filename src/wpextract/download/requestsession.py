import logging
import random
import time
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Literal, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib3 import Retry

if TYPE_CHECKING:
    from requests.models import Response
    from requests.sessions import _Data as RequestDataType

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"


class ConnectionCouldNotResolve(Exception):
    """The remote host could not be resolved."""

    pass


class ConnectionReset(Exception):
    """The connection was reset during the request."""

    pass


class ConnectionRefused(Exception):
    """The connection was refused by the server."""

    pass


class ConnectionTimeout(Exception):
    """A connection timeout occurred."""

    pass


class HTTPError(Exception):
    """Base class for HTTP errors."""

    pass


class HTTPError400(HTTPError):
    """HTTP Bad Request.

    See Also:
        HTTPErrorInvalidPage for a special case of this error.
    """

    pass


class HTTPErrorInvalidPage(HTTPError):
    """Special case of HTTP 400 if the error is caused by a nonexistent page.

    This indicates the last page has been passed and all items have been retrieved.
    """

    pass


class HTTPError401(HTTPError):
    """HTTP Unauthorized."""

    pass


class HTTPError403(HTTPError):
    """HTTP Forbidden."""

    pass


class HTTPError404(HTTPError):
    """HTTP Not Found."""

    pass


class HTTPError500(HTTPError):
    """HTTP Internal Server Error."""

    pass


class HTTPError502(HTTPError):
    """HTTP Bad Gateway."""

    pass


class HTTPTooManyRedirects(Exception):
    """Raised if the number of allowed redirects exceeds the configured maximum value."""

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


def _handle_status(url: str, status_code: int, n_tries: Optional[int] = None) -> None:
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
    """Manages waiting between requests."""

    def __init__(
        self, wait: Optional[float] = None, random_wait: Optional[bool] = False
    ):
        """Create a new waiting instance.

        Args:
            wait: The base time to wait in seconds
            random_wait: If true, the wait duration will be multiplied by a random factor between 0.5 and 1.5.
        """
        self.wait_s = wait or 0
        self.random_wait = random_wait

    def wait(self) -> None:
        """Perform the specified wait."""
        if self.wait is None:
            return

        wait_factor = 1.0
        if self.random_wait:
            wait_factor = random.uniform(0.5, 1.5)

        time.sleep(self.wait_s * wait_factor)


AuthorizationType = Union[tuple[str, str], HTTPBasicAuth, HTTPDigestAuth]


class RequestSession:
    """Manages HTTP requests and their behaviour."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        cookies: Optional[str] = None,
        authorization: Optional[AuthorizationType] = None,
        timeout: Optional[float] = 30,
        wait: Optional[float] = None,
        random_wait: bool = False,
        max_retries: int = 10,
        backoff_factor: float = 0.1,
        max_redirects: int = 20,
        user_agent: Optional[str] = None,
    ):
        """Create a new request session.

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
            user_agent: User agent to use for requests. Set to [`DEFAULT_UA`][wpextract.download.requestsession.DEFAULT_UA] by default.
        """
        self.s = requests.Session()
        if proxy is not None:
            self.set_proxy(proxy)
        if cookies is not None:
            self.set_cookies(cookies)
        if authorization is not None and (
            (type(authorization) is tuple and len(authorization) == 2)
            or type(authorization) is HTTPBasicAuth
            or type(authorization) is HTTPDigestAuth
        ):
            self.s.auth = authorization
        self.wait = wait
        self.timeout = timeout
        self.s.max_redirects = max_redirects
        self._mount_retry(backoff_factor, max_retries)
        self.waiter = RequestWait(wait, random_wait)
        self.user_agent = user_agent if user_agent is not None else DEFAULT_UA

    def _mount_retry(self, backoff_factor: float, max_retries: int) -> None:
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=RETRY_AFTER_STATUS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.s.mount("http://", adapter)
        self.s.mount("https://", adapter)

    def get(self, url: str) -> "Response":
        """Calls the get function from requests but handles errors to raise proper exception following the context.

        Args:
            url: URL to fetch

        Returns:
            the Response object
        """
        return self.do_request("get", url)

    def post(self, url: str, data: Optional["RequestDataType"] = None) -> "Response":
        """Calls the post function from requests but handles errors to raise proper exception following the context.

        Args:
            url: URL to fetch
            data: optional data to send

        Returns:
            the Response object
        """
        return self.do_request("post", url, data)

    def do_request(
        self,
        method: Literal["get", "post"],
        url: str,
        data: Optional["RequestDataType"] = None,
        stream: bool = False,
    ) -> "Response":
        """Helper class to regroup requests and handle exceptions at the same location.

        Args:
            method: HTTP method to use
            url: URL to fetch
            data: optional data to send
            stream: if True, the response will be streamed

        Raises:
            ConnectionCouldNotResolve: The remote host could not be resolved.
            ConnectionRefused: The connection was refused by the server.
            ConnectionReset: The connection was reset during the request.
            ConnectionTimeout: Exceeded the configured timeout
            HTTPErrorInvalidPage: Special case of HTTP 400 if the error is caused by a nonexistent page.
                This usually signals that available pages have been exhausted.

        Returns:
            the Response object
        """
        headers = {"User-Agent": self.user_agent}
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
                logging.error(f"Could not resolve host {url}")
                raise ConnectionCouldNotResolve from e
            elif "Errno 111" in str(e):
                logging.error(f"Connection refused by {url}")
                raise ConnectionRefused from e
            elif "RemoteDisconnected" in str(e):
                logging.error(f"Connection reset by {url}")
                raise ConnectionReset from e
            else:
                raise e
        except requests.Timeout as e:
            logging.error(f"Request timed out fetching {url}")
            raise ConnectionTimeout from e
        except requests.TooManyRedirects as e:
            logging.error(f'Too many redirects while fetching "{url}"')
            raise HTTPTooManyRedirects from e

        # If this is an HTTP 400 due to an invalid page, raise this special error early
        if response.status_code == 400 and "application/json" in response.headers.get(
            "content-type", ""
        ):
            json_body = response.json()
            if "code" in json_body and "invalid_page_number" in json_body["code"]:
                raise HTTPErrorInvalidPage

        n_tries = None
        if hasattr(response.raw, "retries") and response.raw.retries is not None:
            # initial request + n retires = n+1 tries
            n_tries = len(response.raw.retries.history) + 1

        _handle_status(url, response.status_code, n_tries)

        self.waiter.wait()
        return response

    def set_cookies(self, cookies: str) -> None:
        """Sets new cookies from a string.

        Args:
            cookies: Cookies in a format usable by [http.cookies.SimpleCookie.load][]
        """
        c = SimpleCookie()
        c.load(cookies)
        for key, m in c.items():
            self.s.cookies.set(key, m.value)

    def get_cookies(self) -> dict[str, str]:
        """Retrieve cookies in the cookie jar.

        Returns:
            Cookies in dictionary format.
        """
        return self.s.cookies.get_dict()

    def set_proxy(self, proxy: str) -> None:
        """Set a proxy to use for the request.

        Args:
            proxy: proxy URL In the format supported by requests
        """
        prot = "http"
        if proxy[:5].lower() == "https":
            prot = "https"
        self.s.proxies = {prot: proxy}

    def set_creds(self, credentials: AuthorizationType) -> None:
        """Set new credentials for the request.

        Args:
            credentials: credentials as an HTTPBasic tuple or supported requests HTTP auth instance
        """
        self.s.auth = credentials
