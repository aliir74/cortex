---
name: convert-date
description: Use when user mentions Shamsi, Jalali, Persian date, or needs to convert between Shamsi/Jalali and Gregorian calendars. Triggers on date conversion requests, "what's today in Shamsi", "convert date", or any Jalali date like 1404/11/20.
model: sonnet
---

# Shamsi (Jalali) <-> Gregorian Date Converter

Converts dates between the Persian Shamsi (Jalali) calendar and the Gregorian calendar using the Python `jdatetime` library.

## Prerequisites

Requires Python 3 with the `jdatetime` package installed and importable from the `python3` on `$PATH`. If `python3 -c "import jdatetime"` fails, point the user to `SETUP.md` at the plugin root (section: **convert-date**) and stop until it's available.

## Resolving the Python interpreter

Use the first interpreter that imports `jdatetime` cleanly:

```bash
for PY in python3 python; do
  command -v "$PY" >/dev/null 2>&1 || continue
  "$PY" -c "import jdatetime" 2>/dev/null && PYTHON="$PY" && break
done
```

If `PYTHON` is unset after the loop, fall back to the prerequisites message above. If the user has a project-local virtualenv (e.g., `.venv/bin/python`) and tells you to use it, prefer that path instead.

## Quick Reference

Run as `"$PYTHON" -c "<expr>"`:

| Task | Command |
|------|---------|
| Today in Shamsi | `import jdatetime; print(jdatetime.date.today())` |
| Gregorian -> Shamsi | `import jdatetime; print(jdatetime.date.fromgregorian(day=DD, month=MM, year=YYYY))` |
| Shamsi -> Gregorian | `import jdatetime; print(jdatetime.date(YYYY, MM, DD).togregorian())` |
| Day of week (Farsi) | `import jdatetime; d=jdatetime.date.today(); print(d.j_weekdays_fa[d.weekday()])` |
| Day of week (English) | `import jdatetime; d=jdatetime.date.today(); print(d.strftime('%A'))` |

## How to Use

1. Resolve `$PYTHON` as shown above.
2. Run the appropriate one-liner from the table.
3. Present results in BOTH calendars so the user can cross-reference:

```
2026-02-09 (Gregorian) = 1404/11/20 (Shamsi)
```

If the user asks for the day of week, append it: `2026-02-09 (Gregorian) = 1404/11/20 (Shamsi) - شنبه (Saturday)`.

## Farsi Month Names

| # | Farsi | Transliteration |
|---|-------|-----------------|
| 1 | فروردین | Farvardin |
| 2 | اردیبهشت | Ordibehesht |
| 3 | خرداد | Khordad |
| 4 | تیر | Tir |
| 5 | مرداد | Mordad |
| 6 | شهریور | Shahrivar |
| 7 | مهر | Mehr |
| 8 | آبان | Aban |
| 9 | آذر | Azar |
| 10 | دی | Dey |
| 11 | بهمن | Bahman |
| 12 | اسفند | Esfand |
