from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup

import requests
import psycopg2
from bs4 import BeautifulSoup


POSTGRES_HOST = "host.docker.internal"
POSTGRES_PORT = 5542
POSTGRES_DB = "bookdb"
POSTGRES_USER = "bookuser"
POSTGRES_PASSWORD = "bookpass"


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


with DAG(
    dag_id="book_analysis_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["books", "level2"],
) as dag:

    with TaskGroup("extract_sources") as extract_sources:

        @task
        def extract_open_library():
            url = "https://openlibrary.org/search.json"

            books = []

            headers = {
                "User-Agent": "BookAnalysisProject/1.0"
            }

            for page in range(1, 4):

                params = {
                    "q": "computer",
                    "page": page,
                    "limit": 40
                }

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                response.raise_for_status()

                data = response.json()

                for item in data.get("docs", []):

                    authors = item.get(
                        "author_name", []
                    )

                    subjects = item.get(
                        "subject", []
                    )

                    category = (
                        subjects[0]
                        if subjects
                        else "Technology"
                    )

                    books.append({
                        "title": item.get("title"),
                        "author": ", ".join(authors),
                        "published_year": item.get(
                            "first_publish_year"
                        ),
                        "edition_count": item.get(
                            "edition_count"
                        ),
                        "price": None,
                        "rating": None,
                        "category": category,
                        "source": "Open Library",
                        "url": (
                            "https://openlibrary.org"
                            + item.get("key", "")
                        )
                    })

            print(
                f"Open Library: {len(books)} records"
            )

            return books


        @task
        def extract_books_to_scrape():

            books = []

            headers = {
                "User-Agent": "BookAnalysisProject/1.0"
            }

            rating_map = {
                "One": 1,
                "Two": 2,
                "Three": 3,
                "Four": 4,
                "Five": 5
            }

            for page in range(1, 6):

                url = (
                    "https://books.toscrape.com/"
                    f"catalogue/page-{page}.html"
                )

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30
                )

                response.raise_for_status()

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                items = soup.select(
                    "article.product_pod"
                )

                for item in items:

                    title = item.h3.a["title"]

                    price_text = item.select_one(
                        ".price_color"
                    ).text.strip()

                    price_text = (
                        price_text
                        .replace("Â£", "")
                        .replace("£", "")
                        .strip()
                    )

                    price = float(price_text)

                    rating_class = item.select_one(
                        "p.star-rating"
                    )["class"][1]

                    rating = rating_map.get(
                        rating_class,
                        0
                    )

                    relative_url = (
                        item.h3.a["href"]
                    )

                    book_url = (
                        "https://books.toscrape.com/"
                        "catalogue/"
                        + relative_url.replace("../", "")
                    )

                    books.append({
                        "title": title,
                        "author": None,
                        "published_year": None,
                        "edition_count": None,
                        "price": price,
                        "rating": rating,
                        "category": "General",
                        "source": "Books to Scrape",
                        "url": book_url
                    })

            print(
                f"Books to Scrape: {len(books)} records"
            )

            return books


        open_library_data = extract_open_library()
        books_to_scrape_data = extract_books_to_scrape()


    @task
    def load_to_postgresql(
        open_library_data,
        books_to_scrape_data
    ):

        all_books = (
            open_library_data
            + books_to_scrape_data
        )

        connection = get_connection()
        cursor = connection.cursor()

        # เพิ่ม category ถ้ายังไม่มี
        cursor.execute("""
            ALTER TABLE books
            ADD COLUMN IF NOT EXISTS category TEXT
        """)

        # UPSERT
        sql = """
            INSERT INTO books (
                title,
                author,
                published_year,
                edition_count,
                price,
                rating,
                category,
                source,
                url
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (title, source)
            DO UPDATE SET
                author = EXCLUDED.author,
                published_year = EXCLUDED.published_year,
                edition_count = EXCLUDED.edition_count,
                price = EXCLUDED.price,
                rating = EXCLUDED.rating,
                category = EXCLUDED.category,
                url = EXCLUDED.url
        """

        for book in all_books:

            cursor.execute(
                sql,
                (
                    book["title"],
                    book["author"],
                    book["published_year"],
                    book["edition_count"],
                    book["price"],
                    book["rating"],
                    book["category"],
                    book["source"],
                    book["url"]
                )
            )

        connection.commit()

        print(
            f"Loaded {len(all_books)} records"
        )

        cursor.close()
        connection.close()


    load_to_postgresql(
        open_library_data,
        books_to_scrape_data
    )