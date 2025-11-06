from bs4 import BeautifulSoup
from .models import Book

def normalize_rating(class_list):
    mapping = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}
    for c in class_list:
        if c in mapping:
            return mapping[c]
    return 0

def parse_book_page(html: str, url: str) -> Book:
    soup = BeautifulSoup(html, "lxml")

    name = soup.select_one("div.product_main h1").get_text(strip=True)
    desc_el = soup.select_one("#product_description ~ p")
    description = desc_el.get_text(strip=True) if desc_el else None
    category = soup.select("ul.breadcrumb li a")[-1].get_text(strip=True)

    table = {row.find("th").text: row.find("td").text for row in soup.select("table.table-striped tr")}
    price_incl = float(table.get("Price (incl. tax)", "£0").replace("£", ""))
    price_excl = float(table.get("Price (excl. tax)", "£0").replace("£", ""))
    availability = table.get("Availability")
    num_reviews = int(table.get("Number of reviews", "0"))

    image_rel = soup.select_one("div.item.active img")["src"].replace("../..", "")
    image_url = f"https://books.toscrape.com{image_rel}"

    rating_class = soup.select_one("p.star-rating")["class"]
    mapping = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}
    rating = next((mapping[c] for c in rating_class if c in mapping), 0)

    return Book(
        source_url=url,
        name=name,
        description=description,
        category=category,
        price_including_tax=price_incl,
        price_excluding_tax=price_excl,
        availability=availability,
        num_reviews=num_reviews,
        image_url=image_url,
        rating=rating,
        raw_html=html,
    )

