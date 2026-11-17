"""Shared pytest setup for Rootly.

The most important job of this file: point the app at a separate TEST
database *before* server.py is imported. server.py connects to the database
as soon as it's imported, so setting the URL any later (as the old tests did)
left the tests running against your real `rootly` database, and every
tearDown dropped all of its tables.

Run the tests with:  pytest
Create the test database once with:  createdb rootly_test
"""

import os
import sys

import pytest

TEST_DB_URI = os.environ.get("TEST_DATABASE_URI", "postgresql:///rootly_test")

# Safety check: refuse to run against anything that doesn't look like a test DB
if "test" not in TEST_DB_URI.rsplit("/", 1)[-1]:
    raise RuntimeError(
        f"Refusing to run tests against {TEST_DB_URI!r}: the database name "
        "must contain 'test' so the tests can never wipe real data."
    )

os.environ["DATABASE_URI"] = TEST_DB_URI
# Never call the real Trefle API from tests (tests that need it use fakes)
os.environ["TREFLE_API_KEY"] = ""

# Make the project root importable (server.py, model.py, crud.py live there)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server import app as flask_app  # noqa: E402
from model import db  # noqa: E402
import crud  # noqa: E402


@pytest.fixture
def app(tmp_path):
    """The Flask app with fresh, empty tables for each test."""
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        UPLOAD_FOLDER=str(tmp_path),  # uploads go to a temp folder, not static/
    )
    with flask_app.app_context():
        assert str(db.engine.url) == TEST_DB_URI, "tests must use the test database"
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    return crud.create_user("gardener", "gardener@example.com", "correct-horse")


@pytest.fixture
def other_user(app):
    return crud.create_user("neighbor", "neighbor@example.com", "other-pass")


@pytest.fixture
def plant(app):
    return crud.create_plant(
        scientific_name="Monstera deliciosa",
        common_name="Swiss cheese plant",
        indoor=True,
    )


@pytest.fixture
def logged_in_client(client, user):
    """A test client that is logged in as `user`."""
    with client.session_transaction() as sess:
        sess["user_id"] = user.user_id
    return client
