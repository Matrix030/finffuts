# finffuts — Rules for Claude Code

Apply these rules at every step:

1. Do only the requested step
2. Do not add future features early
3. Keep code simple and readable
4. Prefer Python
5. Use SQLite for storage
6. Keep everything local
7. After completing a step, explain:
   - what files were created/changed
   - how to run it
   - how to test it
8. Wait for approval before moving to the next step

## Stack (fixed unless something breaks)

- Python
- SQLite
- Textual (TUI)
- CSV import first
- Teller later

## Project goal

Build a local terminal finance app that starts with CSV import and later can support Teller.

Answer:
- Where is my money going?
- How much am I spending over time?
- How bad is the trend?
