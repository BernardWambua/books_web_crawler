"""End-to-end guard tests: a real Chromium, the real guard, the local range.

Assertions count what the range's servers actually received. Each trap also runs
with no guard at all, which proves the trap really fires and the range would
notice a leak.
"""
import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from crawler.guard import GuardedBrowser, Policy
from tests.range_site import TestRange

SETTLE_MS = 400

REACHES_OUTSIDE = [
    "/redirect/out",
    "/redirect/chain",
    "/trap/offsite-image",
    "/trap/meta-refresh",
    "/trap/js-redirect",
    "/trap/own-host-image-redirects-out",
    "/trap/fetch-redirects-out",
    "/trap/websocket",
]

WRITES_TO_SITE = [
    ("/trap/form-post", "POST"),
    ("/trap/fetch-post", "POST"),
    ("/trap/fetch-delete", "DELETE"),
    ("/trap/beacon", "POST"),
]


@pytest.fixture(scope="module")
def range_servers():
    with TestRange() as servers:
        yield servers


@pytest.fixture(autouse=True)
def clean_range(range_servers):
    range_servers.clear()


@pytest.fixture(scope="module")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture
def guarded(playwright):
    with GuardedBrowser(playwright, Policy(["127.0.0.1"])) as browser:
        yield browser


@pytest.fixture
def unguarded_page(playwright):
    browser = playwright.chromium.launch()
    yield browser.new_context().new_page()
    browser.close()


def visit(page, url):
    """Open a page and let its scripts run. A refused navigation is expected here."""
    try:
        page.goto(url, wait_until="load", timeout=10_000)
    except PlaywrightError:
        pass
    # Not time.sleep: that would also pause the guard's route handlers.
    page.wait_for_timeout(SETTLE_MS)


# ---------- the guard must not get in the way ----------


def test_start_url_is_allowed(guarded, range_servers):
    page = guarded.context.new_page()
    response = page.goto(range_servers.site.url + "/")
    assert response.status == 200
    assert ("GET", "/") in range_servers.site.calls()
    assert guarded.blocked == []


def test_redirect_within_the_site_is_followed(guarded, range_servers):
    page = guarded.context.new_page()
    page.goto(range_servers.site.url + "/redirect/in")
    assert page.url == range_servers.site.url + "/landing"
    assert guarded.blocked == []


# ---------- the guard must stop these ----------


@pytest.mark.parametrize("path", REACHES_OUTSIDE)
def test_outside_is_never_reached(guarded, range_servers, path):
    visit(guarded.context.new_page(), range_servers.site.url + path)
    assert range_servers.outside.calls() == []
    assert any(range_servers.outside.url.replace("http", "") in b.url for b in guarded.blocked)


@pytest.mark.parametrize("path, method", WRITES_TO_SITE)
def test_writes_never_reach_the_site(guarded, range_servers, path, method):
    visit(guarded.context.new_page(), range_servers.site.url + path)
    assert range_servers.site.calls(method) == []
    assert any(b.method == method for b in guarded.blocked)


def test_service_workers_cannot_start(guarded, range_servers):
    visit(guarded.context.new_page(), range_servers.site.url + "/trap/service-worker")
    assert ("GET", "/sw.js") not in range_servers.site.calls()


# ---------- controls: without the guard, the same traps fire ----------


@pytest.mark.parametrize("path", REACHES_OUTSIDE)
def test_control_trap_reaches_outside_when_unguarded(unguarded_page, range_servers, path):
    visit(unguarded_page, range_servers.site.url + path)
    assert range_servers.outside.calls() != []


@pytest.mark.parametrize("path, method", WRITES_TO_SITE)
def test_control_trap_writes_when_unguarded(unguarded_page, range_servers, path, method):
    visit(unguarded_page, range_servers.site.url + path)
    assert range_servers.site.calls(method) != []


def test_control_routing_alone_does_not_stop_redirects(playwright, range_servers):
    """Why the resolver layer exists: routes are not called for redirect hops."""
    browser = playwright.chromium.launch()
    context = browser.new_context()
    policy = Policy(["127.0.0.1"])

    def route_only_guard(route, request):
        route.continue_() if policy.decide(request.method, request.url).allowed else route.abort()

    context.route("**/*", route_only_guard)
    visit(context.new_page(), range_servers.site.url + "/redirect/out")
    browser.close()
    assert range_servers.outside.calls() == [("GET", "/stolen")]
