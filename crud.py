"""CRUD operations for Rootly application."""

from model import db, connect_to_db
from model import User, Plant, PlantCareDetails, UserPlant, CareEvent, Reminder
from model import HealthAssessment, IdentificationHistory, PlantHealthIssue
from model import UserFavorite, Region, PlantRegionCare, RelatedPlant
from datetime import datetime, date, timedelta
import os

# ----------------------------------------
# User operations
# ----------------------------------------

def create_user(username, email, password, region_id=None, preferences=None):
    """Create and return a new user."""
    
    user = User(
        username=username,
        email=email,
        region_id=region_id,
        preferences=preferences
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return user

def get_users():
    """Return all users."""
    return User.query.all()

def get_user_by_id(user_id):
    """Return a user by ID."""
    return User.query.get(user_id)

def get_user_by_email(email):
    """Return a user by email."""
    return User.query.filter(User.email == email).first()

def update_user(user_id, **kwargs):
    """Update user details."""
    user = User.query.get(user_id)
    
    if not user:
        return None
    
    for key, value in kwargs.items():
        if key == 'password':
            user.set_password(value)
        elif hasattr(user, key):
            setattr(user, key, value)
    
    db.session.commit()
    return user

def delete_user(user_id):
    """Delete a user."""
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    db.session.delete(user)
    db.session.commit()
    return True

# ----------------------------------------
# Plant operations
# ----------------------------------------

def create_plant(scientific_name, common_name=None, plant_type=None, image_url=None, 
                origin=None, description=None, poisonous_to_humans=False, 
                poisonous_to_pets=False, invasive=False, rare=False, 
                tropical=False, indoor=False, outdoor=False, data_sources=None):
    """Create and return a new plant."""
    
    plant = Plant(
        scientific_name=scientific_name,
        common_name=common_name,
        plant_type=plant_type,
        image_url=image_url,
        origin=origin,
        description=description,
        poisonous_to_humans=poisonous_to_humans,
        poisonous_to_pets=poisonous_to_pets,
        invasive=invasive,
        rare=rare,
        tropical=tropical,
        indoor=indoor,
        outdoor=outdoor,
        data_sources=data_sources or [],
        last_updated=datetime.utcnow()
    )
    
    db.session.add(plant)
    db.session.commit()
    
    return plant

def get_plants():
    """Return all plants."""
    return Plant.query.all()

def get_plant_by_id(plant_id):
    """Return a plant by ID."""
    return Plant.query.get(plant_id)

def get_plant_by_scientific_name(scientific_name):
    """Return a plant by scientific name."""
    return Plant.query.filter(Plant.scientific_name == scientific_name).first()

def search_plants(query):
    """Search for plants by name."""
    search_term = f"%{query}%"
    return Plant.query.filter(
        (Plant.scientific_name.ilike(search_term)) | 
        (Plant.common_name.ilike(search_term))
    ).all()

def filter_plants(plant_type=None, indoor=None, outdoor=None, poisonous=None, tropical=None):
    """Filter plants by various attributes."""
    query = Plant.query
    
    if plant_type:
        query = query.filter(Plant.plant_type == plant_type)
    
    if indoor is not None:
        query = query.filter(Plant.indoor == indoor)
    
    if outdoor is not None:
        query = query.filter(Plant.outdoor == outdoor)
    
    if poisonous is not None:
        query = query.filter((Plant.poisonous_to_humans == poisonous) | 
                            (Plant.poisonous_to_pets == poisonous))
    
    if tropical is not None:
        query = query.filter(Plant.tropical == tropical)
    
    return query.all()

def update_plant(plant_id, **kwargs):
    """Update plant details."""
    plant = Plant.query.get(plant_id)
    
    if not plant:
        return None
    
    for key, value in kwargs.items():
        if hasattr(plant, key):
            setattr(plant, key, value)
    
    plant.last_updated = datetime.utcnow()
    db.session.commit()
    return plant

def delete_plant(plant_id):
    """Delete a plant."""
    plant = Plant.query.get(plant_id)
    
    if not plant:
        return False
    
    db.session.delete(plant)
    db.session.commit()
    return True

# ----------------------------------------
# PlantCareDetails operations
# ----------------------------------------

def create_plant_care_details(plant_id, watering_frequency=None, watering_interval_days=None,
                            sunlight_requirements=None, sunlight_duration_min=None,
                            sunlight_duration_max=None, sunlight_duration_unit='hours',
                            soil_preferences=None, temperature_range=None,
                            fertilizing_schedule=None, pruning_months=None,
                            difficulty_level=None, growth_rate=None,
                            propagation_methods=None, companion_plants=None):
    """Create and return care details for a plant."""
    
    care_details = PlantCareDetails(
        plant_id=plant_id,
        watering_frequency=watering_frequency,
        watering_interval_days=watering_interval_days,
        sunlight_requirements=sunlight_requirements or [],
        sunlight_duration_min=sunlight_duration_min,
        sunlight_duration_max=sunlight_duration_max,
        sunlight_duration_unit=sunlight_duration_unit,
        soil_preferences=soil_preferences,
        temperature_range=temperature_range,
        fertilizing_schedule=fertilizing_schedule,
        pruning_months=pruning_months or [],
        difficulty_level=difficulty_level,
        growth_rate=growth_rate,
        propagation_methods=propagation_methods or [],
        companion_plants=companion_plants
    )
    
    db.session.add(care_details)
    db.session.commit()
    
    return care_details

def get_care_details_by_plant_id(plant_id):
    """Return care details for a specific plant."""
    return PlantCareDetails.query.filter(PlantCareDetails.plant_id == plant_id).first()

def update_plant_care_details(plant_id, **kwargs):
    """Update care details for a plant."""
    care_details = PlantCareDetails.query.filter(PlantCareDetails.plant_id == plant_id).first()
    
    if not care_details:
        return None
    
    for key, value in kwargs.items():
        if hasattr(care_details, key):
            setattr(care_details, key, value)
    
    db.session.commit()
    return care_details

# ----------------------------------------
# UserPlant operations
# ----------------------------------------

def create_user_plant(user_id, plant_id, nickname=None, location_in_home=None,
                    acquisition_date=None, image_url=None, notes=None, status='active'):
    """Create and return a user's plant."""
    
    user_plant = UserPlant(
        user_id=user_id,
        plant_id=plant_id,
        nickname=nickname,
        location_in_home=location_in_home,
        acquisition_date=acquisition_date or date.today(),
        image_url=image_url,
        notes=notes,
        status=status
    )
    
    db.session.add(user_plant)
    db.session.commit()
    
    return user_plant

def get_user_plants(user_id):
    """Return all plants for a specific user."""
    return UserPlant.query.filter(UserPlant.user_id == user_id).all()

def get_user_plant_by_id(user_plant_id):
    """Return a specific user plant by ID."""
    return UserPlant.query.get(user_plant_id)

def update_user_plant(user_plant_id, **kwargs):
    """Update a user's plant."""
    user_plant = UserPlant.query.get(user_plant_id)
    
    if not user_plant:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user_plant, key):
            setattr(user_plant, key, value)
    
    db.session.commit()
    return user_plant

