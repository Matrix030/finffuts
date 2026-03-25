RULES = [
    ("Transport",      ["mta", "uber", "lyft", "metro", "transit", "subway", "taxi"]),
    ("Subscriptions",  ["claude", "subscription", "netflix", "spotify", "hulu", "neetcode", "amazon prime"]),
    ("Food",           ["starbucks", "cafe", "restaurant", "mcdonald", "chipotle", "dunkin", "pizza", "halal", "instacart", "doordash", "grubhub", "papa john"]),
    ("Shopping",       ["amazon", "primark", "target", "walmart", "zara", "h&m"]),
]

DEFAULT = "Other"


def categorize(name: str) -> str:
    lower = name.lower()
    for category, keywords in RULES:
        if any(kw in lower for kw in keywords):
            return category
    return DEFAULT
