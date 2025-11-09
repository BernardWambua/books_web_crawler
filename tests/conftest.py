import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fastapi_limiter import FastAPILimiter


# ---------------------------
#  Fixtures for parser tests
# ---------------------------

TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def chrome_driver():
    """Provides a Chrome WebDriver instance for the entire test session"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    yield driver
    driver.quit()


@pytest.fixture
def sample_book_html():
    """Provides sample book HTML for testing parsers"""
    return """
    <article class="product_pod">
        <h3><a href="catalogue/sample-book_123/index.html">Sample Book</a></h3>
        <div class="product_price">
            <p class="price_color">£10.99</p>
            <p class="availability">In stock</p>
        </div>
    </article>
    """


@pytest.fixture(autouse=True)
def mock_fastapi_limiter(monkeypatch):
    """
    Disable FastAPI rate limiting during tests.
    Prevents 'You must call FastAPILimiter.init' errors and Redis evalsha calls.
    Works with all fastapi-limiter versions.
    """

    # --- Mock a fake async Redis client ---
    class FakeRedis:
        async def evalsha(self, *args, **kwargs):
            return 0  # pretend no rate limit was hit
        async def set(self, *args, **kwargs):
            return True
        async def get(self, *args, **kwargs):
            return None
        async def ttl(self, *args, **kwargs):
            return 0

    fake_redis = FakeRedis()

    # Patch FastAPILimiter internals
    monkeypatch.setattr(FastAPILimiter, "redis", fake_redis)
    monkeypatch.setattr(FastAPILimiter, "lua_sha", "mock_sha")

    async def fake_identifier(request):
        return "test-client"

    async def fake_http_callback(request, response, pexpire):
        return None

    async def fake_init(redis=None):
        FastAPILimiter.redis = fake_redis
        return None

    monkeypatch.setattr(FastAPILimiter, "identifier", fake_identifier)
    monkeypatch.setattr(FastAPILimiter, "http_callback", fake_http_callback)
    monkeypatch.setattr(FastAPILimiter, "init", fake_init)

    # For some versions, also patch possible flags
    for attr in ["inited", "initialized", "is_initialized"]:
        if hasattr(FastAPILimiter, attr):
            monkeypatch.setattr(FastAPILimiter, attr, True)

    yield


@pytest.fixture(autouse=True)
def mock_api_key(monkeypatch):
    """
    Automatically bypass API key authentication during tests.
    This prevents 401 errors unless explicitly testing auth.
    """
    from api import security

    def fake_get_api_key():
        return "test-key"

    monkeypatch.setattr(security.auth, "get_api_key", fake_get_api_key)
    yield
