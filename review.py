from db import get_connection
from categorize import clean_name

DEFAULT_CATEGORIES = [
    "Food",
    "Transport",
    "Subscriptions",
    "Shopping",
    "Utilities",
    "Rent",
    "Other",
]


def normalize_category(name: str) -> str:
    return name.strip().title()


def load_categories(conn) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL AND category != ''"
    ).fetchall()
    db_cats = [normalize_category(r[0]) for r in rows]

    seen = set()
    merged = []
    for cat in DEFAULT_CATEGORIES + db_cats:
        key = normalize_category(cat)
        if key not in seen:
            seen.add(key)
            merged.append(key)
    return merged


def print_menu(tx: tuple, categories: list[str]):
    tx_id, date, name, amount, category = tx
    print("\n" + "-" * 48)
    print(f"  Date    : {date}")
    print(f"  Name    : {name}")
    print(f"  Amount  : {amount:+.2f}")
    print(f"  Current : {category or 'Uncategorized'}")
    print("-" * 48)
    print("\nCategories:\n")
    for i, cat in enumerate(categories, start=1):
        print(f"  [{i}] {cat}")
    print()
    print("  [n] New category")
    print("  [s] Skip")
    print("  [q] Quit")
    print()


def apply_category(conn, tx_id: str, raw_name: str, category: str):
    category = normalize_category(category)
    conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (category, tx_id))
    conn.execute(
        "INSERT OR REPLACE INTO merchant_map (name, category) VALUES (?, ?)",
        (clean_name(raw_name), category),
    )
    conn.commit()


def run_reviewer(uncategorized_only: bool = False):
    with get_connection() as conn:
        if uncategorized_only:
            rows = conn.execute(
                "SELECT id, date, name, amount, category FROM transactions "
                "WHERE category IS NULL OR category = '' OR category = 'Other' "
                "ORDER BY date DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, date, name, amount, category FROM transactions ORDER BY date DESC"
            ).fetchall()

        if not rows:
            print("No transactions to review.")
            return

        categories = load_categories(conn)

        for tx in rows:
            tx_id, date, name, amount, category = tx
            print_menu(tx, categories)

            while True:
                raw = input("  Choice: ").strip().lower()

                if raw == "q":
                    print("\nReview session complete.")
                    return

                if raw == "s":
                    break

                if raw == "n":
                    new_cat = input("  Enter new category: ").strip()
                    if not new_cat:
                        print("  Category cannot be empty.")
                        continue
                    new_cat = normalize_category(new_cat)
                    if new_cat not in categories:
                        categories.append(new_cat)
                    apply_category(conn, tx_id, name, new_cat)
                    print(f"  Saved as: {new_cat}")
                    break

                if raw.isdigit():
                    idx = int(raw) - 1
                    if 0 <= idx < len(categories):
                        chosen = categories[idx]
                        apply_category(conn, tx_id, name, chosen)
                        print(f"  Saved as: {chosen}")
                        break
                    else:
                        print(f"  Invalid number. Pick 1–{len(categories)}.")
                        continue

                print("  Invalid input. Enter a number, n, s, or q.")

        print("\nReview session complete.")