def delete_user_plant(user_plant_id):
    """Delete a user's plant."""
    user_plant = UserPlant.query.get(user_plant_id)
    
    if not user_plant:
        return False
    
    db.session.delete(user_plant)
    db.session.commit()
    return True

# ----------------------------------------
# CareEvent operations
# ----------------------------------------

def create_care_event(user_plant_id, event_type, notes=None, date=None):
    """Create and return a care event."""
    
    care_event = CareEvent(
        user_plant_id=user_plant_id,
        event_type=event_type,
        date=date or datetime.utcnow(),
        notes=notes
    )
    
    db.session.add(care_event)
    db.session.commit()
    
    return care_event

def get_care_events_by_user_plant(user_plant_id):
    """Return all care events for a specific user plant."""
    return CareEvent.query.filter(CareEvent.user_plant_id == user_plant_id).order_by(CareEvent.date.desc()).all()

def get_recent_care_events(user_id, days=30):
    """Return recent care events for a user."""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    return CareEvent.query.join(UserPlant).filter(
        UserPlant.user_id == user_id,
        CareEvent.date >= since_date
    ).order_by(CareEvent.date.desc()).all()

# ----------------------------------------
# Reminder operations
# ----------------------------------------

def create_reminder(user_plant_id, reminder_type, frequency, next_reminder_date=None, is_active=True):
    """Create and return a reminder."""
    
    reminder = Reminder(
        user_plant_id=user_plant_id,
        reminder_type=reminder_type,
        frequency=frequency,
        next_reminder_date=next_reminder_date or date.today(),
        is_active=is_active
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    return reminder

def get_reminders_by_user_plant(user_plant_id):
    """Return all reminders for a specific user plant."""
    return Reminder.query.filter(Reminder.user_plant_id == user_plant_id).all()

def get_upcoming_reminders(user_id, days=7):
    """Return upcoming reminders for a user."""
    end_date = date.today() + timedelta(days=days)
    
    return Reminder.query.join(UserPlant).filter(
        UserPlant.user_id == user_id,
        Reminder.next_reminder_date <= end_date,
        Reminder.is_active == True
    ).order_by(Reminder.next_reminder_date).all()

def update_reminder(reminder_id, **kwargs):
    """Update a reminder."""
    reminder = Reminder.query.get(reminder_id)
    
    if not reminder:
        return None
    
    for key, value in kwargs.items():
        if hasattr(reminder, key):
            setattr(reminder, key, value)
    
    db.session.commit()
    return reminder

# ----------------------------------------
# HealthAssessment operations
# ----------------------------------------

def create_health_assessment(user_plant_id, symptoms=None, diagnosis=None, 
                           treatment_recommendations=None, image_url=None, resolved=False):
    """Create and return a health assessment."""
    
    assessment = HealthAssessment(
        user_plant_id=user_plant_id,
        assessment_date=datetime.utcnow(),
        symptoms=symptoms or [],
        diagnosis=diagnosis,
        treatment_recommendations=treatment_recommendations,
        image_url=image_url,
        resolved=resolved
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return assessment

def get_health_assessments_by_user_plant(user_plant_id):
    """Return all health assessments for a specific user plant."""
    return HealthAssessment.query.filter(HealthAssessment.user_plant_id == user_plant_id).order_by(HealthAssessment.assessment_date.desc()).all()

def update_health_assessment(assessment_id, **kwargs):
    """Update a health assessment."""
    assessment = HealthAssessment.query.get(assessment_id)
    
    if not assessment:
        return None
    
    for key, value in kwargs.items():
        if hasattr(assessment, key):
            setattr(assessment, key, value)
    
    db.session.commit()
    return assessment

# ----------------------------------------
# IdentificationHistory operations
# ----------------------------------------

def create_identification(user_id, image_url, identified_plant_id, 
                         confidence_score, user_plant_id=None, added_to_collection=False):
    """Create and return an identification record."""
    
    identification = IdentificationHistory(
        user_id=user_id,
        user_plant_id=user_plant_id,
        image_url=image_url,
        identified_plant_id=identified_plant_id,
        confidence_score=confidence_score,
        identified_at=datetime.utcnow(),
        added_to_collection=added_to_collection
    )
    
    db.session.add(identification)
    db.session.commit()
    
    return identification

def get_identifications_by_user(user_id):
    """Return all identifications for a specific user."""
    return IdentificationHistory.query.filter(IdentificationHistory.user_id == user_id).order_by(IdentificationHistory.identified_at.desc()).all()

def update_identification(identification_id, **kwargs):
    """Update an identification record."""
    identification = IdentificationHistory.query.get(identification_id)
    
    if not identification:
        return None
    
    for key, value in kwargs.items():
        if hasattr(identification, key):
            setattr(identification, key, value)
    
    db.session.commit()
    return identification

# ----------------------------------------
# PlantHealthIssue operations
# ----------------------------------------

def create_plant_health_issue(plant_id, issue_name, symptoms=None, 
                             treatment=None, prevention=None, severity=None):
    """Create and return a plant health issue."""
    
    health_issue = PlantHealthIssue(
        plant_id=plant_id,
        issue_name=issue_name,
        symptoms=symptoms,
        treatment=treatment,
        prevention=prevention,
        severity=severity
    )
    
    db.session.add(health_issue)
    db.session.commit()
    
    return health_issue

def get_health_issues_by_plant(plant_id):
    """Return all health issues for a specific plant."""
    return PlantHealthIssue.query.filter(PlantHealthIssue.plant_id == plant_id).all()

# ----------------------------------------
# UserFavorite operations
# ----------------------------------------

def create_user_favorite(user_id, plant_id):
    """Create and return a user favorite."""
    
    # Check if already favorited
    existing = UserFavorite.query.filter(
        UserFavorite.user_id == user_id,
        UserFavorite.plant_id == plant_id
    ).first()
    
    if existing:
        return existing
    
    favorite = UserFavorite(
        user_id=user_id,
        plant_id=plant_id,
        favorited_at=datetime.utcnow()
    )
    
    db.session.add(favorite)
    db.session.commit()
    
    return favorite

def get_user_favorites(user_id):
    """Return all favorites for a specific user."""
    return UserFavorite.query.filter(UserFavorite.user_id == user_id).all()

def delete_user_favorite(user_id, plant_id):
    """Delete a user favorite."""
    favorite = UserFavorite.query.filter(
        UserFavorite.user_id == user_id,
        UserFavorite.plant_id == plant_id
    ).first()
    
    if not favorite:
        return False
    
    db.session.delete(favorite)
    db.session.commit()
    return True

# ----------------------------------------
# Region operations
# ----------------------------------------

def create_region(name, climate_zone=None, avg_temperature=None, humidity_level=None):
    """Create and return a region."""
    
    region = Region(
        name=name,
        climate_zone=climate_zone,
        avg_temperature=avg_temperature,
        humidity_level=humidity_level
    )
    
    db.session.add(region)
    db.session.commit()
    
    return region

def get_regions():
    """Return all regions."""
    return Region.query.all()

def get_region_by_id(region_id):
    """Return a region by ID."""
    return Region.query.get(region_id)

# ----------------------------------------
# PlantRegionCare operations
# ----------------------------------------

def create_plant_region_care(plant_id, region_id, watering_frequency=None, 
                           sunlight_adjustments=None, seasonal_notes=None):
    """Create and return region-specific plant care."""
    
    plant_region_care = PlantRegionCare(
        plant_id=plant_id,
        region_id=region_id,
        watering_frequency=watering_frequency,
        sunlight_adjustments=sunlight_adjustments,
        seasonal_notes=seasonal_notes
    )
    
    db.session.add(plant_region_care)
    db.session.commit()
    
    return plant_region_care

def get_plant_region_care(plant_id, region_id):
    """Return region-specific care for a plant."""
    return PlantRegionCare.query.filter(
        PlantRegionCare.plant_id == plant_id,
        PlantRegionCare.region_id == region_id
    ).first()

# ----------------------------------------
# RelatedPlant operations
# ----------------------------------------

def create_related_plants(plant_id_1, plant_id_2, relationship_type, notes=None):
    """Create and return a relationship between plants."""
    
    # Check if relationship already exists
    existing = RelatedPlant.query.filter(
        ((RelatedPlant.plant_id_1 == plant_id_1) & (RelatedPlant.plant_id_2 == plant_id_2)) |
        ((RelatedPlant.plant_id_1 == plant_id_2) & (RelatedPlant.plant_id_2 == plant_id_1))
    ).first()
    
    if existing:
        return existing
    
    related_plant = RelatedPlant(
        plant_id_1=plant_id_1,
        plant_id_2=plant_id_2,
        relationship_type=relationship_type,
        notes=notes
    )
    
    db.session.add(related_plant)
    db.session.commit()
    
    return related_plant

def get_related_plants(plant_id):
    """Return all plants related to a specific plant."""
    
    related_as_1 = RelatedPlant.query.filter(RelatedPlant.plant_id_1 == plant_id).all()
    related_as_2 = RelatedPlant.query.filter(RelatedPlant.plant_id_2 == plant_id).all()
    
    # Combine both sets of relationships
    related_plants = []
    
    for relation in related_as_1:
        related_plants.append({
            'related_id': relation.related_id,
            'plant_id': relation.plant_id_2,
            'relationship_type': relation.relationship_type,
            'notes': relation.notes
        })
    
    for relation in related_as_2:
        related_plants.append({
            'related_id': relation.related_id,
            'plant_id': relation.plant_id_1,
            'relationship_type': relation.relationship_type,
            'notes': relation.notes
        })
    
    return related_plants

# ----------------------------------------
# Test functions
# ----------------------------------------

def run_crud_tests():
    """Run tests for CRUD operations."""
    
    print("Testing CRUD operations...")
    
    # Create test user
    print("\nCreating test user...")
    test_user = create_user("testuser", "test@example.com", "password123")
    print(f"Created user: {test_user}")
    
    # Create test region
    print("\nCreating test region...")
    test_region = create_region("Test Region", "7-9", 65.0, "Moderate")
    print(f"Created region: {test_region}")
    
    # Create test plant
    print("\nCreating test plant...")
    test_plant = create_plant(
        scientific_name="Testus plantus",
        common_name="Test Plant",
        plant_type="Indoor",
        description="A plant for testing",
        indoor=True,
        data_sources=["test"]
    )
    print(f"Created plant: {test_plant}")
    
    # Create plant care details
    print("\nCreating plant care details...")
    test_care = create_plant_care_details(
        plant_id=test_plant.plant_id,
        watering_frequency="Weekly",
        watering_interval_days=7,
        sunlight_requirements=["Bright indirect"],
        difficulty_level="Easy"
    )
    print(f"Created care details: {test_care}")
    
    # Add plant to user's collection
    print("\nAdding plant to user's collection...")
    test_user_plant = create_user_plant(
        user_id=test_user.user_id,
        plant_id=test_plant.plant_id,
        nickname="My Test Plant",
        location_in_home="Living Room"
    )
    print(f"Added plant to collection: {test_user_plant}")
    
    # Add care event
    print("\nAdding care event...")
    test_event = create_care_event(
        user_plant_id=test_user_plant.user_plant_id,
        event_type="Watering",
        notes="First watering"
    )
    print(f"Added care event: {test_event}")
    
    # Create reminder
    print("\nCreating reminder...")
    test_reminder = create_reminder(
        user_plant_id=test_user_plant.user_plant_id,
        reminder_type="Watering",
        frequency="Weekly",
        next_reminder_date=date.today() + timedelta(days=7)
    )
    print(f"Created reminder: {test_reminder}")
    
    # Add health assessment
    print("\nCreating health assessment...")
    test_assessment = create_health_assessment(
        user_plant_id=test_user_plant.user_plant_id,
        symptoms=["Yellow leaves", "Drooping"],
        diagnosis="Overwatering",
        treatment_recommendations="Allow soil to dry out completely before watering again."
    )
    print(f"Created health assessment: {test_assessment}")
    
    # Test queries
    print("\nTesting queries...")
    
    # Get user by email
    print(f"User by email: {get_user_by_email('test@example.com')}")
    
    # Get plant by ID
    print(f"Plant by ID: {get_plant_by_id(test_plant.plant_id)}")
    
    # Get user plants
    print(f"User plants: {get_user_plants(test_user.user_id)}")
    
    # Get care events
    print(f"Care events: {get_care_events_by_user_plant(test_user_plant.user_plant_id)}")
    
    # Get upcoming reminders
    print(f"Upcoming reminders: {get_upcoming_reminders(test_user.user_id)}")
    
    # Update user plant
    print("\nUpdating user plant...")
    updated_plant = update_user_plant(
        test_user_plant.user_plant_id,
        nickname="Updated Test Plant",
        notes="This plant has been updated"
    )
    print(f"Updated plant: {updated_plant}")
    
    print("\nCRUD testing complete!")
    
    # Clean up test data - uncomment if you want to remove test data after running
    # delete_user_plant(test_user_plant.user_plant_id)
    # delete_plant(test_plant.plant_id)
    # delete_user(test_user.user_id)
    
    return True


if __name__ == "__main__":
    """Run CRUD tests when executed directly."""
    
    from server import app
    connect_to_db(app)
    
    run_crud_tests()