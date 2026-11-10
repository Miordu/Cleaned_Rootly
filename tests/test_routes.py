"""Tests for the pages and forms in server.py.

The plant APIs are replaced with small fakes (monkeypatch), so these tests
never call the internet and don't need API keys.
"""

import io
from datetime import date, timedelta

import pytest

import crud
import api.perenual
import api.quantitative_plant
from model import CareEvent, HealthAssessment, Reminder, UserPlant, db


@pytest.fixture(autouse=True)
def no_real_apis(monkeypatch):
    """Make the plant APIs return nothing unless a test says otherwise."""
    monkeypatch.setattr(api.perenual, "get_plant_list", lambda page=1, **kw: {"data": []})
    monkeypatch.setattr(api.perenual, "search_plants", lambda q: {"data": []})
    monkeypatch.setattr(api.quantitative_plant, "search_plants", lambda q: {"data": []})


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
        "password": "pw12345", "region_id": "",
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
    logged_in_client.get("/logout")
    with logged_in_client.session_transaction() as sess:
        assert "user_id" not in sess


@pytest.mark.parametrize("path", [
    "/dashboard", "/my-plants", "/add-plant", "/identify", "/search-plants",
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
            "image": (io.BytesIO(b"fake image bytes"), "leaf.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    db.session.refresh(user_plant)
    assert user_plant.nickname == "Big Monty"
    assert user_plant.image_url.endswith("_leaf.jpg")


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


def test_browse_plants_shows_api_results(client, monkeypatch):
    monkeypatch.setattr(api.perenual, "get_plant_list", lambda page=1, **kw: {"data": [
        {"id": 1, "common_name": "European Silver Fir",
         "scientific_name": ["Abies alba"], "type": "tree", "default_image": None},
    ]})
    response = client.get("/browse-plants")
    assert response.status_code == 200
    assert b"European Silver Fir" in response.data


def test_browse_plants_search(client, plant):
    response = client.get("/browse-plants?search=monstera")
    assert response.status_code == 200
    assert b"Monstera deliciosa" in response.data


def test_search_plants(logged_in_client, plant, monkeypatch):
    monkeypatch.setattr(api.quantitative_plant, "search_plants", lambda q: {"data": [
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
    monkeypatch.setattr(api.quantitative_plant, "get_plant_details", lambda pid: {"data": {
        "scientific_name": "Ficus lyrata", "common_name": "Fiddle-leaf fig", "family": "Moraceae",
    }})
    monkeypatch.setattr(api.quantitative_plant, "get_growth_data", lambda pid: {"error": "none"})
    response = logged_in_client.post("/import-plant", data={
        "scientific_name": "Ficus lyrata", "api_source": "trefle", "external_id": "5",
    })
    imported = crud.get_plant_by_scientific_name("Ficus lyrata")
    assert imported is not None
    assert response.headers["Location"].endswith(f"/plant/{imported.plant_id}")


def test_import_plant_without_source_uses_data_merger(logged_in_client):
    response = logged_in_client.post("/import-plant", data={"scientific_name": "Pilea peperomioides"})
    imported = crud.get_plant_by_scientific_name("Pilea peperomioides")
    assert imported is not None
    assert response.headers["Location"].endswith(f"/plant/{imported.plant_id}")


def test_identify_page_and_api_error(logged_in_client, monkeypatch):
    import api.plant_id
    assert logged_in_client.get("/identify").status_code == 200
    monkeypatch.setattr(api.plant_id, "identify_plant", lambda path, **kw: {"error": "no key"})
    response = logged_in_client.post(
        "/identify",
        data={"plant_image": (io.BytesIO(b"img"), "rose.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/identify")


def test_identify_success_creates_plant(logged_in_client, monkeypatch):
    import api.plant_id
    monkeypatch.setattr(api.plant_id, "identify_plant", lambda path, **kw: {"ok": True})
    monkeypatch.setattr(api.plant_id, "map_identification_result", lambda result, **kw: {
        "scientific_name": "Rosa rubiginosa", "confidence_score": 0.93,
    })
    response = logged_in_client.post(
        "/identify",
        data={"plant_image": (io.BytesIO(b"img"), "rose.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"Rosa rubiginosa" in response.data


def test_uploads_over_16mb_are_rejected(logged_in_client):
    big = io.BytesIO(b"0" * (16 * 1024 * 1024 + 1))
    response = logged_in_client.post(
        "/identify", data={"plant_image": (big, "huge.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
