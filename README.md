# 🧠 WholeBIF Explorer – Postgres Edition

End‑to‑end workflow: **build the WholeBIF‑RDB schema in PostgreSQL** from the official SQLite dump (or Google Sheet) and launch the one‑file **Gradio UI**.

---

## ✨ Feature Summary

| Module                       | Highlights                                                                                                                          |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **`build_wholebifrdb.py`**   | • CLI tool that copies data from `wholebif.db` (SQLite) → PostgreSQL.<br>• Reflects schema, creates tables, bulk‑inserts per chunk. |
| **`gradio_wholebif_app.py`** | • Autocomplete search, pair lookup, Pillow heat‑map.<br>• Works with *any* SQLAlchemy URI (SQLite / MySQL / **PostgreSQL**).        |
| **macOS / Linux manual**     | Brew + pyenv + Postgres 15; 10‑min from clone to running UI.                                                                        |

---

## 1 · Prerequisites (macOS Monterey+)

```bash
# Homebrew core
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install pyenv git postgresql@15
# start Postgres service
brew services start postgresql@15

# Python env
pyenv install 3.12.3 && pyenv virtualenv 3.12.3 wholebif-env && pyenv local wholebif-env
pip install --upgrade pip wheel
pip install sqlalchemy psycopg2-binary pandas rapidfuzz pillow gradio
```

> **psycopg2‑binary** is mandatory for PostgreSQL.

---

## 2 · Obtain the data dump

```bash
curl -L -o wholebif.db \
  "https://drive.google.com/uc?export=download&id=11GwfVqOVMOwig2uFNfNJWgyDK4EHqAZY"
```

*(or)* export sheets → CSV → import path; `build_wholebifrdb.py` accepts either.

---

## 3 · Build WholeBIF‑RDB in PostgreSQL

```bash
# create user & DB (defaults: user = wholebif, db = wholebif)
createuser -s wholebif
createdb -O wholebif wholebif

# run the builder
python build_wholebifrdb.py --sqlite wholebif.db \
       --pg postgresql+psycopg2://wholebif@localhost:5432/wholebif \
       --chunk 5000
```

*Copy time*: 1–2 min on M‑chip for ≈1 M rows.

---

## 4 · Launch the Gradio UI (Postgres)

```bash
export WHOLEBIF_DB_URI=postgresql+psycopg2://wholebif@localhost:5432/wholebif
python gradio_wholebif_app.py  # → http://localhost:7860
```

---

## 5 · Docker (optional all‑in‑one)

```bash
docker compose -f docker-compose.postgres.yml up --build
```

* Services: `db` (Postgres 15), `app` (builder + UI).

---

## 6 · Troubleshooting

| Issue                                          | Fix                                                |
| ---------------------------------------------- | -------------------------------------------------- |
| `psycopg2.OperationalError: could not connect` | Is Postgres running? (`brew services list`)        |
| `relation "circuits" does not exist`           | Build step skipped – run `build_wholebifrdb.py`    |
| UI port busy                                   | `python gradio_wholebif_app.py --server_port 7861` |

---

## 7 · File list

```
├─ build_wholebifrdb.py      # DB loader (this repo)
├─ gradio_wholebif_app.py    # UI (this repo)
├─ wholebif.db               # original SQLite dump (✗ git‑tracked)
├─ requirements.txt          # pinned deps
└─ README.md                 # you are here
```

---

## 8 · License

Apache‑2.0 © 2025 WholeBIF Team
