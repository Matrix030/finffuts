import sqlite3

DB_PATH = "finance.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id       TEXT PRIMARY KEY,
                date     TEXT,
                name     TEXT,
                amount   REAL,
                category TEXT
            )
        """)
    print("Database ready.")
