BAR_WIDTH = 40


def chart_category(rows: list):
    # rows: [(category, total_amount), ...] — amounts are negative
    if not rows:
        print("No data to chart.")
        return

    max_amount = max(abs(r[1]) for r in rows)

    print("\n  Spending by Category\n")
    for category, amount in rows:
        bar_len = int((abs(amount) / max_amount) * BAR_WIDTH)
        bar = "█" * bar_len
        print(f"  {category:<16} {bar:<{BAR_WIDTH}}  ${abs(amount):,.0f}")
    print()
