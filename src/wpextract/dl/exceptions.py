class NoWordpressApi(Exception):
    """No API is available at the given URL."""

    pass


class WordPressApiNotV2(Exception):
    """The WordPress V2 API is not available."""

    pass


class NSNotFoundException(Exception):
    """The specified namespace does not exist."""

    pass
