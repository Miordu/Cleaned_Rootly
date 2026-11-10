"""Tests for the database models and the helper functions in crud.py."""

from datetime import date, timedelta

import crud
from model import User


def test_password_is_hashed_and_checked(app):
    user = crud.create_user("ana", "ana@example.com", "s3cret-pass")
    assert user.password_hash != "s3cret-pass"
    assert user.check_password("s3cret-pass")
    assert not user.check_password("wrong")


def test_user_create_read_update_delete(app):
    user = crud.create_user("testuser", "test@example.com", "password123")
    assert user.user_id is not None

    assert crud.get_user_by_email("test@example.com").user_id == user.user_id

    updated = crud.update_user(user.user_id, username="updateduser")
    assert updated.username == "updateduser"

    assert crud.delete_user(user.user_id) is True
    assert crud.get_user_by_id(user.user_id) is None


def test_update_and_delete_missing_user(app):
    assert crud.update_user(9999, username="nobody") is None
    assert crud.delete_user(9999) is False


def test_plant_create_search_filter_update(app):
    plant = crud.create_plant(scientific_name="Test Plant",
                              common_name="Common Test Plant", indoor=True)
    crud.create_plant(scientific_name="Outdoor Thing", outdoor=True)

    assert crud.get_plant_by_scientific_name("Test Plant").plant_id == plant.plant_id
    # search is case-insensitive and matches common or scientific name
    assert [p.plant_id for p in crud.search_plants("common test")] == [plant.plant_id]
    assert [p.plant_id for p in crud.filter_plants(indoor=True)] == [plant.plant_id]

    updated = crud.update_plant(plant.plant_id, description="Updated description")
    assert updated.description == "Updated description"


def test_search_plants_respects_limit(app):
    for i in range(5):
        crud.create_plant(scientific_name=f"Ficus {i}")
    assert len(crud.search_plants("Ficus", limit=3)) == 3


def test_care_details(app, plant):
    details = crud.create_plant_care_details(
        plant_id=plant.plant_id,
        watering_frequency="Weekly",
        sunlight_requirements=["Bright indirect"],
        difficulty_level="Easy",
    )
    assert details is not None
    assert crud.get_care_details_by_plant_id(plant.plant_id).watering_frequency == "Weekly"

    updated = crud.update_plant_care_details(plant.plant_id, watering_frequency="Bi-weekly")
    assert updated.watering_frequency == "Bi-weekly"


def test_user_plant_care_events_and_reminders(app, user, plant):
    user_plant = crud.create_user_plant(user.user_id, plant.plant_id, nickname="Monty")
    assert crud.get_user_plants(user.user_id)[0].nickname == "Monty"

    crud.create_care_event(user_plant.user_plant_id, "Watering", notes="Half a cup")
    assert len(crud.get_care_events_by_user_plant(user_plant.user_plant_id)) == 1
    assert len(crud.get_recent_care_events(user.user_id)) == 1

    crud.create_reminder(user_plant.user_plant_id, "Watering", "Weekly",
                         next_reminder_date=date.today() + timedelta(days=2))
    assert len(crud.get_upcoming_reminders(user.user_id)) == 1


def test_favorites(app, user, plant):
    crud.create_user_favorite(user.user_id, plant.plant_id)
    assert len(crud.get_user_favorites(user.user_id)) == 1
    assert crud.delete_user_favorite(user.user_id, plant.plant_id)
    assert crud.get_user_favorites(user.user_id) == []


def test_regions(app):
    region = crud.create_region("Southeast US", "7-10", 70.0, "High")
    assert crud.get_region_by_id(region.region_id).name == "Southeast US"
    assert len(crud.get_regions()) == 1


def test_email_must_be_unique(app):
    crud.create_user("one", "same@example.com", "pw")
    try:
        crud.create_user("two", "same@example.com", "pw")
    except Exception:
        from model import db
        db.session.rollback()
    assert User.query.filter_by(email="same@example.com").count() == 1
