"""Tests for the pages and forms in server.py.

The Trefle API is replaced with small fakes (monkeypatch), so these tests
never call the internet and don't need an API key.
"""

import io
from datetime import date, timedelta

import pytest
from PIL import Image

import crud
import api.quantitative_plant as trefle
from model import CareEvent, HealthAssessment, Photo, Plant, Reminder, UserPlant, db


@pytest.fixture(autouse=True)
def no_real_apis(monkeypatch):
    """Make Trefle return nothing unless a test says otherwise."""
    monkeypatch.setattr(trefle, "get_plant_list", lambda page=1, **kw: {"data": []})
    monkeypatch.setattr(trefle, "search_plants", lambda q, **kw: {"data": []})


def photo_file(fmt="JPEG"):
    """A small real picture, as an upload."""
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "green").save(buffer, format=fmt)
    buffer.seek(0)
    return buffer


@pytest.fixture
def user_plant(user, plant):
    return crud.create_user_plant(user.user_id, plant.plant_id, nickname="Monty")


# ---------- public pages ----------

def test_homepage(client):
    assert client.get("/").status_code == 200


def test_register_and_login_pages(client):
    assert client.get("/register").status_code == 200
    assert client.get("/login").status_code == 200


def test_unknown_page_shows_404_template(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404


def test_plant_details(client, plant):
    response = client.get(f"/plant/{plant.plant_id}")
    assert response.status_code == 200
    assert b"Monstera deliciosa" in response.data


def test_plant_details_missing_plant_is_404(client):
    assert client.get("/plant/9999").status_code == 404


# ---------- accounts ----------

def test_register_creates_user_and_logs_in(client, app):
    crud.create_region("Southeast US")
    response = client.post("/register", data={
        "username": "newbie", "email": "newbie@example.com",
        "password": "pw1234567", "region_id": "",
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    user = crud.get_user_by_email("newbie@example.com")
    assert user is not None and user.region_id is None
    with client.session_transaction() as sess:
        assert sess["user_id"] == user.user_id


def test_register_rejects_duplicate_email(client, user):
    response = client.post("/register", data={
        "username": "copy", "email": user.email, "password": "x",
    })
    assert response.headers["Location"].endswith("/register")


def test_login_success_and_failure(client, user):
    bad = client.post("/login", data={"email": user.email, "password": "nope"})
    assert bad.status_code == 200
    assert b"Invalid email or password" in bad.data

    good = client.post("/login", data={"email": user.email, "password": "correct-horse"})
    assert good.status_code == 302
    assert good.headers["Location"].endswith("/dashboard")


def test_logout_clears_session(logged_in_client):
    logged_in_client.post("/logout")
    with logged_in_client.session_transaction() as sess:
        assert "user_id" not in sess


@pytest.mark.parametrize("path", [
    "/dashboard", "/my-plants", "/add-plant", "/search-plants",
])
def test_pages_that_need_login_redirect(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_deleted_user_with_old_cookie_is_sent_to_login(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.user_id
    crud.delete_user(user.user_id)
    for path in ("/dashboard", "/my-plants"):
        response = client.get(path)
        assert response.status_code == 302, path
        assert response.headers["Location"].endswith("/login")


# ---------- logged-in pages ----------

def test_dashboard_and_my_plants(logged_in_client, user_plant):
    assert logged_in_client.get("/dashboard").status_code == 200
    response = logged_in_client.get("/my-plants")
    assert response.status_code == 200
    assert b"Monty" in response.data


def test_add_plant(logged_in_client, user, plant):
    assert logged_in_client.get("/add-plant").status_code == 200
    response = logged_in_client.post("/add-plant", data={
        "plant_id": plant.plant_id, "nickname": "Leafy", "location": "Kitchen",
    })
    assert response.headers["Location"].endswith("/my-plants")
    assert UserPlant.query.filter_by(user_id=user.user_id, nickname="Leafy").count() == 1


@pytest.mark.parametrize("bad_id", ["", "abc", "9999"])
def test_add_plant_with_bad_plant_id_does_not_crash(logged_in_client, bad_id):
    response = logged_in_client.post("/add-plant", data={"plant_id": bad_id})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/add-plant")
    assert UserPlant.query.count() == 0


def test_user_plant_details(logged_in_client, user_plant):
    response = logged_in_client.get(f"/user-plant/{user_plant.user_plant_id}")
    assert response.status_code == 200


def test_log_care_event(logged_in_client, user_plant):
    response = logged_in_client.post("/log-care", data={
        "user_plant_id": user_plant.user_plant_id, "event_type": "Watering", "notes": "",
    })
    assert response.status_code == 302
    assert CareEvent.query.filter_by(user_plant_id=user_plant.user_plant_id).count() == 1


def test_add_reminder(logged_in_client, user_plant):
    when = (date.today() + timedelta(days=3)).isoformat()
    response = logged_in_client.post("/add-reminder", data={
        "user_plant_id": user_plant.user_plant_id, "reminder_type": "Watering",
        "frequency": "Weekly", "next_reminder_date": when,
    })
    assert response.status_code == 302
    assert Reminder.query.count() == 1


@pytest.mark.parametrize("bad_date", ["", "next tuesday"])
def test_add_reminder_with_bad_date_does_not_crash(logged_in_client, user_plant, bad_date):
    response = logged_in_client.post("/add-reminder", data={
        "user_plant_id": user_plant.user_plant_id, "reminder_type": "Watering",
        "frequency": "Weekly", "next_reminder_date": bad_date,
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/user-plant/{user_plant.user_plant_id}")
    assert Reminder.query.count() == 0


def test_health_assessment_and_resolve(logged_in_client, user_plant):
    response = logged_in_client.post("/add-health-assessment", data={
        "user_plant_id": user_plant.user_plant_id,
        "symptoms": ["Yellow leaves", "Drooping"],
        "diagnosis": "Overwatering",
    })
    assert response.status_code == 302
    assessment = HealthAssessment.query.one()
    assert assessment.symptoms == ["Yellow leaves", "Drooping"]

    logged_in_client.post(f"/resolve-health-issue/{assessment.assessment_id}")
    db.session.refresh(assessment)
    assert assessment.resolved is True


def test_edit_user_plant_with_photo(logged_in_client, user_plant, app):
    assert logged_in_client.get(f"/edit-user-plant/{user_plant.user_plant_id}").status_code == 200
    response = logged_in_client.post(
        f"/edit-user-plant/{user_plant.user_plant_id}",
        data={
            "nickname": "Big Monty", "location": "Office", "status": "active", "notes": "",
            "image": (photo_file(), "leaf.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    db.session.refresh(user_plant)
    assert user_plant.nickname == "Big Monty"
    assert user_plant.image_url.startswith("/photos/")
    # The photo is stored in the database and can be fetched back
    assert Photo.query.count() == 1
    picture = logged_in_client.get(user_plant.image_url)
    assert picture.status_code == 200 and picture.mimetype == "image/jpeg"


def test_upload_rejects_disallowed_file_type(logged_in_client, user_plant):
    logged_in_client.post(
        f"/edit-user-plant/{user_plant.user_plant_id}",
        data={"nickname": "x", "image": (io.BytesIO(b"#!/bin/sh"), "evil.sh")},
        content_type="multipart/form-data",
    )
    db.session.refresh(user_plant)
    assert user_plant.image_url is None


# ---------- people can't touch each other's plants ----------

def test_cannot_view_or_change_someone_elses_plant(client, other_user, user_plant):
    with client.session_transaction() as sess:
        sess["user_id"] = other_user.user_id
    upid = user_plant.user_plant_id

    for response in (
        client.get(f"/user-plant/{upid}"),
        client.get(f"/edit-user-plant/{upid}"),
        client.post(f"/edit-user-plant/{upid}", data={"nickname": "Stolen"}),
        client.post("/log-care", data={"user_plant_id": upid, "event_type": "Watering"}),
        client.post("/add-reminder", data={"user_plant_id": upid, "reminder_type": "x"}),
        client.post("/add-health-assessment", data={"user_plant_id": upid}),
    ):
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/my-plants")

    db.session.refresh(user_plant)
    assert user_plant.nickname == "Monty"
    assert CareEvent.query.count() == 0
    assert Reminder.query.count() == 0
    assert HealthAssessment.query.count() == 0


def test_missing_user_plant_id_is_404_not_500(logged_in_client):
    assert logged_in_client.post("/log-care", data={"event_type": "Watering"}).status_code == 404


# ---------- browse and search ----------

def test_browse_plants_falls_back_to_database(client, plant):
    response = client.get("/browse-plants")
    assert response.status_code == 200
    assert b"Monstera deliciosa" in response.data


@pytest.mark.parametrize("page", ["abc", "-3", "0"])
def test_browse_plants_bad_page_number(client, page):
    assert client.get(f"/browse-plants?page={page}").status_code == 200


def test_browse_plants_shows_trefle_results(client, monkeypatch):
    seen = {}

    def fake_list(page=1, **kw):
        seen["page"] = page
        return {"data": [{"id": 1, "common_name": "European silver fir",
                          "scientific_name": "Abies alba", "family": "Pinaceae",
                          "image_url": None}]}

    monkeypatch.setattr(trefle, "get_plant_list", fake_list)
    response = client.get("/browse-plants?page=3")
    assert response.status_code == 200
    assert b"European silver fir" in response.data
    assert seen["page"] == 3


def test_browse_plants_search_adds_trefle_results(client, plant, monkeypatch):
    monkeypatch.setattr(trefle, "search_plants", lambda q, **kw: {"data": [
        {"id": 2, "common_name": "Monkey mask", "scientific_name": "Monstera adansonii"},
        # same plant as the one already in our database: shouldn't show twice
        {"id": 3, "common_name": "Swiss cheese", "scientific_name": "Monstera deliciosa"},
    ]})
    response = client.get("/browse-plants?search=monstera")
    assert response.data.count(b"Monstera deliciosa") >= 1
    assert b"Monstera adansonii" in response.data
    assert b"Swiss cheese<" not in response.data


def test_browse_plants_search(client, plant):
    response = client.get("/browse-plants?search=monstera")
    assert response.status_code == 200
    assert b"Monstera deliciosa" in response.data


def test_search_plants(logged_in_client, plant, monkeypatch):
    monkeypatch.setattr(trefle, "search_plants", lambda q, **kw: {"data": [
        {"id": 77, "scientific_name": "Monstera adansonii", "common_name": "Monkey mask",
         "image_url": None},
    ]})
    assert logged_in_client.get("/search-plants").status_code == 200
    response = logged_in_client.get("/search-plants?query=monstera")
    assert response.status_code == 200
    assert b"Monstera deliciosa" in response.data
    assert b"Monstera adansonii" in response.data


def test_import_existing_plant_redirects_to_it(logged_in_client, plant):
    response = logged_in_client.post("/import-plant", data={"scientific_name": plant.scientific_name})
    assert response.headers["Location"].endswith(f"/plant/{plant.plant_id}")


def test_import_plant_from_trefle(logged_in_client, monkeypatch):
    calls = []
    monkeypatch.setattr(trefle, "get_plant_details", lambda pid: calls.append(pid) or {"data": {
        "scientific_name": "Ficus lyrata", "common_name": "Fiddle-leaf fig", "family": "Moraceae",
    }})
    response = logged_in_client.post("/import-plant", data={
        "scientific_name": "Ficus lyrata", "api_source": "trefle", "external_id": "5",
    })
    imported = crud.get_plant_by_scientific_name("Ficus lyrata")
    assert imported is not None
    assert response.headers["Location"].endswith(f"/plant/{imported.plant_id}")
    # Details are fetched once and reused for the growth data (saves a request)
    assert calls == ["5"]


def test_import_needs_a_trefle_result(logged_in_client):
    # This used to create a made-up placeholder plant from any text sent to it
    response = logged_in_client.post("/import-plant", data={"scientific_name": "<b>Fake plant</b>"})
    assert response.headers["Location"].endswith("/search-plants")
    assert Plant.query.count() == 0


def test_old_identify_link_goes_to_search(logged_in_client):
    # Photo identification was removed with the paid Plant.id API
    response = logged_in_client.get("/identify")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/search-plants")


def test_health_assessment_saves_photo(logged_in_client, user_plant):
    logged_in_client.post(
        "/add-health-assessment",
        data={"user_plant_id": user_plant.user_plant_id, "diagnosis": "Root rot",
              "image": (photo_file(), "sick.jpg")},
        content_type="multipart/form-data",
    )
    assessment = HealthAssessment.query.one()
    assert assessment.diagnosis == "Root rot"
    assert assessment.image_url.startswith("/photos/")


def test_dashboard_counts(logged_in_client, user_plant):
    crud.create_care_event(user_plant.user_plant_id, "Watering")
    crud.create_reminder(user_plant.user_plant_id, "Watering", "Weekly",
                         next_reminder_date=date.today() + timedelta(days=1))
    page = logged_in_client.get("/dashboard").data.decode()
    # Both cards used to show a hard-coded 0
    assert page.count('display-4">1</p>') == 3


def test_no_links_to_removed_identify_page(logged_in_client, user_plant):
    for path in ("/", "/dashboard", "/my-plants", "/add-plant"):
        assert b'href="/identify"' not in logged_in_client.get(path).data, path


def test_uploads_over_16mb_are_rejected(logged_in_client):
    big = io.BytesIO(b"0" * (16 * 1024 * 1024 + 1))
    response = logged_in_client.post(
        "/add-health-assessment",
        data={"user_plant_id": "1", "image": (big, "huge.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413


# ---------- fixes from the Nov 17 review ----------

def test_browse_trefle_cards_can_be_opened(logged_in_client, monkeypatch):
    # The "View Details" button on a Trefle card used to link to /plant/api_123 (a 404)
    monkeypatch.setattr(trefle, "get_plant_list", lambda page=1, **kw: {
        "data": [{"id": 123, "scientific_name": "Ficus lyrata", "common_name": "Fiddle"}],
        "links": {"next": "/api/v1/plants?page=2"},
    })
    monkeypatch.setattr(trefle, "get_plant_details", lambda pid: {"data": {
        "scientific_name": "Ficus lyrata", "common_name": "Fiddle", "family": {"name": "Moraceae"},
        "main_species": {"growth": {"light": 8}},
    }})
    page = logged_in_client.get("/browse-plants").get_data(as_text=True)
    assert "/plant/api_" not in page
    assert 'name="external_id" value="123"' in page
    assert "page=2" in page  # there is a Next link now

    response = logged_in_client.post("/import-plant", data={
        "scientific_name": "Ficus lyrata", "api_source": "trefle", "external_id": "123"})
    imported = crud.get_plant_by_scientific_name("Ficus lyrata")
    assert response.headers["Location"].endswith(f"/plant/{imported.plant_id}")
    assert imported.care_details.sunlight_requirements == ["Full sun"]
    assert logged_in_client.get(f"/plant/{imported.plant_id}").status_code == 200


def test_browse_filters_and_search_box(client, plant):
    crud.create_plant("Quercus robur", common_name="English oak", outdoor=True)
    indoor = client.get("/browse-plants?filter=indoor").get_data(as_text=True)
    assert "Swiss cheese plant" in indoor and "English oak" not in indoor
    outdoor = client.get("/browse-plants?filter=outdoor").get_data(as_text=True)
    assert "English oak" in outdoor and "Swiss cheese plant" not in outdoor
    # The search box keeps what you typed
    assert 'value="oak"' in client.get("/browse-plants?search=oak").get_data(as_text=True)


@pytest.mark.parametrize("form", [
    {"email": "a@example.com", "password": "long-enough"},                    # no username
    {"username": "a", "email": "a@example.com"},                               # no password
    {"username": "a", "email": "a@example.com", "password": "short"},          # short password
    {"username": "a", "email": "not-an-email", "password": "long-enough"},     # bad email
])
def test_register_with_missing_details_does_not_crash(client, form):
    response = client.post("/register", data=form)
    assert response.status_code == 302 and response.headers["Location"].endswith("/register")
    assert crud.get_users() == []


def test_login_locks_after_too_many_wrong_passwords(client, user):
    for _ in range(10):
        client.post("/login", data={"email": user.email, "password": "wrong"})
    response = client.post("/login", data={"email": user.email, "password": "correct-horse"})
    assert b"Too many wrong passwords" in response.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_needs_a_form_post(logged_in_client):
    assert logged_in_client.get("/logout").status_code == 405


def test_forms_are_rejected_without_the_hidden_token(app, logged_in_client, user_plant):
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        # Another website can't make a logged-in browser submit this
        response = logged_in_client.post("/log-care", data={
            "user_plant_id": user_plant.user_plant_id, "event_type": "Watering"})
        assert response.status_code == 302
        assert CareEvent.query.count() == 0

        # A form from our own page carries the token and works
        page = logged_in_client.get(f"/user-plant/{user_plant.user_plant_id}").get_data(as_text=True)
        token = page.split('name="csrf_token" value="')[1].split('"')[0]
        logged_in_client.post("/log-care", data={
            "user_plant_id": user_plant.user_plant_id, "event_type": "Watering",
            "csrf_token": token})
        assert CareEvent.query.count() == 1
    finally:
        app.config["WTF_CSRF_ENABLED"] = False


def test_every_post_form_has_the_hidden_token(logged_in_client, user_plant, plant):
    pages = ["/login", "/register", "/add-plant", "/my-plants", "/account",
             f"/plant/{plant.plant_id}", f"/user-plant/{user_plant.user_plant_id}",
             f"/edit-user-plant/{user_plant.user_plant_id}"]
    for path in pages:
        html = logged_in_client.get(path).get_data(as_text=True)
        for form in html.split("<form")[1:]:
            form = form.split("</form>")[0]
            if "POST" in form.split(">")[0]:
                assert 'name="csrf_token"' in form, f"form without token on {path}"


def test_reminder_done_and_delete(logged_in_client, user_plant):
    reminder = crud.create_reminder(user_plant.user_plant_id, "Watering", "Weekly",
                                    next_reminder_date=date.today())
    page = logged_in_client.get(f"/user-plant/{user_plant.user_plant_id}").get_data(as_text=True)
    assert f"/reminder/{reminder.reminder_id}/done" in page

    logged_in_client.post(f"/reminder/{reminder.reminder_id}/done")
    db.session.refresh(reminder)
    assert reminder.next_reminder_date == date.today() + timedelta(days=7)
    assert CareEvent.query.one().event_type == "Watering"

    logged_in_client.post(f"/reminder/{reminder.reminder_id}/delete")
    assert Reminder.query.count() == 0


def test_remove_plant_from_collection(logged_in_client, user_plant):
    upid = user_plant.user_plant_id
    crud.create_care_event(upid, "Watering")
    crud.create_reminder(upid, "Watering", "Weekly")
    crud.create_health_assessment(upid, diagnosis="Root rot")
    response = logged_in_client.post(f"/delete-user-plant/{upid}")
    assert response.headers["Location"].endswith("/my-plants")
    assert UserPlant.query.count() == CareEvent.query.count() == 0
    assert Reminder.query.count() == HealthAssessment.query.count() == 0
    assert Plant.query.count() == 1  # the catalogue plant stays


def test_cannot_touch_someone_elses_reminder_or_plant(client, other_user, user_plant):
    reminder = crud.create_reminder(user_plant.user_plant_id, "Watering", "Weekly")
    with client.session_transaction() as sess:
        sess["user_id"] = other_user.user_id
    assert client.post(f"/reminder/{reminder.reminder_id}/delete").status_code == 404
    assert client.post(f"/reminder/{reminder.reminder_id}/done").status_code == 404
    assert client.post(f"/delete-user-plant/{user_plant.user_plant_id}").status_code == 404
    assert Reminder.query.count() == 1 and UserPlant.query.count() == 1


def test_a_file_that_is_not_a_photo_is_refused(logged_in_client, user_plant):
    # Named .jpg but not a picture: used to be saved as-is
    logged_in_client.post(
        f"/edit-user-plant/{user_plant.user_plant_id}",
        data={"nickname": "Still saved", "image": (io.BytesIO(b"<script>alert(1)</script>"), "x.jpg")},
        content_type="multipart/form-data",
    )
    db.session.refresh(user_plant)
    assert user_plant.image_url is None and Photo.query.count() == 0
    assert user_plant.nickname == "Still saved"


def test_delete_account_from_the_website(logged_in_client, user, user_plant):
    assert logged_in_client.get("/account").status_code == 200
    logged_in_client.post("/account/delete", data={"password": "wrong"})
    assert len(crud.get_users()) == 1
    logged_in_client.post("/account/delete", data={"password": "correct-horse"})
    assert crud.get_users() == [] and UserPlant.query.count() == 0


def test_plant_page_shows_the_real_description(client):
    plant = crud.create_plant("Pilea peperomioides", description="Round coin-shaped leaves.")
    page = client.get(f"/plant/{plant.plant_id}").get_data(as_text=True)
    assert "Round coin-shaped leaves." in page and "Lorem ipsum" not in page


def test_privacy_and_health_pages(client):
    assert client.get("/privacy").status_code == 200
    assert client.get("/healthz").get_json() == {"status": "ok"}
    assert client.get("/search-plants-template").status_code == 404
