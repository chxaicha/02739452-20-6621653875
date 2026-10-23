CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    author TEXT,

    published_year INTEGER,

    edition_count INTEGER,

    price NUMERIC(10, 2),

    rating INTEGER,

    source TEXT NOT NULL,

    url TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(title, source)
);