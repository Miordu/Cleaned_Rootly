# Rootly - Plant Care Tracker

Rootly is a Flask web app that helps people look after their houseplants. You
can identify a plant from a photo, keep a personal collection, log watering and
other care, set reminders, and record health problems and how they were fixed.

## Features

- Plant identification from a photo (Plant.id API)
- Personal plant collection with nicknames, locations and photos
- Care log (watering, fertilizing, repotting) and reminders
- Plant health assessments, with optional automatic diagnosis from a photo
- Browse and search plants from the local database plus the Perenual and Trefle APIs
- Region-specific care information

## Technologies

- Python 3.9+ and Flask 3
- PostgreSQL with Flask-SQLAlchemy
- Jinja templates and Bootstrap
- Plant.id, Perenual and Trefle APIs
- pytest for tests

## Project layout

| Path | What it is |
| --- | --- |
| `server.py` | The Flask app: every page and form |
| `model.py` | Database tables (SQLAlchemy models) and `connect_to_db` |
| `crud.py` | Helper functions that create, read, update and delete records |
| `data_merger.py` | Builds a new plant record from API data |
| `api/` | One module per plant API |
| `seed.py` | Creates the tables and adds sample regions, plants and an admin user |
| `populate_plants.py`, `enhanced_seed_plants.py` | Load many plants from the APIs (need API keys) |
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

3. Copy the settings file and fill in your own API keys and a secret key:

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

The tests don't call the real plant APIs. To check your API keys against the
live APIs, run `RUN_LIVE_API_TESTS=1 pytest tests/test_apis.py -k live`.

## Settings (.env)

| Setting | What it does |
| --- | --- |
| `FLASK_SECRET_KEY` | Signs login cookies. Use a long random value. |
| `DATABASE_URI` | The app's database (default `postgresql:///rootly`) |
| `TEST_DATABASE_URI` | The tests' database (default `postgresql:///rootly_test`) |
| `PLANT_ID_API_KEY`, `TREFLE_API_KEY`, `PERENUAL_API_KEY` | API keys |
| `DEBUG` | `True` turns on Flask's debugger. Only on your own computer. |
| `HOST`, `PORT` | Where the dev server listens (default `127.0.0.1:5001`) |
