import requests
from bs4 import BeautifulSoup
import csv
import time


BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

books = []


for page in range(1, 6):

    url = BASE_URL.format(page)

    print(f"กำลัง Scrape Page {page}...")

    headers = {
        "User-Agent": "BookAnalysisProject/1.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        print("เกิดข้อผิดพลาด")
        continue

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    book_items = soup.select(
        "article.product_pod"
    )

    print(
        f"พบหนังสือ {len(book_items)} รายการ"
    )

    for item in book_items:

        # ชื่อหนังสือ
        title = item.h3.a["title"]

        # ราคา
        price = item.select_one(
            ".price_color"
        ).text.strip()

        # Rating
        rating_element = item.select_one(
            "p.star-rating"
        )

        rating = rating_element["class"][1]

        # แปลง Rating เป็นตัวเลข
        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }

        rating_number = rating_map.get(
            rating,
            0
        )

        # URL หนังสือ
        relative_url = item.h3.a["href"]

        book_url = (
            "https://books.toscrape.com/catalogue/"
            + relative_url.replace("../", "")
        )

        book = {
            "title": title,
            "price": price,
            "rating": rating_number,
            "source": "Books to Scrape",
            "url": book_url
        }

        books.append(book)

    # เว้นช่วงระหว่าง Request
    time.sleep(1)


# บันทึกเป็น CSV
with open(
    "scraped_books.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [
        "title",
        "price",
        "rating",
        "source",
        "url"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(books)


print()
print(
    f"Scrape สำเร็จทั้งหมด {len(books)} รายการ"
)

print(
    "บันทึกไฟล์ scraped_books.csv เรียบร้อยแล้ว"
)