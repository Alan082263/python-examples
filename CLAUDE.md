# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

A collection of independent Python learning projects, not one application. There is no top-level build, lint, or test setup, and no test suite anywhere. Each project is run on its own.

- Two real apps, each with its own `requirements.txt` and (gitignored) `venv/`: `Pizza/pizza_app/` and `Network Scanner/network_scanner/`. Their READMEs cover setup in detail.
- Everything else is a single-file script, run with `python <file>.py` from its folder: `Area of Circle`, `Car`, `First and Last Colours`, `Human`, `List and Tuple Generator`, `Reverse String`, `Sun Stages` (interactive, prompts on stdin).
- `Car.py` at the repo root is a stray tracked duplicate of `Car/Car.py`.
- `Network Scanner/network_scanner.zip` is a tracked archive of the app. Edit the unpacked source, not the zip.
- `.gitignore` excludes `*.db`/`*.sqlite*`, `venv/`, `_to_delete/`. Never commit databases such as `Pizza/pizza_app/pizza.db`.

## Pizza app (`Pizza/pizza_app/`)

Flask app: Flask-Login sessions, Flask-WTF forms, Flask-SQLAlchemy on SQLite.

```bash
cd Pizza/pizza_app
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py            # dev server on http://127.0.0.1:5000
python seed.py           # creates testuser / testpass123
python debug_login.py    # prints the DB URI in use and lists users
```

Architecture points that span files:
- `app.py` builds the app in `create_app()` and also instantiates a module-level `app = create_app()`. `seed.py` and `debug_login.py` do `from app import app`, so importing `app` has side effects: it runs `db.create_all()` and creates the DB. There are no migrations.
- All routes are defined inside `register_routes(app)`, not as top-level decorators.
- `db` and `login_manager` live in `extensions.py`, so `models.py` and `app.py` can both import them without a circular import.
- `config.py` reads `SECRET_KEY` and `DATABASE_URL` from the environment. The defaults are a dev-only secret and a SQLite file next to `config.py`.
- Order routes must check that the order belongs to `current_user` and return 403 otherwise. Keep that check on any new order route.

## Network Scanner (`Network Scanner/network_scanner/`)

Tkinter GUI over the system `nmap` binary (must be on PATH). Python 3.11.4 per `.python-version`.

```bash
cd "Network Scanner/network_scanner"
pip install -r requirements.txt   # python-nmap, openpyxl
python main.py
sudo python main.py               # only needed for OS detection (-O)
```

Three layers with a one-way dependency:
- `scanner.py`: `NetworkScanner` wraps python-nmap and returns plain data. It raises `NmapNotFoundError` if nmap is missing. It falls back to a scan without OS detection when privileges don't allow `-O`.
- `asset_manager.py`: `AssetManager` is an in-memory inventory keyed by IP, so re-scanning a host updates its row. It also handles CSV/XLSX export.
- `main.py`: the Tk UI. Scans run on a background thread, so any UI update from scan results has to be marshalled back to the Tk main thread.
