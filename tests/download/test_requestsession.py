import pytest
from responses import matchers
from wpextract.download import RequestSession
from wpextract.download.requestsession import (
    HTTPError404,
    HTTPError500,
    HTTPTooManyRedirects,
)


def test_request_session_get(mocked_responses):
    sess = RequestSession()
    mocked_responses.get("https://example.org", body="Example response")

    resp = sess.get("https://example.org")
    assert resp.text == "Example response"


def test_request_session_post(mocked_responses):
    sess = RequestSession()
    mocked_responses.post(
        "https://example.org",
        match=[matchers.urlencoded_params_matcher({"foo": "bar"})],
        body="Example response",
    )

    resp = sess.post("https://example.org", {"foo": "bar"})
    assert resp.text == "Example response"


def test_no_retry_404_error(mocked_responses):
    sess = RequestSession()
    mocked_responses.get("https://example.org", status=404)

    with pytest.raises(HTTPError404):
        sess.get("https://example.org")

    mocked_responses.assert_call_count("https://example.org", 1)


def test_no_retries(mocked_responses, caplog):
    sess_no_retries = RequestSession(max_retries=0)
    mocked_responses.get("https://example.org/a", status=500)

    with pytest.raises(HTTPError500):
        sess_no_retries.get("https://example.org/a")
    mocked_responses.assert_call_count("https://example.org/a", 1)


def test_retries(mocked_responses, caplog):
    sess_retries = RequestSession(max_retries=5)
    mocked_responses.get("https://example.org/b", status=500)

    with pytest.raises(HTTPError500):
        sess_retries.get("https://example.org/b")
    mocked_responses.assert_call_count("https://example.org/b", 6)


def test_timeout(mocked_responses):
    sess = RequestSession(timeout=1)
    mocked_responses.get(
        "https://example.org",
        body="Example response",
        match=[matchers.request_kwargs_matcher({"timeout": 1})],
    )

    sess.get("https://example.org")


@pytest.fixture()
def mocked_sleep(mocker):
    return mocker.patch("wpextract.download.requestsession.time.sleep")


def test_wait(mocked_responses, mocked_sleep):
    sess = RequestSession(wait=1)
    mocked_responses.get("https://example.org", body="Example response")

    sess.get("https://example.org")

    mocked_sleep.assert_called_once_with(1)


def test_rand_wait(mocked_responses, mocked_sleep):
    sess = RequestSession(wait=1, random_wait=True)
    mocked_responses.get("https://example.org", body="Example response")
    sess.get("https://example.org")

    mocked_sleep.assert_called_once()
    assert mocked_sleep.call_args[0][0] >= 0.5
    assert mocked_sleep.call_args[0][0] <= 1.5


def test_max_redirects(mocked_responses):
    for i in range(1, 5):
        mocked_responses.get(
            f"https://example.org/{i}",
            status=301,
            headers={"Location": f"https://example.org/{i+1}"},
        )

    sess = RequestSession(max_redirects=3)
    with pytest.raises(HTTPTooManyRedirects):
        sess.get("https://example.org/1")


def test_max_redirects_within_limit(mocked_responses):
    for i in range(1, 5):
        mocked_responses.get(
            f"https://example.org/{i}",
            status=301,
            headers={"Location": f"https://example.org/{i+1}"},
        )
    mocked_responses.get("https://example.org/5", body="Example response")
    sess = RequestSession(max_redirects=5)
    resp = sess.get("https://example.org/1")
    assert resp.status_code == 200
    assert resp.text == "Example response"
