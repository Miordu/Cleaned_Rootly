# Rootly - Plant Care Tracker

Rootly is a Flask web app that helps people look after their houseplants. You
can find plants by name, keep a personal collection, log watering and other
care, set reminders, and record health problems and how they were fixed.

## Features

- Browse and search plants from the local database plus the Trefle API
- Import a plant from Trefle with its growing conditions
- Personal plant collection with nicknames, locations and photos
- Care log (watering, fertilizing, repotting) and reminders
- Plant health records with photos
- Region-specific care information

## Technologies

- Python 3.9+ and Flask 3
- PostgreSQL with Flask-SQLAlchemy
- Jinja templates and Bootstrap
- Trefle plant API
- pytest for tests

## Project layout

| Path | What it is |
| --- | --- |
| `server.py` | The Flask app: every page and form |
| `model.py` | Database tables (SQLAlchemy models) and `connect_to_db` |
| `crud.py` | Helper functions that create, read, update and delete records |
| `data_merger.py` | Builds a new plant record from API data |
| `api/quantitative_plant.py` | Trefle API client (keeps to 60 requests a minute) |
| `seed.py` | Creates the tables and adds sample regions, plants and an admin user |
| `populate_plants.py`, `enhanced_seed_plants.py` | Load many plants from Trefle (need `TREFLE_API_KEY`) |
| `templates/`, `static/` | HTML pages, CSS, JavaScript and images |
| `tests/` | The automated test suite (run with `pytest`) |
| `test_flask_app.py`, `check_*.py`, `debug_flask.py` | Manual check scripts that need the app running |

## Setup

1. Clone the repository and go into it:

   ```bash
   git clone https://github.com/miordu/cleaned_rootly.git
   cd cleaned_rootly
   ```

2. Create a virtual environment and install the packages:

   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements-dev.txt
   ```

3. Copy the settings file and fill in your Trefle token and a secret key:

   ```bash
   cp .env.example .env
   ```

   `.env` is ignored by git, so your keys stay on your computer.

4. Create the database and load the sample data:

   ```bash
   createdb rootly
   python3 seed.py
   ```

   `seed.py` expects an empty database. To start over:
   `dropdb rootly && createdb rootly && python3 seed.py`.
   It creates a sample admin account (`admin@rootly.com`, password
   `adminpassword`) for local testing only.

5. Start the app and open http://127.0.0.1:5001:

   ```bash
   python3 server.py
   ```

## Running the tests

The tests use their own database, so they never touch your real data:

```bash
createdb rootly_test   # once
pytest
```

The tests don't call the real Trefle API. To check your Trefle token against
the live API, run `RUN_LIVE_API_TESTS=1 pytest tests/test_apis.py -k live`.

## Settings (.env)

| Setting | What it does |
| --- | --- |
| `FLASK_SECRET_KEY` | Signs login cookies. Use a long random value. |
| `DATABASE_URI` | The app's database (default `postgresql:///rootly`) |
| `TEST_DATABASE_URI` | The tests' database (default `postgresql:///rootly_test`) |
| `TREFLE_API_KEY` | Your Trefle access token (free at trefle.io) |
| `DEBUG` | `True` turns on Flask's debugger. Only on your own computer. |
| `HOST`, `PORT` | Where the dev server listens (default `127.0.0.1:5001`) |

## About the Trefle limit

Trefle allows 60 requests per minute per token. The Trefle client in
`api/quantitative_plant.py` counts its own requests and waits when it would go
over, and if Trefle still answers "429 Too Many Requests" it waits as long as
Trefle asks (up to 30 seconds) and tries again, up to twice. Pages only call
Trefle when they need to: the browse page asks for one list or one search, and
importing a plant uses one request.
