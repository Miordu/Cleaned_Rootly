"""Tests for the mobile app's API (mobile_api.py, addresses under /api/v1)."""

import io
from datetime import date, timedelta

import pytest
from PIL import Image

import crud
import api.quantitative_plant as trefle
from model import ApiToken, CareEvent, Photo, Plant, Reminder, User, UserPlant, db

API = "/api/v1"


@pytest.fixture(autouse=True)
def no_real_apis(monkeypatch):
    monkeypatch.setattr(trefle, "search_plants", lambda q, **kw: {"data": []})


def photo_file():
    buffer = io.BytesIO()
    Image.new("RGB", (3000, 2000), "green").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@pytest.fixture
def auth(client, user):
    """Headers for a phone logged in as `user`."""
    response = client.post(f"{API}/auth/login",
                           json={"email": user.email, "password": "correct-horse"})
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


@pytest.fixture
def my_plant(client, auth, plant):
    response = client.post(f"{API}/my-plants", json={"plant_id": plant.plant_id, "nickname": "Monty"},
                           headers=auth)
    return response.get_json()["plant"]


# ---------- accounts ----------

def test_register_login_me_logout(client):
    response = client.post(f"{API}/auth/register", json={
        "username": "phone", "email": "Phone@Example.com", "password": "long-enough"})
    assert response.status_code == 201
    token = response.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get(f"{API}/me", headers=headers).get_json()["user"]["email"] == "phone@example.com"

    # The token itself is never stored, only a hash of it
    assert ApiToken.query.one().token_hash != token

    # Email is not case sensitive when logging in
    login = client.post(f"{API}/auth/login", json={"email": "phone@example.com", "password": "long-enough"})
    assert login.status_code == 200

    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 200
    assert client.get(f"{API}/me", headers=headers).status_code == 401


@pytest.mark.parametrize("body, message", [
    ({"email": "a@example.com", "password": "long-enough"}, "username"),
    ({"username": "a", "email": "a@example.com", "password": "short"}, "8 characters"),
    ({"username": "a", "email": "nope", "password": "long-enough"}, "email"),
])
def test_register_problems_are_explained(client, body, message):
    response = client.post(f"{API}/auth/register", json=body)
    assert response.status_code == 400 and message in response.get_json()["error"]


def test_register_duplicate_email(client, user):
    response = client.post(f"{API}/auth/register", json={
        "username": "x", "email": user.email.upper(), "password": "long-enough"})
    assert response.status_code == 400


def test_wrong_password_and_no_token(client, user):
    response = client.post(f"{API}/auth/login", json={"email": user.email, "password": "nope"})
    assert response.status_code == 401 and "error" in response.get_json()
    for path in ["/me", "/dashboard", "/my-plants", "/plants", "/reminders"]:
        assert client.get(f"{API}{path}").status_code == 401
        assert client.get(f"{API}{path}", headers={"Authorization": "Bearer made-up"}).status_code == 401


def test_delete_account_removes_everything(client, auth, my_plant, user):
    upid = my_plant["user_plant_id"]
    client.post(f"{API}/my-plants/{upid}/care-events", json={"event_type": "Watering"}, headers=auth)
    client.post(f"{API}/my-plants/{upid}", data={"image": (photo_file(), "p.png")}, headers=auth,
                content_type="multipart/form-data")

    assert client.delete(f"{API}/me", json={"password": "wrong"}, headers=auth).status_code == 403
    assert client.delete(f"{API}/me", json={"password": "correct-horse"}, headers=auth).status_code == 200
    assert User.query.count() == UserPlant.query.count() == CareEvent.query.count() == 0
    assert Photo.query.count() == ApiToken.query.count() == 0
    assert client.get(f"{API}/me", headers=auth).status_code == 401


# ---------- catalogue ----------

def test_options(client, app):
    crud.create_region("Southeast US")
    data = client.get(f"{API}/options").get_json()
    assert "Watering" in data["care_types"] and "Weekly" in data["reminder_frequencies"]
    assert data["regions"][0]["name"] == "Southeast US"


