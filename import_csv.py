import csv
import hashlib
from db import get_connection
from categorize import categorize

REQUIRED_COLUMNS = {"Posting Date", "Description", "Amount"}


def make_id(date: str, name: str, amount: str) -> str:
    raw = f"{date}|{name}|{amount}"
    return hashlib.sha1(raw.encode()).hexdigest()


def import_csv(path: str):
    inserted = 0
    skipped = 0
    duplicates = 0

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            print(f"Error: CSV is missing required columns: {missing}")
            return

        with get_connection() as conn:
            from embeddings import load_merchant_embeddings
            merchant_embeddings = load_merchant_embeddings(conn)
            for i, row in enumerate(reader, start=2):  # row 1 is header
                date = row.get("Posting Date", "").strip()
                name = row.get("Description", "").strip()
                amount_raw = row.get("Amount", "").strip()

                if not date or not name or not amount_raw:
                    print(f"  Row {i}: skipped — missing date, description, or amount")
                    skipped += 1
                    continue

                try:
                    amount = float(amount_raw)
                except ValueError:
                    print(f"  Row {i}: skipped — invalid amount {amount_raw!r}")
                    skipped += 1
                    continue

                tx_id = make_id(date, name, amount_raw)
                category = categorize(name, conn, merchant_embeddings)

                try:
                    conn.execute(
                        "INSERT INTO transactions (id, date, name, amount, category) VALUES (?, ?, ?, ?, ?)",
                        (tx_id, date, name, amount, category),
                    )
                    inserted += 1
                except Exception:
                    duplicates += 1

    print(f"Import complete: {inserted} inserted, {duplicates} duplicates skipped, {skipped} malformed rows skipped")
