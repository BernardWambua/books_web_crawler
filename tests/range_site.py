"""A local test range: a small book site full of traps, plus an "outside" server.

Nothing here touches the internet. Two servers run on loopback:

- the site, on 127.0.0.1, which the guard is told to allow
- the outside, on 127.0.0.2, a different host the browser must never reach

Each server records every request it receives, so a test can assert on what
actually arrived rather than on what the guard says it did.
"""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _book_page(number):
    return f"""<html><body>
    <ul class="breadcrumb"><li><a href="/">Home</a></li><li><a href="/cat">Poetry</a></li></ul>
    <div class="item active"><img src="../../media/{number}.jpg"></div>
    <div class="product_main"><h1>Book {number}</h1><p class="star-rating Three"></p></div>
    <div id="product_description"></div><p>About book {number}.</p>
    <table class="table table-striped">
      <tr><th>Price (incl. tax)</th><td>£1{number}.50</td></tr>
      <tr><th>Price (excl. tax)</th><td>£1{number}.00</td></tr>
      <tr><th>Availability</th><td>In stock</td></tr>
      <tr><th>Number of reviews</th><td>{number}</td></tr>
    </table></body></html>"""


def _listing(numbers):
    links = "".join(f'<h3><a href="/catalogue/book-{n}.html">Book {n}</a></h3>' for n in numbers)
    return f"<html><body>{links}</body></html>"


def _traps(outside):
    """Trap path -> page body. Each page tries to reach the outside or to write."""
    return {
        "/trap/offsite-image": f'<img src="{outside}/image.png">',
        "/trap/meta-refresh": f'<meta http-equiv="refresh" content="0;url={outside}/meta">',
        "/trap/js-redirect": f'<script>location.href="{outside}/js"</script>',
        "/trap/own-host-image-redirects-out": '<img src="/redirect/out">',
        "/trap/fetch-redirects-out": "<script>fetch('/redirect/out', {mode:'no-cors'})</script>",
        "/trap/websocket": f"<script>new WebSocket('{outside.replace('http', 'ws')}/ws')</script>",
        "/trap/form-post": (
            '<form id="f" method="post" action="/submit"><input name="a" value="b"></form>'
            "<script>document.getElementById('f').submit()</script>"
        ),
        "/trap/fetch-post": "<script>fetch('/submit', {method:'POST', body:'x'})</script>",
        "/trap/fetch-delete": "<script>fetch('/submit', {method:'DELETE'})</script>",
        "/trap/beacon": "<script>navigator.sendBeacon('/submit', 'x')</script>",
        "/trap/service-worker": "<script>navigator.serviceWorker.register('/sw.js')</script>",
    }


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host, handler):
        super().__init__((host, 0), handler)
        self.hits = []
        self.lock = threading.Lock()
        self.outside_url = None

    @property
    def url(self):
        return f"http://{self.server_address[0]}:{self.server_address[1]}"

    def calls(self, method=None):
        with self.lock:
            return [h for h in self.hits if method is None or h[0] == method]

    def clear(self):
        with self.lock:
            self.hits.clear()


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, body="", headers=None, content_type="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _serve(self):
        with self.server.lock:
            self.server.hits.append((self.command, self.path))
        self.page()

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _serve

    def page(self):
        self._send(200, "ok")


class _SiteHandler(_Handler):
    def page(self):
        path = self.path
        outside = self.server.outside_url
        redirects = {
            "/redirect/out": f"{outside}/stolen",
            "/redirect/chain": "/redirect/out",
            "/redirect/in": "/landing",
        }
        traps = _traps(outside)

        if path == "/":
            self._send(200, _listing([1, 2]))
        elif path == "/catalogue/page-2.html":
            self._send(200, _listing([3]))
        elif path.startswith("/catalogue/page-"):
            self._send(404, "Page not found")
        elif path.startswith("/catalogue/book-"):
            self._send(200, _book_page(path.split("-")[1].split(".")[0]))
        elif path in redirects:
            self._send(302, headers={"Location": redirects[path]})
        elif path in traps:
            self._send(200, f"<html><body>{traps[path]}</body></html>")
        elif path == "/sw.js":
            self._send(200, "", content_type="application/javascript")
        else:
            self._send(200, "<html><body>ok</body></html>")


class TestRange:
    """Starts both servers. Use as a context manager."""

    __test__ = False  # not a pytest test class

    def __init__(self):
        self.outside = _Server("127.0.0.2", _Handler)
        self.site = _Server("127.0.0.1", _SiteHandler)
        self.site.outside_url = self.outside.url

    def __enter__(self):
        for server in (self.site, self.outside):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        for server in (self.site, self.outside):
            server.shutdown()
            server.server_close()

    def clear(self):
        self.site.clear()
        self.outside.clear()
