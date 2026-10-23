from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 5542,
    "database": "bookdb",
    "user": "bookuser",
    "password": "bookpass"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/")
def dashboard():

    source = request.args.get("source", "")
    category = request.args.get("category", "")
    min_rating = request.args.get("min_rating", "")
    max_price = request.args.get("max_price", "")

    conn = get_connection()
    cur = conn.cursor()

    # -------------------------
    # Build filter
    # -------------------------

    conditions = []
    params = []

    if source:
        conditions.append("source = %s")
        params.append(source)

    if category:
        conditions.append("category = %s")
        params.append(category)

    if min_rating:
        conditions.append("rating >= %s")
        params.append(int(min_rating))

    if max_price:
        conditions.append("price <= %s")
        params.append(float(max_price))

    where_sql = ""

    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    # -------------------------
    # KPI
    # -------------------------

    cur.execute(f"""
        SELECT
            COUNT(*),
            COALESCE(AVG(price), 0),
            COALESCE(AVG(rating), 0),
            COUNT(DISTINCT source)
        FROM books
        {where_sql}
    """, params)

    kpi = cur.fetchone()

    total_books = kpi[0]
    avg_price = round(float(kpi[1]), 2)
    avg_rating = round(float(kpi[2]), 2)
    total_sources = kpi[3]

    # -------------------------
    # Source chart
    # -------------------------

    cur.execute(f"""
        SELECT source, COUNT(*)
        FROM books
        {where_sql}
        GROUP BY source
        ORDER BY COUNT(*) DESC
    """, params)

    source_data = cur.fetchall()

    source_labels = [row[0] for row in source_data]
    source_values = [row[1] for row in source_data]

    # -------------------------
    # Rating chart
    # -------------------------

    cur.execute(f"""
        SELECT rating, COUNT(*)
        FROM books
        {where_sql}
        AND rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating
    """ if where_sql else """
        SELECT rating, COUNT(*)
        FROM books
        WHERE rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating
    """, params)

    rating_data = cur.fetchall()

    rating_labels = [str(row[0]) for row in rating_data]
    rating_values = [row[1] for row in rating_data]

    # -------------------------
    # Category chart
    # -------------------------

    cur.execute(f"""
        SELECT category, COUNT(*)
        FROM books
        {where_sql}
        GROUP BY category
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """, params)

    category_data = cur.fetchall()

    category_labels = [
        row[0] if row[0] else "Unknown"
        for row in category_data
    ]

    category_values = [
        row[1]
        for row in category_data
    ]

    # -------------------------
    # Book table
    # -------------------------

    cur.execute(f"""
        SELECT
            title,
            author,
            published_year,
            price,
            rating,
            category,
            source
        FROM books
        {where_sql}
        ORDER BY title
        LIMIT 100
    """, params)

    books = cur.fetchall()

    # -------------------------
    # Filter options
    # -------------------------

    cur.execute("""
        SELECT DISTINCT source
        FROM books
        ORDER BY source
    """)

    sources = [row[0] for row in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT category
        FROM books
        WHERE category IS NOT NULL
        ORDER BY category
        LIMIT 100
    """)

    categories = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        avg_price=avg_price,
        avg_rating=avg_rating,
        total_sources=total_sources,

        source_labels=source_labels,
        source_values=source_values,

        rating_labels=rating_labels,
        rating_values=rating_values,

        category_labels=category_labels,
        category_values=category_values,

        books=books,
        sources=sources,
        categories=categories,

        selected_source=source,
        selected_category=category,
        selected_rating=min_rating,
        selected_price=max_price
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )