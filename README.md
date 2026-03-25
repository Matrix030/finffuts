# finffuts

A local terminal finance app. Answers:
- Where is my money going?
- How much am I spending over time?
- How bad is the trend?

## Stack

- Python + SQLite
- Textual (TUI — coming)
- CSV import (Chase format)
- Local LLM via ollama (`gpt-oss:20b`) for categorization and natural language queries
- Teller (planned)

## Setup

```bash
uv sync
```

Requires [ollama](https://ollama.com) running locally with `gpt-oss:20b` pulled.

## Usage

```bash
# Import a Chase CSV
uv run python main.py --import yourfile.csv

# List recent transactions (default 20)
uv run python main.py --list
uv run python main.py --list --limit 50

# Spending summary by category
uv run python main.py --summary

# Terminal bar chart
uv run python main.py --chart category

# Natural language queries
uv run python main.py --ask "how much did I spend on uber?"
uv run python main.py --ask "show top categories"
uv run python main.py --ask "what did I spend last december?"

# Re-run categorization rules on all transactions
uv run python main.py --recategorize
```

## Categorization

Transactions are categorized in three steps:

1. **Keyword rules** — fast, always runs first (`categorize.py`)
2. **merchant_map** — learned from past categorizations, stored in SQLite
3. **GPT fallback** — calls `gpt-oss:20b` via ollama for unknown merchants; result is cached in `merchant_map` so GPT is only called once per new merchant

Categories: `Food`, `Transport`, `Subscriptions`, `Shopping`, `Utilities`, `Other`

## Database

SQLite (`finance.db`, gitignored).

```
transactions(id, date, name, amount, category)
merchant_map(name, category)
```

## Files

| File | Purpose |
|---|---|
| `main.py` | CLI entry point |
| `db.py` | SQLite setup and queries |
| `import_csv.py` | Chase CSV import with deduplication |
| `categorize.py` | Keyword rules + merchant_map + GPT fallback |
| `charts.py` | ASCII bar chart |
| `ask.py` | Natural language → SQL via local LLM |
