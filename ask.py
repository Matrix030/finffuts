import re
import json
import urllib.request
from db import get_connection

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"

SCHEMA = """
Table: transactions
Columns:
  id       TEXT PRIMARY KEY
  date     TEXT  (format: MM/DD/YYYY)
  name     TEXT  (merchant / description)
  amount   REAL  (negative = expense, positive = income)
  category TEXT  (Transport, Food, Shopping, Subscriptions, Other)
"""

SYSTEM_PROMPT = f"""You are a SQL assistant for a personal finance SQLite database.

Schema:
{SCHEMA}

Rules:
- Return ONLY a single raw SQL SELECT statement. No explanation, no markdown, no code fences.
- Never use INSERT, UPDATE, DELETE, DROP, or any write operation.
- Use only the transactions table.
- Dates are stored as MM/DD/YYYY strings. Use strftime or string comparison carefully.
- For "this month" use the current month. Today is date('now').
- For spending questions, filter amount < 0 and use ABS(amount) or SUM(amount).
- Limit open-ended queries to 20 rows unless the user asks for more.
"""


def _call_ollama(question: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    return body["message"]["content"].strip()


def _extract_sql(raw: str) -> str:
    # Strip markdown code fences if the model adds them anyway
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE).strip().strip("`").strip()
    # Take only the first statement
    return raw.split(";")[0].strip()


def _is_safe(sql: str) -> bool:
    upper = sql.upper()
    if not upper.startswith("SELECT"):
        return False
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "PRAGMA"]
    return not any(kw in upper for kw in forbidden)


def _format_results(rows: list, description: list) -> str:
    if not rows:
        return "No results found."

    col_names = [d[0] for d in description]
    col_widths = [max(len(str(name)), max((len(str(r[i])) for r in rows), default=0))
                  for i, name in enumerate(col_names)]

    header = "  ".join(str(name).upper().ljust(w) for name, w in zip(col_names, col_widths))
    divider = "  ".join("-" * w for w in col_widths)
    lines = [header, divider]
    for row in rows:
        lines.append("  ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))
    return "\n".join(lines)


def ask_question(question: str) -> str:
    print(f"  Thinking...", end="\r")

    try:
        raw_sql = _call_ollama(question)
    except Exception as e:
        return f"Error: could not reach ollama — {e}"

    sql = _extract_sql(raw_sql)

    if not _is_safe(sql):
        return f"Blocked: generated query is not a safe SELECT.\n  Got: {sql}"

    print(f"  SQL: {sql}\n")

    try:
        with get_connection() as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            return _format_results(rows, cursor.description)
    except Exception as e:
        return f"SQL error: {e}\n  Query was: {sql}"
