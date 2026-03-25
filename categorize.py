import re
import json
import urllib.request

RULES = [
    ("Transport",     ["mta", "uber", "lyft", "metro", "transit", "subway", "taxi"]),
    ("Subscriptions", ["claude", "subscription", "netflix", "spotify", "hulu", "neetcode", "amazon prime"]),
    ("Food",          ["starbucks", "cafe", "restaurant", "mcdonald", "chipotle", "dunkin", "pizza", "halal", "instacart", "doordash", "grubhub", "papa john"]),
    ("Shopping",      ["amazon", "primark", "target", "walmart", "zara", "h&m"]),
]

DEFAULT = "Other"

VALID_CATEGORIES = {"Food", "Transport", "Subscriptions", "Shopping", "Utilities", "Rent", "Other"}

RENT_AMOUNTS = {650.0, 730.0, 725.0, 395.0}

_OLLAMA_URL = "http://localhost:11434/api/chat"
_MODEL = "gpt-oss:20b"

# Noise tokens that appear in Chase descriptions but carry no merchant signal
_NOISE = re.compile(
    r"\b("
    r"sq\s*\*|sq|tst\*|tst|in\*|sp\s*\*|ic\s*\*"   # payment processor prefixes
    r"|help\.uber\.com|uber\.com"                     # uber URL fragments
    r"|ca|ny|wa|de|nj|fl|tx|il"                       # US state abbreviations
    r"|\d{4,}"                                         # long digit strings
    r")\b",
    re.IGNORECASE,
)


def clean_name(raw: str) -> str:
    """Normalize a Chase transaction description to a stable merchant key."""
    s = raw.strip()
    # Strip trailing date fragments like "12/30" or "01/15"
    s = re.sub(r"\s+\d{1,2}/\d{1,2}$", "", s)
    # Remove noise tokens
    s = _NOISE.sub(" ", s)
    # Collapse whitespace and lowercase
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def categorize_with_gpt(name: str) -> str:
    """Call the local LLM to categorize a single merchant name."""
    prompt = (
        "Categorize this transaction into one of:\n"
        "Food, Transport, Subscriptions, Shopping, Utilities, Other\n\n"
        f'Transaction: "{name}"\n\n'
        "Return ONLY the category. No explanation."
    )
    payload = json.dumps({
        "model": _MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode()

    try:
        req = urllib.request.Request(
            _OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
        result = body["message"]["content"].strip().strip(".")
        # Take first word in case model adds any extra text
        word = result.split()[0].capitalize() if result else DEFAULT
        return word if word in VALID_CATEGORIES else DEFAULT
    except Exception:
        return DEFAULT


def _keyword_match(cleaned: str) -> str | None:
    for category, keywords in RULES:
        if any(kw in cleaned for kw in keywords):
            return category
    return None


def categorize(name: str, conn=None) -> str:
    """
    Categorize a transaction name using a hybrid approach:
      1. Keyword rules (fast, always applied first)
      2. merchant_map lookup (learned from past categorizations)
      3. Fallback to DEFAULT

    If conn is provided, stores the result in merchant_map for future reuse.
    """
    cleaned = clean_name(name)

    # 1. Keyword rules
    category = _keyword_match(cleaned)

    # 2. merchant_map lookup (only if keyword didn't match)
    if category is None and conn is not None:
        row = conn.execute(
            "SELECT category FROM merchant_map WHERE name = ?", (cleaned,)
        ).fetchone()
        if row:
            category = row[0]

    # 3. GPT fallback
    if category is None:
        print(f"  GPT categorizing: {cleaned}")
        category = categorize_with_gpt(cleaned)

    # Persist to merchant_map for future reuse
    if conn is not None:
        conn.execute(
            "INSERT OR REPLACE INTO merchant_map (name, category) VALUES (?, ?)",
            (cleaned, category),
        )

    return category
