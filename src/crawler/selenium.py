from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import logging
from pathlib import Path

# Setup logging directory
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

class BooksCrawler:
    def __init__(self):
        self.base_url = "https://books.toscrape.com"
        self.setup_logging()
        self.setup_driver()

    def setup_logging(self):
        """Setup basic logging configuration"""
        logging.basicConfig(
            filename=log_dir / "crawler.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Initialize the Chrome WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            # Uncomment below line for headless mode
            # options.add_argument('--headless')
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            self.wait = WebDriverWait(self.driver, 10)
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    # Add rest of the crawler implementation here...

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info("WebDriver closed successfully")