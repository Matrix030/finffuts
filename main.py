import argparse
import subprocess
import sys
from db import init_db, get_recent_transactions, recategorize_all, get_spending_by_category, apply_rent_rule
from import_csv import import_csv
from charts import chart_category
from ask import ask_question


def bat_print(text: str, language: str = "tsv"):
    """Print text through bat for syntax highlighting, fall back to plain print."""
    try:
        subprocess.run(
            ["bat", "--language", language, "--style", "grid,numbers", "--paging", "never", "-"],
            input=text.encode(),
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(text)


def print_transactions(rows: list):
    if not rows:
        print("No transactions found.")
        return

    lines = ["DATE\tAMOUNT\tCATEGORY\tNAME"]
    for date, name, amount, category in rows:
        label = category if category else "Uncategorized"
        lines.append(f"{date}\t{amount:+.2f}\t{label}\t{name}")
    bat_print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="finffuts — local finance tracker")
    parser.add_argument("--import", dest="import_path", metavar="FILE", help="Import a Chase CSV file")
    parser.add_argument("--list", dest="list_txns", action="store_true", help="List recent transactions")
    parser.add_argument("--limit", type=int, default=20, metavar="N", help="Number of transactions to show (default 20)")
    parser.add_argument("--recategorize", action="store_true", help="Re-run categorization rules on all existing transactions")
    parser.add_argument("--summary", action="store_true", help="Show total spending grouped by category")
    parser.add_argument("--chart", metavar="TYPE", help="Show a chart (use: category)")
    parser.add_argument("--ask", metavar="QUESTION", help="Ask a natural language question about your finances")
    args = parser.parse_args()

    sys.stderr.write("Finance app starting...\n")
    init_db()

    if args.import_path:
        import_csv(args.import_path)

    if args.recategorize:
        count = recategorize_all()
        rent_count = apply_rent_rule()
        print(f"Recategorized {count} transactions ({rent_count} marked as Rent).")

    if args.summary:
        rows = get_spending_by_category()
        if not rows:
            print("No expense transactions found.")
        else:
            total = sum(amount for _, amount in rows)
            lines = ["CATEGORY\tTOTAL\tSHARE"]
            for category, amount in rows:
                share = (amount / total) * 100
                lines.append(f"{category}\t{amount:.2f}\t{share:.1f}%")
            lines.append(f"TOTAL\t{total:.2f}\t100.0%")
            bat_print("\n".join(lines))

    if args.chart:
        if args.chart == "category":
            rows = get_spending_by_category()
            if not rows:
                print("No expense transactions found.")
            else:
                chart_category(rows)
        else:
            print(f"Unknown chart type: {args.chart!r}. Available: category")

    if args.ask:
        result = ask_question(args.ask)
        bat_print(result)

    if args.list_txns:
        rows = get_recent_transactions(args.limit)
        print_transactions(rows)


if __name__ == "__main__":
    main()
