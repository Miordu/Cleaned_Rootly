import unittest
from datetime import datetime, timedelta
from server import app
from model import connect_to_db, db
import crud

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rootly_test'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.client = app.test_client()
        
        with app.app_context():
            connect_to_db(app)
            db.create_all()
            
            # Create test user and plant
            self.user = crud.create_user("testuser", "test@example.com", "password123")
            self.plant = crud.create_plant(
                scientific_name="Test Integration Plant",
                common_name="TIP",
                indoor=True
            )
            crud.create_plant_care_details(
                plant_id=self.plant.plant_id,
                watering_frequency="Weekly"
            )
    
    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_plant_care_workflow(self):
        """Test the full plant care workflow."""
        with app.app_context():
            # Add plant to user's collection
            user_plant = crud.create_user_plant(
                user_id=self.user.user_id,
                plant_id=self.plant.plant_id,
                nickname="My Test Plant"
            )
            self.assertIsNotNone(user_plant)
            
            # Create care event
            care_event = crud.create_care_event(
                user_plant_id=user_plant.user_plant_id,
                event_type="Watering",
                notes="Initial watering"
            )
            self.assertIsNotNone(care_event)
            
            # Create reminder
            reminder = crud.create_reminder(
                user_plant_id=user_plant.user_plant_id,
                reminder_type="Watering",
                frequency="Weekly",
                next_reminder_date=datetime.now().date() + timedelta(days=7)
            )
            self.assertIsNotNone(reminder)
            
            # Verify we can retrieve upcoming reminders
            upcoming = crud.get_upcoming_reminders(self.user.user_id)
            self.assertGreaterEqual(len(upcoming), 1)

if __name__ == '__main__':
    unittest.main()
