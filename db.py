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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS merchant_map (
                name     TEXT PRIMARY KEY,
                category TEXT
            )
        """)
    print("Database ready.")


def recategorize_all() -> int:
    from categorize import categorize
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM transactions").fetchall()
        updated = 0
        for tx_id, name in rows:
            category = categorize(name, conn)
            conn.execute(
                "UPDATE transactions SET category = ? WHERE id = ?",
                (category, tx_id),
            )
            updated += 1
    return updated


def get_spending_by_category() -> list:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE amount < 0
            GROUP BY category
            ORDER BY total ASC
        """).fetchall()
    return rows


def get_recent_transactions(limit: int = 20) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT date, name, amount, category FROM transactions ORDER BY date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows
