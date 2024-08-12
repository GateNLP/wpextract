import json

import pytest
from responses import matchers
from wpextract.download.exceptions import NoWordpressApi
from wpextract.download.requestsession import HTTPError
from wpextract.download.wpapi import WPApi

FAKE_TARGET = "https://example.org"
WP_POSTS_ENDPOINT = f"{FAKE_TARGET}/wp-json/wp/v2/posts"


def _get_page_url(p, datatype="posts"):
    return f"{FAKE_TARGET}/wp-json/wp/v2/{datatype}?page={p}"


def _fake_data_resp(n, start_idx):
    return [
        {"id": idx, "title": f"dummy return {idx}"}
        for idx in range(start_idx, start_idx + n)
    ]


def _fake_api_page(page=1, per_page=10):
    assert page > 0

    return _fake_data_resp(per_page, (page - 1) * per_page + 1)


no_more_pages_body = {
    "code": "rest_post_invalid_page_number",
    "message": "The page number requested is larger than the number of pages available.",
    "data": {"status": 400},
}


def test_data_resp():
    data = _fake_data_resp(10, 1)
    assert data[0]["id"] == 1
    assert data[9]["id"] == 10
    assert len(data) == 10


def test_api_page_fake():
    pg1 = _fake_api_page(1)
    assert pg1[0]["id"] == 1
    assert pg1[9]["id"] == 10

    pg2 = _fake_api_page(2)
    assert pg2[0]["id"] == 11
    assert pg2[9]["id"] == 20

    with pytest.raises(AssertionError):
        _fake_api_page(0)


@pytest.fixture()
def mock_api_root(datadir):
    return json.loads((datadir / "api_root.json").read_text())


class TestBasicInfo:
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
        resps = []

        for i in range(1, n + 1):
            params = {"page": str(i)}
            if with_per_page:
                params["per_page"] = "10"

            resps.append(
                responses.get(
                    WP_POSTS_ENDPOINT,
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
                WP_POSTS_ENDPOINT,
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
        self._assert_ids(entries, 12, 30)

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
        self._assert_ids(entries, 6, 15)

        # Should only call the first 2 pages
        resps = mock_optional_3_pages_with_per_page
        _assert_all_called(resps[0], resps[1])
        _assert_none_called(*resps[2:])

    def test_start_limit_less_than_page(
        self, wpapi, mock_optional_3_pages_with_per_page
    ):
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH, start=5, num=5)
        assert len(entries) == 5
        self._assert_ids(entries, 6, 10)

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

    def test_http_error_first_page(self, wpapi, mocked_responses):
        mocked_responses.get(WP_POSTS_ENDPOINT, status=500)
        with pytest.raises(HTTPError):
            wpapi.crawl_pages(POSTS_API_PATH)

    def test_http_error_after_first_page(self, caplog, wpapi, mocked_responses):
        headers = {"X-WP-Total": "30", "X-WP-TotalPages": "3"}
        mocked_responses.get(
            WP_POSTS_ENDPOINT,
            match=[matchers.query_param_matcher({"page": 1})],
            json=_fake_api_page(1),
            headers=headers,
        )
        mocked_responses.get(
            WP_POSTS_ENDPOINT,
            match=[matchers.query_param_matcher({"page": 2})],
            status=500,
            headers=headers,
        )

        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH)
        assert len(entries) == 10
        assert total_entries == 30
        self._assert_ids(entries, 1, 10)

        assert "HTTPError500" in caplog.text

    def test_pagination_ends_empty(self, caplog, wpapi, mocked_responses):
        headers = {"X-WP-Total": "5", "X-WP-TotalPages": "1"}
        mocked_responses.get(
            WP_POSTS_ENDPOINT,
            match=[matchers.query_param_matcher({"page": 1})],
            json=_fake_api_page(1, 5),
            headers=headers,
        )
        mocked_responses.get(
            WP_POSTS_ENDPOINT,
            match=[matchers.query_param_matcher({"page": 2})],
            json=[],
            headers=headers,
        )
        entries, total_entries = wpapi.crawl_pages(POSTS_API_PATH)
        assert len(entries) == 5
        assert total_entries == 5
        self._assert_ids(entries, 1, 5)


@pytest.mark.parametrize(
    ("obj_type", "test_method"),
    [
        (
            WPApi.COMMENT,
            "get_comments",
        ),
        (
            WPApi.POST,
            "get_posts",
        ),
        (
            WPApi.TAG,
            "get_tags",
        ),
        (
            WPApi.CATEGORY,
            "get_categories",
        ),
        (
            WPApi.USER,
            "get_users",
        ),
        (
            WPApi.MEDIA,
            "get_media",
        ),
        (
            WPApi.PAGE,
            "get_pages",
        ),
    ],
)
class TestGetData:
    @pytest.fixture()
    def wpapi_mocked_crawl(self, mocker, mock_api_root, start, num):
        # start, num = req_opts
        api = WPApi(target=FAKE_TARGET)
        api.has_v2 = True
        api.get_basic_info = mocker.Mock()
        start = 0 if start is None else start
        start_idx = start + 1
        num = (30 - start) if num is None else num
        fake_data = _fake_data_resp(num, start_idx)
        api.crawl_pages = mocker.Mock(return_value=(fake_data, 30))

        return api

    @pytest.fixture()
    def wpapi(self, mocker):
        api = WPApi(target=FAKE_TARGET)
        api.has_v2 = True
        api.get_basic_info = mocker.Mock()
        api.crawl_pages = mocker.Mock(return_value=([], 0))
        return api

    @pytest.fixture()
    def wpapi_method(self, wpapi_mocked_crawl, test_method):
        return getattr(wpapi_mocked_crawl, test_method)

    def test_get_obj_list(self, wpapi, obj_type, test_method, mocker):
        get_f_mock = mocker.patch.object(wpapi, test_method)
        wpapi.get_obj_list(obj_type, None, None)

        assert get_f_mock.call_count == 1

    @pytest.mark.parametrize(
        ("start", "num"),
        [
            pytest.param(None, None, id="fetch all"),
            pytest.param(1, None, id="fetch all from start"),
            pytest.param(5, None, id="fetch all from mid-first page"),
            pytest.param(11, None, id="fetch all from second page "),
            pytest.param(5, 10, id="fetch across pages"),
            pytest.param(None, 15, id="fetch from start with limit"),
        ],
    )
    def test_get_data(self, obj_type, wpapi_method, start, num):
        data, n_max = wpapi_method(start=start, num=num)

        start = 0 if start is None else start
        start_idx = start + 1
        num = 30 - start if num is None else num

        assert len(data) == num
        assert data[0]["id"] == start_idx
        assert data[-1]["id"] == start + num
        assert n_max == 30
