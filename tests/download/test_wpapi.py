import json

import pytest
from responses import matchers
from wpextract.download.exceptions import NoWordpressApi
from wpextract.download.wpapi import WPApi

FAKE_TARGET = "https://example.org"


def _get_page_url(p, datatype="posts", add_per_page=False):
    return f"{FAKE_TARGET}/wp-json/wp/v2/{datatype}?page={p}"


def _fake_api_page(page=1, per_page=10):
    assert page > 0
    return [
        {"id": idx + (page - 1) * per_page, "title": "dummy return"}
        for idx in range(1, per_page + 1)
    ]


no_more_pages_body = {
    "code": "rest_post_invalid_page_number",
    "message": "The page number requested is larger than the number of pages available.",
    "data": {"status": 400},
}


def test_api_page_fake():
    pg1 = _fake_api_page(1)
    assert pg1[0]["id"] == 1
    assert pg1[9]["id"] == 10

    pg2 = _fake_api_page(2)
    assert pg2[0]["id"] == 11
    assert pg2[9]["id"] == 20

    with pytest.raises(AssertionError):
        _fake_api_page(0)


class TestBasicInfo:
    @pytest.fixture()
    def mock_api_root(self, datadir):
        return json.loads((datadir / "api_root.json").read_text())

    def test_happy(self, mock_api_root, mocked_responses):
        mocked_responses.get(f"{FAKE_TARGET}/wp-json", json=mock_api_root)
        wpapi = WPApi(target=FAKE_TARGET)
        wpapi.get_basic_info()

        assert wpapi.name == "Example WordPress Site"
        assert wpapi.description == "Just another WordPress site"
        assert wpapi.has_v2 is True

    def test_nov2(self, mock_api_root, mocked_responses):
        mock_api_root["namespaces"].remove("wp/v2")
        mocked_responses.get(f"{FAKE_TARGET}/wp-json", json=mock_api_root)
        wpapi = WPApi(target=FAKE_TARGET)
        wpapi.get_basic_info()

        assert wpapi.has_v2 is None

    @pytest.mark.parametrize("err_code", [403, 404, 500])
    def test_error(self, mocked_responses, err_code):
        mocked_responses.get(f"{FAKE_TARGET}/wp-json", status=err_code)
        wpapi = WPApi(target=FAKE_TARGET)
        with pytest.raises(NoWordpressApi):
            wpapi.get_basic_info()

    def test_str_response(self, mocked_responses):
        mocked_responses.get(f"{FAKE_TARGET}/wp-json", body="Not a JSON")
        wpapi = WPApi(target=FAKE_TARGET)
        with pytest.raises(NoWordpressApi):
            wpapi.get_basic_info()


POSTS_API_PATH = "wp/v2/posts?page=%d"


def _assert_none_called(*resps):
    assert all([resp.call_count == 0 for resp in resps])


def _assert_all_called(*resps):
    assert all([resp.call_count == 1 for resp in resps])


