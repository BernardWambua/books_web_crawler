import pytest
from crawler.parser import parse_book_page

@pytest.fixture
def sample_html():
    return """
    <html><head><title>Book</title></head>
    <body>
      <div class="product_main">
        <h1>Example Book</h1>
        <p class="price_color">£51.77</p>
        <p class="instock availability">In stock</p>
        <p class="star-rating Three"></p>
      </div>
      <ul class="breadcrumb">
        <li><a href="/">Home</a></li>
        <li><a href="/catalogue/category/books/poetry_23/index.html">Poetry</a></li>
      </ul>
      <div id="product_description"></div>
      <p>Test description here.</p>
      <table class="table table-striped">
        <tr><th>Price (incl. tax)</th><td>£51.77</td></tr>
        <tr><th>Price (excl. tax)</th><td>£50.00</td></tr>
        <tr><th>Number of reviews</th><td>3</td></tr>
      </table>
      <div class="item active"><img src="../media/cache/fe/9d/fe9d123.jpg" /></div>
    </body></html>
    """

def test_parse_book_page(sample_html):
    book = parse_book_page(sample_html, "https://books.toscrape.com/test-book")
    assert book.name == "Example Book"
    assert book.price_including_tax == 51.77
    assert book.category == "Poetry"
    assert book.rating == 3
