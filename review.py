import sqlite3
from db import DB_PATH
from categorize import clean_name

CATEGORIES = [
    "Food",
    "Transport",
    "Subscriptions",
    "Shopping",
    "Utilities",
    "Other",
]

SEPARATOR = "-" * 40


def load_transactions(limit: int = 50) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, date, name, amount, category
            FROM transactions
            WHERE category = 'Other'
            ORDER BY date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


def update_transaction(tx_id: str, name: str, category: str):
    cleaned = clean_name(name)
    with sqlite3.connect(DB_PATH) as conn:
        # Update this transaction
        conn.execute(
            "UPDATE transactions SET category = ? WHERE id = ?",
            (category, tx_id),
        )
        # Also update all other transactions with the same cleaned merchant name
        conn.execute(
            "UPDATE transactions SET category = ? WHERE lower(trim(name)) LIKE ? AND category = 'Other'",
            (category, f"%{cleaned}%"),
        )
        conn.execute(
            "INSERT OR REPLACE INTO merchant_map (name, category) VALUES (?, ?)",
            (cleaned, category),
        )
        conn.commit()


def show_transaction(tx, index: int, total: int):
    tx_id, date, name, amount, category = tx
    print(f"\n[{index + 1}/{total}]")
    print(SEPARATOR)
    print(f"Date:             {date}")
    print(f"Name:             {name}")
    print(f"Amount:           {amount:+.2f}")
    print(f"Current Category: {category}")
    print(SEPARATOR)


def show_menu():
    print()
    for i, cat in enumerate(CATEGORIES, start=1):
        print(f"  [{i}] {cat}")
    print(f"  [{len(CATEGORIES) + 1}] New Category")
    print(f"  [s] Skip")
    print(f"  [q] Quit")
    print()


def run_reviewer():
    transactions = load_transactions()
    if not transactions:
        print("No transactions with category 'Other' found.")
        return

    print(f"\nLoaded {len(transactions)} transaction(s) to review.")

    while transactions:
        tx = transactions[0]
        total = len(transactions)
        show_transaction(tx, 0, total)
        show_menu()

        try:
            choice = input("Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting.")
            break

        if choice == "q":
            print("Quitting.")
            break

        if choice == "s":
            transactions = transactions[1:]
            continue

        # Numeric choice for preset category
        if choice.isdigit():
            num = int(choice)
            new_cat_index = len(CATEGORIES) + 1

            if 1 <= num <= len(CATEGORIES):
                selected = CATEGORIES[num - 1]
                update_transaction(tx[0], tx[2], selected)
                print(f"  Saved: {selected}")
                transactions = load_transactions()
                continue

            if num == new_cat_index:
                try:
                    new_cat = input("Enter new category name: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nQuitting.")
                    break

                if not new_cat:
                    print("  Empty input, skipping.")
                    transactions = transactions[1:]
                    continue

                update_transaction(tx[0], tx[2], new_cat)
                print(f"  Saved: {new_cat}")
                transactions = load_transactions()
                continue

        print("  Invalid choice, try again.")

    if not transactions:
        print("\nAll transactions reviewed.")
