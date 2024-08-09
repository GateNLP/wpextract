import pytest
import responses


@pytest.fixture()
def mock_request_session(mocker):
    mock_session_cls = mocker.patch("wpextract.downloader.RequestSession")
    mock_session_cls = mock_session_cls.return_value
    return mock_session_cls


@pytest.fixture()
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def mocked_responses_optional():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
