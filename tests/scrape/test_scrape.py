from wpextract.scrape.scrape import load_scrape


def test_load_scrape(shared_datadir):
    scrape_urls_files = {
        "https://example.org/an-example-post/": shared_datadir
        / "scrape"
        / "an-example-post"
        / "index.html",
    }

    soup = load_scrape(scrape_urls_files, "https://example.org/an-example-post/")
    assert soup.title.string == "An Example Post - example.org"

    not_found = load_scrape(scrape_urls_files, "https://example.org/not-found/")
    assert not_found is None
