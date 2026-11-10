import pytest

from crawler.guard import Policy


@pytest.fixture
def policy():
    return Policy(["books.toscrape.com", "*.cdn.example"])


@pytest.mark.parametrize(
    "method, url",
    [
        ("GET", "https://books.toscrape.com/"),
        ("get", "http://books.toscrape.com/catalogue/page-2.html"),
        ("GET", "https://BOOKS.toscrape.com/"),
        ("GET", "https://books.toscrape.com./"),
        ("GET", "https://books.toscrape.com:8443/x"),
        ("GET", "https://a.cdn.example/x.js"),
        ("GET", "https://a.b.cdn.example/x.js"),
    ],
)
def test_allowed(policy, method, url):
    assert policy.decide(method, url).allowed


@pytest.mark.parametrize(
    "method, url",
    [
        ("POST", "https://books.toscrape.com/"),
        ("HEAD", "https://books.toscrape.com/"),
        ("OPTIONS", "https://books.toscrape.com/"),
        ("DELETE", "https://books.toscrape.com/"),
        ("GET", "https://evil.example/"),
        ("GET", "https://sub.books.toscrape.com/"),
        ("GET", "https://books.toscrape.com.evil.example/"),
        ("GET", "https://notbooks.toscrape.com/"),
        ("GET", "https://books.toscrape.com@evil.example/"),
        ("GET", "https://cdn.example/x.js"),
        ("GET", "https://evilcdn.example/x.js"),
        ("GET", "file:///etc/passwd"),
        ("GET", "ftp://books.toscrape.com/"),
        ("GET", "data:text/html,hi"),
        ("GET", "http://[bad/"),
        ("GET", "not a url"),
    ],
)
def test_refused(policy, method, url):
    assert not policy.decide(method, url).allowed


@pytest.mark.parametrize(
    "hosts",
    [
        [],
        ["*"],
        [""],
        ["a.com, EXCLUDE *"],
        ["a.com --flag"],
        ["https://a.com"],
    ],
)
def test_bad_allowlists_are_rejected(hosts):
    with pytest.raises(ValueError):
        Policy(hosts)


def test_chromium_args_deny_by_default():
    args = Policy(["a.com", "*.b.com"]).chromium_args()
    assert "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE a.com, EXCLUDE *.b.com" in args
    assert "--no-proxy-server" in args
