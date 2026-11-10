# Rootly cleanup log (Nov 10, 2026)

A record of every check, test run and correction made while going through the
Rootly code. Each fix has a test that failed on the old code and passes now.

## Setup used for testing

- PostgreSQL 16, databases `rootly` (app) and `rootly_test` (tests)
- Python 3.12 and 3.11 virtual environments built from `requirements.txt`
  (the old committed venvs were built for Python 3.9 on a Mac)
- No API keys and no internet access to the plant APIs, so every API call in
  the tests is replaced with a fake response

## 1. Baseline: the tests as they were

| Test file | Result |
| --- | --- |
| `tests/test_models.py` | Could not run: syntax error. Two copies of the file were pasted together (`unittest.main()import unittest`), which also stopped the whole suite from running |
| `tests/test_routes.py` | 3 passed, but it was a copy of the model tests (class named `ModelTests`) and tested no routes |
| `tests/test_integration.py` | Failed: `RuntimeError: A 'SQLAlchemy' instance has already been registered` |
| `tests/test_performance.py` | 2 failed: same RuntimeError, and it requested `/plants`, a page that doesn't exist |
| `tests/test_apis.py` | 1 failed (`TypeError` when no key is set). The other two "passed" because they return False instead of failing |
| `run_tests.py` | Could not run: imports `RouteTests`, which doesn't exist |

**Most serious finding: running the tests deleted the real database.**
`server.py` connects to `postgresql:///rootly` the moment it's imported. The
tests changed the database setting afterwards, which has no effect, so every
`tearDown` ran `db.drop_all()` on the real `rootly` database. Reproduced: put a
row in `rootly`, ran `pytest tests/test_routes.py`, and `rootly` had 0 tables
afterwards.

## 2. Secrets check

- Searched every file and the full git history for API keys, tokens and
  passwords, and for any `.env` file ever committed.
- **No committed secrets found.** `.env.example` holds placeholders only, and
  all API keys are read from environment variables.
- `seed.py` creates a sample `admin@rootly.com` account with the password
  `adminpassword`. Fine for local testing, but don't seed a public server with it.

## 3. Corrections

| # | Problem | Fix | Test that proves it |
| --- | --- | --- | --- |
| 1 | Tests wiped the real `rootly` database | `connect_to_db` now reads `DATABASE_URI`; new `tests/conftest.py` points it at `rootly_test` before the app is imported, and refuses to run if the database name doesn't contain "test" | Ran the suite with a row in `rootly`: row still there. Ran with `TEST_DATABASE_URI=postgresql:///rootly`: suite refuses to start |
| 2 | `seed.py` crashed (`RuntimeError: SQLAlchemy instance already registered`) because `server.py` had already connected | `connect_to_db` is now safe to call twice | `dropdb rootly && createdb rootly && python seed.py` now finishes and seeds 6 regions, 1 admin, 3 plants |
| 3 | `data_merger.py` imported `get_trefle_plant_details`, which doesn't exist, so identifying or importing a plant with a Trefle ID crashed | Import the real function `get_plant_details` under that name | `test_merge_with_trefle_id_no_longer_crashes` |
| 4 | Perenual `get_care_guide` used an undefined `headers` variable (`NameError`) | Send the API key as a parameter like the other Perenual calls | `test_perenual_care_guide_no_longer_crashes` |
| 5 | No timeout on any plant API call, so a slow API could freeze a page forever | 10 second `REQUEST_TIMEOUT` on every call in `api/` | `test_perenual_returns_data_and_sends_timeout` |
| 6 | `/browse-plants?page=abc` crashed with a 500 error | Read `page` as a number with a safe default | `test_browse_plants_bad_page_number` |
| 7 | `/browse-plants` showed an empty page whenever the API returned nothing (no key, API down), instead of the plants in the database | Fall back to the database when the API list is empty | `test_browse_plants_falls_back_to_database` |
| 8 | Adding a plant with a blank or made-up plant crashed with a 500 error | Check the plant exists and show a message | `test_add_plant_with_bad_plant_id_does_not_crash` (3 cases) |
| 9 | Adding a reminder with a blank or badly typed date crashed with a database error | Check the date and show a message | `test_add_reminder_with_bad_date_does_not_crash` (2 cases) |
| 10 | The Edit Plant page crashed for any plant without a description (`truncate` on `None`); the identify results page printed "None" | Show "No description available." | `test_edit_user_plant_with_photo` |
| 11 | A browser still logged in as a deleted user crashed `/my-plants` | Clear the stale login and send them to the login page | `test_deleted_user_with_old_cookie_is_sent_to_login` |
| 12 | No upload size limit | Uploads over 16 MB get a 413 "too large" response | `test_uploads_over_16mb_are_rejected` |
| 13 | `app.run(host="0.0.0.0", debug=True)` turned on Flask's debugger for anyone on the network, which lets them run code on your computer | Debug and host now come from `.env` (`DEBUG`, `HOST`, `PORT`), defaulting to off and `127.0.0.1` | Started `server.py`: listens on 127.0.0.1, debugger off |
| 14 | Upload folder was a relative path, so starting the app from another folder saved photos in the wrong place | Built from the project folder | Covered by the photo upload tests |
| 15 | Deprecated `Model.query.get()` calls (SQLAlchemy 2.0 warning) | Replaced with `db.session.get()` / `db.get_or_404()` in `server.py` and `crud.py` | Whole suite |
| 16 | SQL echo was always on, flooding the terminal | Off by default, `SQLALCHEMY_ECHO=True` turns it on | Manual run |
| 17 | No warning when `FLASK_SECRET_KEY` is missing | Prints a warning and uses the dev key | Manual run |

