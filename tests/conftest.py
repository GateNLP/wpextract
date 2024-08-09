import pytest
from urllib3 import HTTPConnectionPool


@pytest.fixture(autouse=True)
def _no_http_requests(monkeypatch):
    allowed_hosts = {"localhost"}
    original_urlopen = HTTPConnectionPool.urlopen

    def urlopen_mock(self, method, url, *args, **kwargs):
        if self.host in allowed_hosts:
            return original_urlopen(self, method, url, *args, **kwargs)

        raise RuntimeError(
            f"The test was about to {method} {self.scheme}://{self.host}{url}"
        )

    monkeypatch.setattr(
        "urllib3.connectionpool.HTTPConnectionPool.urlopen", urlopen_mock
    )
