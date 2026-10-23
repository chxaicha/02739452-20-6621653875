import requests
import csv
import time

URL = "https://openlibrary.org/search.json"

books = []

for page in range(1, 4):

    params = {
        "q": "computer",
        "page": page,
        "limit": 40
    }

    headers = {
        "User-Agent": "BookAnalysisProject/1.0"
    }

    print(f"กำลังดึงข้อมูล Page {page}...")

    response = requests.get(
        URL,
        params=params,
        headers=headers,
        timeout=30
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        print("เกิดข้อผิดพลาด")
        print(response.text)
        continue

    data = response.json()

    for item in data.get("docs", []):

        book = {
            "title": item.get("title"),
            "author": ", ".join(
                item.get("author_name", [])
            ),
            "published_year": item.get(
                "first_publish_year"
            ),
            "edition_count": item.get(
                "edition_count"
            ),
            "source": "Open Library",
            "url": (
                "https://openlibrary.org"
                + item.get("key", "")
            )
        }

        books.append(book)

    # เว้นช่วงระหว่าง Request
    time.sleep(2)


# บันทึกข้อมูลเป็น CSV
with open(
    "books.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [
        "title",
        "author",
        "published_year",
        "edition_count",
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
print(f"ดึงข้อมูลสำเร็จทั้งหมด {len(books)} รายการ")
print("บันทึกไฟล์ books.csv เรียบร้อยแล้ว")