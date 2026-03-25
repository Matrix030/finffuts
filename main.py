import argparse
from db import init_db, get_recent_transactions, recategorize_all
from import_csv import import_csv


def print_transactions(rows: list):
    if not rows:
        print("No transactions found.")
        return

    print(f"\n{'DATE':<12} {'AMOUNT':>10}  {'CATEGORY':<16}  NAME")
    print("-" * 72)
    for date, name, amount, category in rows:
        label = category if category else "Uncategorized"
        amount_str = f"{amount:>+.2f}"
        print(f"{date:<12} {amount_str:>10}  {label:<16}  {name}")
    print()


def main():
    parser = argparse.ArgumentParser(description="finffuts — local finance tracker")
    parser.add_argument("--import", dest="import_path", metavar="FILE", help="Import a Chase CSV file")
    parser.add_argument("--list", dest="list_txns", action="store_true", help="List recent transactions")
    parser.add_argument("--limit", type=int, default=20, metavar="N", help="Number of transactions to show (default 20)")
    parser.add_argument("--recategorize", action="store_true", help="Re-run categorization rules on all existing transactions")
    args = parser.parse_args()

    print("Finance app starting...")
    init_db()

    if args.import_path:
        import_csv(args.import_path)

    if args.recategorize:
        count = recategorize_all()
        print(f"Recategorized {count} transactions.")

    if args.list_txns:
        rows = get_recent_transactions(args.limit)
        print_transactions(rows)


if __name__ == "__main__":
    main()
