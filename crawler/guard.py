"""Keep a Playwright browser read-only and on an allowlist of hosts.

Enforcement has two layers because neither is enough alone:

1. Chromium's host resolver (--host-resolver-rules) refuses to resolve any host
   not on the allowlist. It is what stops redirects: Playwright does not call
   route handlers for redirect hops, so a route-only allowlist lets a 302 walk
   straight off the site. It also covers workers and sockets.
2. Playwright routing aborts every non-GET request, which the resolver cannot
   see, and gives a readable record of what was blocked.

Limits: Chromium only. page.request / context.request use Playwright's own
network stack and bypass both layers, so crawling code must not use them.
"""
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError

_HOST_PATTERN = re.compile(r"^(\*\.)?[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
_ALLOWED_SCHEMES = ("http", "https")


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class Blocked:
    method: str
    url: str
    reason: str


class Policy:
    """Which hosts may be reached. "example.com" is exact; "*.example.com" is subdomains only."""

    def __init__(self, hosts: Iterable[str]):
        self.hosts = tuple(host.strip().lower() for host in hosts)
        if not self.hosts:
            raise ValueError("The allowlist is empty.")
        for host in self.hosts:
            # The hosts go into a Chromium flag, so nothing but a hostname may get through.
            if not _HOST_PATTERN.match(host):
                raise ValueError(f"Not a valid allowlist host: {host!r}")

    @classmethod
    def for_url(cls, url: str) -> "Policy":
        host = urlsplit(url).hostname
        if not host:
            raise ValueError(f"No host in URL: {url!r}")
        return cls([host])

    def allows_host(self, host: Optional[str]) -> bool:
        if not host:
            return False
        host = host.lower().rstrip(".")
        for allowed in self.hosts:
            if allowed.startswith("*."):
                if host.endswith(allowed[1:]) and host != allowed[2:]:
                    return True
            elif host == allowed:
                return True
        return False

    def decide(self, method: str, url: str) -> Decision:
        """Rule on one request. Anything not clearly permitted is refused."""
        if method.upper() != "GET":
            return Decision(False, f"method {method.upper()} is not allowed")
        try:
            parts = urlsplit(url)
            host = parts.hostname
        except ValueError:
            return Decision(False, "URL could not be parsed")
        if parts.scheme.lower() not in _ALLOWED_SCHEMES:
            return Decision(False, f"scheme {parts.scheme!r} is not allowed")
        if not self.allows_host(host):
            return Decision(False, f"host {host!r} is not on the allowlist")
        return Decision(True, "allowed")

    def chromium_args(self) -> List[str]:
        excludes = ", ".join(f"EXCLUDE {host}" for host in self.hosts)
        return [
            f"--host-resolver-rules=MAP * ~NOTFOUND, {excludes}",
            # A proxy would resolve hosts on the browser's behalf, past the rule above.
            "--no-proxy-server",
        ]


class GuardedBrowser:
    """Context manager for the only supported way to get a guarded page.

    with GuardedBrowser(playwright, Policy(["books.toscrape.com"])) as guarded:
        page = guarded.context.new_page()
    """

    def __init__(self, playwright, policy: Policy, headless: bool = True):
        self.playwright = playwright
        self.policy = policy
        self.headless = headless
        self.blocked: List[Blocked] = []
        self.browser = None
        self.context = None

    def __enter__(self) -> "GuardedBrowser":
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, args=self.policy.chromium_args()
        )
        # Service workers can make requests that routing never sees.
        self.context = self.browser.new_context(service_workers="block")
        self.context.route("**/*", self._on_route)
        self.context.route_web_socket(re.compile(".*"), self._on_web_socket)
        self.context.on("requestfailed", self._on_request_failed)
        return self

    def __exit__(self, *exc):
        self.browser.close()

    def _on_route(self, route, request):
        decision = self.policy.decide(request.method, request.url)
        if decision.allowed:
            route.continue_()
            return
        self.blocked.append(Blocked(request.method, request.url, decision.reason))
        route.abort("blockedbyclient")

    def _on_web_socket(self, web_socket):
        # A routed socket that is never connected to its server opens no connection.
        # Do not call web_socket.close() here: in the sync API it deadlocks the handler.
        self.blocked.append(Blocked("WEBSOCKET", web_socket.url, "web sockets are not allowed"))

    def _on_request_failed(self, request):
        # Off-allowlist hops stopped by the resolver show up here, never in _on_route.
        decision = self.policy.decide(request.method, request.url)
        if decision.allowed:
            return
        record = Blocked(request.method, request.url, f"redirect refused: {decision.reason}")
        already_logged = any(b.url == request.url and b.method == request.method for b in self.blocked)
        if not already_logged:
            self.blocked.append(record)


__all__ = ["Blocked", "Decision", "GuardedBrowser", "Policy", "PlaywrightError"]
