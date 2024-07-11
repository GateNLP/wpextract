from wpextract.download.wpapi import WPApi


def _fake_api_return(start=0):
    return [{"id": idx + start, "title": "dummy return"} for idx in range(1, 11)]


no_more_pages_body = {
    "code": "rest_post_invalid_page_number",
    "message": "The page number requested is larger than the number of pages available.",
    "data": {"status": 400},
}


def test_wpapi_crawl(mocked_responses):
    wpapi = WPApi(target="https://example.org")

    def _get_page_url(p):
        return f"https://example.org/wp-json/wp/v2/posts?page={p}"

    headers = {"X-WP-Total": "30", "X-WP-TotalPages": "3"}

    mocked_responses.get(_get_page_url(1), json=_fake_api_return(), headers=headers)
    mocked_responses.get(_get_page_url(2), json=_fake_api_return(10), headers=headers)
    mocked_responses.get(_get_page_url(3), json=_fake_api_return(20), headers=headers)
    mocked_responses.get(_get_page_url(4), status=400, json=no_more_pages_body)

    entries, total_entries = wpapi.crawl_pages("wp/v2/posts?page=%d")
    entry_ids = [entry["id"] for entry in entries]
    assert entry_ids == list(range(1, 31))
    assert total_entries == 30
