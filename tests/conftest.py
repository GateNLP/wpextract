import pytest
import responses
from click.testing import CliRunner
from urllib3 import HTTPConnectionPool


@pytest.fixture(autouse=True)
def _no_http_requests(monkeypatch):
    allowed_hosts = {}
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


@pytest.fixture()
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture()
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def mocked_responses_optional():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