### Verifying the tests themselves

To make sure the new tests really catch these bugs, the new test suite was run
against the original code from `main`:

- As-is: 58 tests refused to run because the original code connects to the
  real database (the safety check in fix 1 working).
- With only the database setting pointed at `rootly_test`: **13 failed, 53
  passed.** The 13 failures are exactly the bugs in fixes 3 to 12.
- On the fixed code: **66 passed, 1 skipped** (the skipped one is the optional
  live API check).

## 4. Repo cleanup

| Change | Why |
| --- | --- |
| Stopped tracking `env/` and `venv/` (3,238 files, about 86 MB) | Two identical copies of a Mac-only Python 3.9 virtual environment. Rebuild yours with `python3 -m venv env && pip install -r requirements.txt` |
| Stopped tracking 4 `.DS_Store` files | Mac folder settings, not code |
| Stopped tracking 8 photos in `static/uploads/` | Test uploads; `.gitignore` already said to ignore them. Folder kept with a `.gitkeep` |
| Deleted `gitignore.txt` | Duplicate of `.gitignore` |
| Rewrote `.gitignore` | Removed repeated lines, added `.pytest_cache/` |
| Deleted `utils/data_merger.py` | Broken (imports names `api/` doesn't have) and unused; `data_merger.py` is the one the app uses |
| Deleted root `test_apis.py`, `test_simple.py` and `tests/test_simple.py` | Duplicates and a print-only placeholder |
| `requirements.txt` | Removed duplicate `Pillow` and `requests` lines |
| Added `requirements-dev.txt` and `pytest.ini` | Installs pytest; pytest only collects `tests/`, not the manual scripts in the root |
| `run_tests.py` | Now just runs pytest |
| `README.md` | Finished the setup steps (they stopped at "Clone the repository:"), added project layout, tests and settings |
| `.env.example` | Added `TEST_DATABASE_URI`, `HOST`, `PORT`, `SQLALCHEMY_ECHO` |

Note: these files are removed from the repo going forward, but they are still
in the old git history. Removing them from history would mean rewriting it,
which wasn't done.

## 5. Manual check of the running app

Seeded a fresh `rootly` database, started `python server.py`, and requested
each page. All returned the expected status:

- Logged out: `/`, `/login`, `/register`, `/browse-plants`,
  `/browse-plants?page=abc`, `/browse-plants?search=fig`, `/plant/1` gave 200;
  `/plant/999` gave 404; `/dashboard` redirected to login.
- Logged in as the seeded admin: `/dashboard`, `/my-plants`, `/add-plant`,
  `/search-plants`, `/search-plants?query=ficus`, `/identify`,
  `/user-plant/1`, `/edit-user-plant/1` gave 200; adding a plant and logging
  care redirected as expected.

## 6. Not verified

- The real plant APIs (Plant.id, Perenual, Trefle) weren't reachable from the
  test machine and no keys were available, so the API code was only tested
  with fake responses. Run `RUN_LIVE_API_TESTS=1 pytest -k live` with your
  keys to check them.
- `populate_plants.py` and `enhanced_seed_plants.py` need API keys and weren't run.
- The manual scripts in the root (`test_flask_app.py`, `test_browse_plants.py`,
  `test_fixes.py`, `test_plant_identification.py`, `check_*.py`,
  `debug_flask.py`) weren't changed or run.

## 7. Suggested next steps (not done)

1. **Forms have no CSRF protection.** Flask-WTF is installed but not used, so
   another website could submit forms as a logged-in user. Adding
   `CSRFProtect(app)` and a token to each form would fix it.
2. `trefle_api.py` and `plant_service.py` aren't used anywhere, and
   `trefle_api.py` reads `TREFLE_API_TOKEN` while the rest of the app uses
   `TREFLE_API_KEY`. Delete them or wire them in.
3. Flask-Login is installed but unused (login is done by hand with the session).
4. The plant pages show Lorem ipsum instead of the plant's real description
   (latest commit on `main`). Switch back when you're ready.
5. Move the manual scripts in the root into a `scripts/` folder.
6. `datetime.utcnow()` is deprecated from Python 3.12 on; it still works.
