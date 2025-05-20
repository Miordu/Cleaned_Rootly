"""Script to create database tables and seed with initial data."""

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
    
    for region_data in regions:
        region = Region(**region_data)
        db.session.add(region)
    
    db.session.commit()
    print(f"Added {len(regions)} regions!")

def add_admin_user():
    """Add admin user."""
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
    
    for plant_data in plants:
        plant = Plant(**plant_data)
        db.session.add(plant)
    
    db.session.commit()
    print(f"Added {len(plants)} sample plants!")

def add_plant_care_details():
    """Add care details for sample plants."""
    care_details = [
        {
            "plant_id": 1,  # Monstera
            "watering_frequency": "Weekly",
            "watering_interval_days": 7,
            "sunlight_requirements": ["Bright indirect light"],
            "sunlight_duration_min": 4,
            "sunlight_duration_max": 6,
            "soil_preferences": "Well-draining potting mix",
            "difficulty_level": "Easy"
        },
        {
            "plant_id": 2,  # Fiddle Leaf Fig
            "watering_frequency": "Weekly",
            "watering_interval_days": 7,
            "sunlight_requirements": ["Bright indirect light", "Direct morning sunlight"],
            "sunlight_duration_min": 5,
            "sunlight_duration_max": 8,
            "soil_preferences": "Well-draining potting mix",
            "difficulty_level": "Moderate"
        },
        {
            "plant_id": 3,  # Snake Plant
            "watering_frequency": "Monthly",
            "watering_interval_days": 30,
            "sunlight_requirements": ["Low light", "Bright indirect light"],
            "sunlight_duration_min": 2,
            "sunlight_duration_max": 8,
            "soil_preferences": "Well-draining cactus mix",
            "difficulty_level": "Easy"
        }
    ]
    
    for care_data in care_details:
        care = PlantCareDetails(**care_data)
        db.session.add(care)
    
    db.session.commit()
    print(f"Added care details for {len(care_details)} plants!")

if __name__ == "__main__":
    # Create an application context before working with the database
    with app.app_context():
        create_tables()
        add_regions()
        add_admin_user()
        add_sample_plants()
        add_plant_care_details()
        print("Database seeded successfully!")