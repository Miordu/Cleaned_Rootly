"""Create the database tables and add the starter data.

Safe to run again and again: it only adds what is missing. The live site
runs it every time it starts (see render.yaml), which is also how new tables
get created after an update.
"""

import os
from dotenv import load_dotenv
from server import app
from model import connect_to_db, db, Region, User, Plant, PlantCareDetails
from datetime import datetime

load_dotenv()

def create_tables():
    """Create database tables."""
    connect_to_db(app)
    db.create_all()
    print("Tables created!")

def add_regions():
    """Add basic regions to the database."""
    regions = [
        {"name": "Northeast US", "climate_zone": "4-7", "avg_temperature": 50.0, "humidity_level": "Moderate"},
        {"name": "Southeast US", "climate_zone": "7-10", "avg_temperature": 70.0, "humidity_level": "High"},
        {"name": "Midwest US", "climate_zone": "3-6", "avg_temperature": 45.0, "humidity_level": "Moderate"},
        {"name": "Southwest US", "climate_zone": "8-10", "avg_temperature": 75.0, "humidity_level": "Low"},
        {"name": "West Coast US", "climate_zone": "7-10", "avg_temperature": 65.0, "humidity_level": "Varied"},
        {"name": "Pacific Northwest", "climate_zone": "7-9", "avg_temperature": 55.0, "humidity_level": "High"},
    ]
    
    added = 0
    for region_data in regions:
        if not Region.query.filter_by(name=region_data["name"]).first():
            db.session.add(Region(**region_data))
            added += 1

    db.session.commit()
    print(f"Added {added} regions!")

def add_admin_user():
    """Add a sample admin user for local testing.

    Skipped on the live site (APP_ENV=production): the password is public.
    """
    if os.environ.get("APP_ENV", "").lower() == "production":
        print("Live site: sample admin user not added.")
        return
    if User.query.filter_by(email="admin@rootly.com").first():
        return
    admin = User(
        username="admin",
        email="admin@rootly.com",
        created_at=datetime.utcnow()
    )
    admin.set_password("adminpassword")
    
    db.session.add(admin)
    db.session.commit()
    print("Admin user added!")

def add_sample_plants():
    """Add sample plants to the database."""
    plants = [
        {
            "scientific_name": "Monstera deliciosa",
            "common_name": "Swiss Cheese Plant",
            "plant_type": "Houseplant",
            "origin": "Central America",
            "description": "Popular houseplant with distinctive split leaves.",
            "indoor": True,
            "outdoor": False,
            "tropical": True,
            "data_sources": ["sample_data"]
        },
        {
            "scientific_name": "Ficus lyrata",
            "common_name": "Fiddle Leaf Fig",
            "plant_type": "Houseplant",
            "origin": "Western Africa",
            "description": "Popular indoor tree with large, violin-shaped leaves.",
            "indoor": True,
            "outdoor": False,
            "tropical": True,
            "data_sources": ["sample_data"]
        },
        {
            "scientific_name": "Sansevieria trifasciata",
            "common_name": "Snake Plant",
            "plant_type": "Houseplant",
            "origin": "West Africa",
            "description": "Succulent plant with stiff, upright leaves.",
            "indoor": True,
            "outdoor": True,
            "poisonous_to_pets": True,
            "data_sources": ["sample_data"]
        }
    ]
    
    added = 0
    for plant_data in plants:
        if not Plant.query.filter_by(scientific_name=plant_data["scientific_name"]).first():
            db.session.add(Plant(**plant_data))
            added += 1

    db.session.commit()
    print(f"Added {added} sample plants!")

def add_plant_care_details():
    """Add care details for sample plants."""
    care_details = [
        {
            "scientific_name": "Monstera deliciosa",
            "watering_frequency": "Weekly",
            "watering_interval_days": 7,
            "sunlight_requirements": ["Bright indirect light"],
            "sunlight_duration_min": 4,
            "sunlight_duration_max": 6,
            "soil_preferences": "Well-draining potting mix",
            "difficulty_level": "Easy"
        },
        {
            "scientific_name": "Ficus lyrata",
            "watering_frequency": "Weekly",
            "watering_interval_days": 7,
            "sunlight_requirements": ["Bright indirect light", "Direct morning sunlight"],
            "sunlight_duration_min": 5,
            "sunlight_duration_max": 8,
            "soil_preferences": "Well-draining potting mix",
            "difficulty_level": "Moderate"
        },
        {
            "scientific_name": "Sansevieria trifasciata",
            "watering_frequency": "Monthly",
            "watering_interval_days": 30,
            "sunlight_requirements": ["Low light", "Bright indirect light"],
            "sunlight_duration_min": 2,
            "sunlight_duration_max": 8,
            "soil_preferences": "Well-draining cactus mix",
            "difficulty_level": "Easy"
        }
    ]
    
    added = 0
    for care_data in care_details:
        plant = Plant.query.filter_by(scientific_name=care_data.pop("scientific_name")).first()
        if plant and not plant.care_details:
            db.session.add(PlantCareDetails(plant_id=plant.plant_id, **care_data))
            added += 1

    db.session.commit()
    print(f"Added care details for {added} plants!")

if __name__ == "__main__":
    # Create an application context before working with the database
    with app.app_context():
        create_tables()
        add_regions()
        add_admin_user()
        add_sample_plants()
        add_plant_care_details()
        print("Database seeded successfully!")