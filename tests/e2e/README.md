# E2E Testing

These tests check the full behaviour of the program by running it against data collected from a test WordPress site.

This is mainly used to check program behaviour is consistent against a constant set of data.

## `wpextract download`

The responses library is used to mock HTTP requests recorded from a real run of the program.

### Regenerating Data

1. Start the site with `tools/docker-compose.yml`
2. Install the Yoast SEO plugin and Polylang. Configure Polylang to use en-US, de-DE and fr-FR.
3. Import `tools/test_site.xml`
4. Use `tools/gen_resp_record.py` to run the download command on the test site and record the responses.
5. Copy the recorded yml to `data/dl_requests_record.yaml`
6. Copy the download output to `data/download_out`

## `wpextract extract`

The model output from the download command is used to test the behaviour of the extract command.

### Regenerating Data

1. Use `tools/posts_dl.sh` to download the webpages from the test site
2. Copy the output directory to `data/site_scrape`