def test_plant_search_mixes_database_and_trefle(client, auth, plant, monkeypatch):
    monkeypatch.setattr(trefle, "search_plants", lambda q, **kw: {"data": [
        {"id": 7, "scientific_name": "Monstera adansonii", "common_name": None},
        {"id": 8, "scientific_name": "Monstera deliciosa"},  # already ours: not repeated
    ]})
    data = client.get(f"{API}/plants?search=monstera", headers=auth).get_json()
    assert [p["scientific_name"] for p in data["plants"]] == ["Monstera deliciosa"]
    assert data["more"] == [{"trefle_id": 7, "scientific_name": "Monstera adansonii",
                             "common_name": "Monstera adansonii", "image_url": None}]
    detail = client.get(f"{API}/plants/{plant.plant_id}", headers=auth).get_json()["plant"]
    assert detail["common_name"] == "Swiss cheese plant" and "care" in detail
    assert client.get(f"{API}/plants/999", headers=auth).status_code == 404


def test_add_plant_straight_from_trefle(client, auth, monkeypatch):
    monkeypatch.setattr(trefle, "get_plant_details", lambda pid: {"data": {
        "scientific_name": "Monstera adansonii", "common_name": "Swiss cheese vine",
        "family": {"name": "Araceae"},
        "main_species": {"growth": {"light": 5, "minimum_temperature": {"deg_c": 12},
                                    "maximum_temperature": {"deg_c": 30}}},
    }})
    response = client.post(f"{API}/my-plants", json={"trefle_id": 7, "location": "Bathroom"}, headers=auth)
    assert response.status_code == 201
    mine = response.get_json()["plant"]
    assert mine["name"] == "Swiss cheese vine" and mine["location"] == "Bathroom"
    assert mine["plant"]["care"]["sunlight_requirements"] == ["Partial sun"]
    assert mine["plant"]["care"]["temperature_range"] == "12°C to 30°C"
    assert Plant.query.one().data_sources == ["trefle"]


def test_trefle_down_gives_a_message_not_a_crash(client, auth, monkeypatch):
    monkeypatch.setattr(trefle, "get_plant_details", lambda pid: {"error": "down"})
    response = client.post(f"{API}/my-plants", json={"trefle_id": 7}, headers=auth)
    assert response.status_code == 400 and "try again" in response.get_json()["error"].lower()
    assert client.post(f"{API}/my-plants", json={}, headers=auth).status_code == 400


# ---------- my plants ----------

def test_my_plants_list_detail_update_delete(client, auth, my_plant):
    upid = my_plant["user_plant_id"]
    listing = client.get(f"{API}/my-plants", headers=auth).get_json()["plants"]
    assert [p["name"] for p in listing] == ["Monty"]

    updated = client.patch(f"{API}/my-plants/{upid}", json={
        "nickname": "Big Monty", "status": "struggling", "notes": "Moved to the window"},
        headers=auth).get_json()["plant"]
    assert (updated["name"], updated["status"], updated["notes"]) == \
        ("Big Monty", "struggling", "Moved to the window")
    # A made-up status is ignored
    client.patch(f"{API}/my-plants/{upid}", json={"status": "exploded"}, headers=auth)
    assert db.session.get(UserPlant, upid).status == "struggling"

    assert client.delete(f"{API}/my-plants/{upid}", headers=auth).status_code == 200
    assert client.get(f"{API}/my-plants/{upid}", headers=auth).status_code == 404


def test_photo_upload_is_shrunk_and_served(client, auth, my_plant):
    upid = my_plant["user_plant_id"]
    response = client.post(f"{API}/my-plants/{upid}", data={"image": (photo_file(), "big.png")},
                           headers=auth, content_type="multipart/form-data")
    plant = response.get_json()["plant"]
    assert plant["has_own_photo"] and plant["image_url"].startswith("/photos/")
    picture = client.get(plant["image_url"])
    assert picture.mimetype == "image/jpeg"
    assert max(Image.open(io.BytesIO(picture.data)).size) == 1600  # was 3000 wide

    # Replacing the photo removes the old one
    client.post(f"{API}/my-plants/{upid}", data={"image": (photo_file(), "again.png")},
                headers=auth, content_type="multipart/form-data")
    assert Photo.query.count() == 1 and client.get(plant["image_url"]).status_code == 404

    bad = client.post(f"{API}/my-plants/{upid}", data={"image": (io.BytesIO(b"nope"), "x.jpg")},
                      headers=auth, content_type="multipart/form-data")
    assert bad.status_code == 400 and "photo" in bad.get_json()["error"]