class TestCrawl:
    @pytest.fixture()
    def mock_optional_3_pages_with_per_page(self, mocked_responses_optional):
        return self._mock_n_pages(mocked_responses_optional, n=3, with_per_page=True)

    @pytest.fixture()
    def mock_3_pages(self, mocked_responses):
        return self._mock_n_pages(mocked_responses, n=3, with_per_page=False)

    @pytest.fixture()
    def mock_optional_3_pages(self, mocked_responses_optional):
        return self._mock_n_pages(mocked_responses_optional, n=3, with_per_page=False)

    @pytest.fixture()
    def mock_optional_1_page_with_per_page(self, mocked_responses_optional):
        return self._mock_n_pages(mocked_responses_optional, n=1, with_per_page=True)

    def _mock_n_pages(self, responses, n, with_per_page):
        headers = {"X-WP-Total": "30", "X-WP-TotalPages": "3"}
        endpoint = f"{FAKE_TARGET}/wp-json/wp/v2/posts"

        resps = []

        for i in range(1, n + 1):
            params = {"page": str(i)}
            if with_per_page:
                params["per_page"] = "10"

            resps.append(
                responses.get(
                    endpoint,
                    match=[matchers.query_param_matcher(params)],
                    json=_fake_api_page(i),
                    headers=headers,
                )
            )

        params = {"page": str(n + 1)}
        if with_per_page:
            params["per_page"] = "10"

        resps.append(
            responses.get(
                endpoint,
                match=[matchers.query_param_matcher(params)],
                status=400,
                json=no_more_pages_body,
            )
        )

        return resps

    @pytest.fixture()
    def wpapi(self):
        return WPApi(target=FAKE_TARGET)

    def _assert_ids(self, entries, min_id, max_id):
        entry_ids = [entry["id"] for entry in entries]
        assert entry_ids == list(range(min_id, max_id + 1))

    def test_3_page_crawl(self, wpapi, mock_3_pages):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH)

        self._assert_ids(entries, 1, 30)
        assert total_entries == 30

    def test_start_page_2(self, wpapi, mock_optional_3_pages_with_per_page):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, start=11)
        self._assert_ids(entries, 11, 30)

        resps = mock_optional_3_pages_with_per_page
        _assert_none_called(resps[0])
        _assert_all_called(*resps[1:-1])
        # Should finish due to max num reached rather than going off the end
        _assert_none_called(resps[-1])

    def test_start_beyond_last(self, wpapi, mock_optional_3_pages_with_per_page):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, start=31)
        assert entries == []
        assert total_entries == 0

        resps = mock_optional_3_pages_with_per_page
        _assert_none_called(*resps[:-1])
        # Should call page 4 resulting in an error
        _assert_all_called(resps[-1])
        # and not attempt to call a 5th page (which would trigger a URL not matched error)

    def test_limit(self, wpapi, mock_optional_3_pages):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, num=15)
        assert len(entries) == 15
        self._assert_ids(entries, 1, 15)

        # Should only call the first 2 pages
        resps = mock_optional_3_pages
        _assert_all_called(*resps[:-2])
        _assert_none_called(*resps[-2:])

    def test_limit_less_than_page(self, wpapi, mock_optional_3_pages):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, num=5)
        assert len(entries) == 5
        self._assert_ids(entries, 1, 5)

        # Should only call the first page
        resps = mock_optional_3_pages
        _assert_all_called(resps[0])
        _assert_none_called(*resps[1:])

    def test_start_limit_across_pages(self, wpapi, mock_optional_3_pages_with_per_page):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, start=5, num=10)
        assert len(entries) == 10
        self._assert_ids(entries, 5, 14)

        # Should only call the first 2 pages
        resps = mock_optional_3_pages_with_per_page
        _assert_all_called(resps[0], resps[1])
        _assert_none_called(*resps[2:])

    def test_start_limit_less_than_page(
        self, wpapi, mock_optional_3_pages_with_per_page
    ):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, start=5, num=5)
        assert len(entries) == 5
        self._assert_ids(entries, 5, 9)

        resps = mock_optional_3_pages_with_per_page
        _assert_all_called(resps[0])
        _assert_none_called(*resps[1:])

    def test_limit_more_than_exists(self, wpapi, mock_3_pages):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, num=50)
        assert len(entries) == 30
        self._assert_ids(entries, 1, 30)

        resps = mock_3_pages
        _assert_all_called(*resps)

    def test_less_than_full_page(self, wpapi, mocked_responses):
        headers = {"X-WP-Total": "5", "X-WP-TotalPages": "1"}
        endpoint = f"{FAKE_TARGET}/wp-json/wp/v2/posts"

        mocked_responses.get(
            endpoint,
            match=[matchers.query_param_matcher({"page": "1"})],
            json=_fake_api_page(1, per_page=5),
            headers=headers,
        )
        mocked_responses.get(
            endpoint,
            match=[matchers.query_param_matcher({"page": "2"})],
            status=400,
            json=no_more_pages_body,
        )

        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH)
        assert len(entries) == 5
        self._assert_ids(entries, 1, 5)
