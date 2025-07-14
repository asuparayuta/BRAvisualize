# 🧠 WholeBIF Explorer

> Unified neuroscience connectome explorer – build the **WholeBIF‑RDB** database *once* and inspect it through a modern **Gradio UI**.
>
> **Stack** : SQLite / MySQL · SQLAlchemy 2 · Gradio 4 · Pillow · RapidFuzz · Python 3.12

<p align="center">
  <img src="docs/screenshot_matrix.png" alt="Matrix heat‑map screenshot" width="65%">
</p>

---

## ✨ Features

| Module                    | What it does                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Database builder**      | Converts the original WholeBIF Google Sheet / SQL dump into **SQLite** (single file) or **MySQL 8** schema.               |
| **Autocomplete search**   | Type‑ahead suggestions (<50 ms) for Circuit IDs & full names.                                                             |
| **Single & pair queries** | ① Keyword → Connections / References / Evidence / Scores.<br>② `(Circuit ID, Receiver ID)` → direct lookup + detail pane. |
| **Connectivity matrix**   | On‑the‑fly Pillow heat‑map visualizing existing projections (hover ▶ tooltip, click ▶ deep‑link search – WIP).            |
| **One‑file UI**           | `gradio_wholebif_app.py` (<600 LoC) — quick hackable, no framework lock‑in.                                               |
| **macOS manual**          | Step‑by‑step Homebrew / pyenv setup – *Min 15 min to first query*.                                                        |

---

## 🚀 Quick start (SQLite, macOS)

```bash
# clone this repo
$ git clone https://github.com/your‑org/wholebif‑explorer.git && cd wholebif‑explorer

# install runtime (pyenv, Homebrew)
$ brew install pyenv && pyenv install 3.12.3 && pyenv local 3.12.3
$ pip install -r requirements.txt

# download the DB (≈600 MB) & rename
$ curl -L -o wholebif.db \
  "https://drive.google.com/uc?export=download&id=11GwfVqOVMOwig2uFNfNJWgyDK4EHqAZY"

# launch the UI on http://localhost:7860
$ python gradio_wholebif_app.py
```

> **⌛ First launch?** SQLite creates a statement cache; expect 3‑5 s warm‑up.

---

### MySQL 8 mode (optional)

```bash
# 1) install / start server
brew install mysql && brew services start mysql

# 2) create DB & import dump
mysql -u root -p -e "CREATE DATABASE wholebif CHARACTER SET utf8mb4;"
mysql -u root -p wholebif < wholebif_dump.sql

# 3) point the app via env‑var
export WHOLEBIF_DB_URI=mysql+mysqlconnector://root:PWD@localhost:3306/wholebif
python gradio_wholebif_app.py
```

---

### Docker compose (all‑in‑one)

```bash
docker compose up --build
# → Frontend: http://localhost:7860
```

---

## 📂 Project layout

```
wholebif‑explorer/
├─ gradio_wholebif_app.py   # One‑file UI (v3.0)
├─ db/
│   ├─ wholebif.db          # SQLite database (git‑ignored)
│   └─ wholebif_dump.sql    # canonical MySQL dump (optional)
├─ docs/
│   └─ screenshot_matrix.png
├─ requirements.txt         # pinned deps
└─ README.md
```

---

## 🛠️ Development tips

* **Hot‑reload** : run `gradio_wholebif_app.py` with `--dev` (Gradio auto‑reloads on save).
* **VS Code launch.json** in `/docs` for debugging presets.
* **Schema evolutions** : edit `gradio_wholebif_app.py` → ORM section, keep `@lru_cache` helpers in sync.
* **Performance** : switch `build_heatmap()` to `NumPy → matplotlib → Agg` for large N.

---

## 🤝 Contributing

Pull requests are welcome – please run `pre‑commit run ‑‑all-files` before submitting.

---

## 📜 License

Apache‑2.0 © 2025 WholeBIF Team