def test_care_reminders_and_dashboard(client, auth, my_plant):
    upid = my_plant["user_plant_id"]
    today = date.today()

    assert client.post(f"{API}/my-plants/{upid}/care-events", json={"event_type": "Watering", "notes": "A lot"},
                       headers=auth).status_code == 201
    assert client.post(f"{API}/my-plants/{upid}/care-events", json={}, headers=auth).status_code == 400

    bad = client.post(f"{API}/my-plants/{upid}/reminders", json={
        "reminder_type": "Watering", "frequency": "Weekly", "next_reminder_date": "soon"}, headers=auth)
    assert bad.status_code == 400
    reminder = client.post(f"{API}/my-plants/{upid}/reminders", json={
        "reminder_type": "Watering", "frequency": "Biweekly", "next_reminder_date": today.isoformat()},
        headers=auth).get_json()["reminder"]
    assert reminder["plant_name"] == "Monty"

    dashboard = client.get(f"{API}/dashboard", headers=auth).get_json()
    assert dashboard["plant_count"] == 1 and dashboard["recent_care_count"] == 1
    assert [r["reminder_id"] for r in dashboard["upcoming_reminders"]] == [reminder["reminder_id"]]

    done = client.post(f"{API}/reminders/{reminder['reminder_id']}/done", headers=auth).get_json()["reminder"]
    assert done["next_reminder_date"] == (today + timedelta(days=14)).isoformat()
    detail = client.get(f"{API}/my-plants/{upid}", headers=auth).get_json()["plant"]
    assert len(detail["care_events"]) == 2 and len(detail["reminders"]) == 1
    assert detail["care_events"][0]["date"].endswith("Z")

    assert len(client.get(f"{API}/reminders", headers=auth).get_json()["reminders"]) == 1
    assert client.delete(f"{API}/reminders/{reminder['reminder_id']}", headers=auth).status_code == 200
    assert Reminder.query.count() == 0


def test_health_records(client, auth, my_plant):
    upid = my_plant["user_plant_id"]
    response = client.post(f"{API}/my-plants/{upid}/health", data={
        "symptoms": ["Yellow leaves", "Wilting"], "diagnosis": "Overwatering",
        "treatment_recommendations": "Let it dry out", "image": (photo_file(), "sick.png"),
    }, headers=auth, content_type="multipart/form-data")
    assert response.status_code == 201
    record = response.get_json()["health_assessment"]
    assert record["symptoms"] == ["Yellow leaves", "Wilting"] and record["image_url"].startswith("/photos/")
    assert record["resolved"] is False
    resolved = client.post(f"{API}/health/{record['assessment_id']}/resolve", headers=auth)
    assert resolved.get_json()["health_assessment"]["resolved"] is True


def test_people_cannot_reach_each_others_data(client, my_plant, other_user):
    upid = my_plant["user_plant_id"]
    reminder = crud.create_reminder(upid, "Watering", "Weekly")
    health = crud.create_health_assessment(upid, diagnosis="Root rot")
    login = client.post(f"{API}/auth/login", json={"email": other_user.email, "password": "other-pass"})
    other = {"Authorization": f"Bearer {login.get_json()['token']}"}

    assert client.get(f"{API}/my-plants", headers=other).get_json()["plants"] == []
    for method, path in [
        ("get", f"/my-plants/{upid}"), ("patch", f"/my-plants/{upid}"), ("delete", f"/my-plants/{upid}"),
        ("post", f"/my-plants/{upid}/care-events"), ("post", f"/my-plants/{upid}/reminders"),
        ("post", f"/my-plants/{upid}/health"),
        ("post", f"/reminders/{reminder.reminder_id}/done"), ("delete", f"/reminders/{reminder.reminder_id}"),
        ("post", f"/health/{health.assessment_id}/resolve"),
    ]:
        response = getattr(client, method)(f"{API}{path}", json={"event_type": "Watering"}, headers=other)
        assert response.status_code == 404, f"{method} {path}"
    assert UserPlant.query.count() == 1 and CareEvent.query.count() == 0


def test_api_needs_no_form_token_and_unknown_addresses_answer_in_json(app, client, user):
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        response = client.post(f"{API}/auth/login", json={"email": user.email, "password": "correct-horse"})
        assert response.status_code == 200
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
    missing = client.get(f"{API}/nothing-here")
    assert missing.status_code == 404 and "error" in missing.get_json()
