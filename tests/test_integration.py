"""End-to-end check of the main thing Rootly is for: sign up, add a plant,
look after it, and see it all on the plant's page."""

from datetime import date, timedelta

import crud
from model import CareEvent, Reminder, UserPlant


def test_full_plant_care_workflow(client, app):
    region = crud.create_region("Southeast US", "7-10", 70.0, "High")
    plant = crud.create_plant("Calathea orbifolia", common_name="Prayer plant", indoor=True)
    crud.create_plant_care_details(plant_id=plant.plant_id, watering_frequency="Weekly")

    # Sign up (this also logs you in)
    response = client.post("/register", data={
        "username": "q", "email": "q@example.com", "password": "pw-123456",
        "region_id": region.region_id,
    })
    assert response.headers["Location"].endswith("/dashboard")

    # Add the plant to my collection
    client.post("/add-plant", data={"plant_id": plant.plant_id, "nickname": "Orbi",
                                    "location": "Bedroom"})
    user_plant = UserPlant.query.one()
    upid = user_plant.user_plant_id

    # Water it and set a reminder
    client.post("/log-care", data={"user_plant_id": upid, "event_type": "Watering",
                                   "notes": "Filtered water"})
    client.post("/add-reminder", data={
        "user_plant_id": upid, "reminder_type": "Watering", "frequency": "Weekly",
        "next_reminder_date": (date.today() + timedelta(days=7)).isoformat(),
    })
    assert CareEvent.query.count() == 1
    assert Reminder.query.count() == 1

    # Everything shows up on the plant's page
    page = client.get(f"/user-plant/{upid}")
    assert page.status_code == 200
    assert b"Orbi" in page.data

    # Log out, log back in
    client.post("/logout")
    assert client.get("/my-plants").status_code == 302
    login = client.post("/login", data={"email": "q@example.com", "password": "pw-123456"})
    assert login.headers["Location"].endswith("/dashboard")
    assert b"Orbi" in client.get("/my-plants").data
