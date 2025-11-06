import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def chrome_driver():
    """Provides a Chrome WebDriver instance for the entire test session"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
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
