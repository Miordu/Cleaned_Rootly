import unittest
from datetime import datetime, timedelta
from server import app
from model import db
import crud

class ModelTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rootly_test'
        self.client = app.test_client()
        
        # Create tables within app context
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_operations(self):
        """Test user CRUD operations."""
        with app.app_context():
            # Create user
            user = crud.create_user("testuser", "test@example.com", "password123")
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "testuser")
            
            # Read user
            retrieved_user = crud.get_user_by_email("test@example.com")
            self.assertEqual(retrieved_user.user_id, user.user_id)
            
            # Update user
            updated_user = crud.update_user(user.user_id, username="updateduser")
            self.assertEqual(updated_user.username, "updateduser")
            
            # Delete user
            result = crud.delete_user(user.user_id)
            self.assertTrue(result)
            self.assertIsNone(crud.get_user_by_id(user.user_id))
    
    def test_plant_operations(self):
        """Test plant CRUD operations."""
        with app.app_context():
            # Create plant
            plant = crud.create_plant(
                scientific_name="Test Plant",
                common_name="Common Test Plant",
                indoor=True
            )
            self.assertIsNotNone(plant)
            
            # Read plant
            retrieved_plant = crud.get_plant_by_scientific_name("Test Plant")
            self.assertEqual(retrieved_plant.plant_id, plant.plant_id)
            
            # Test search functionality
            search_results = crud.search_plants("Test")
            self.assertGreaterEqual(len(search_results), 1)
            
            # Test filter functionality
            filter_results = crud.filter_plants(indoor=True)
            self.assertGreaterEqual(len(filter_results), 1)
            
            # Update plant
            updated_plant = crud.update_plant(plant.plant_id, description="Updated description")
            self.assertEqual(updated_plant.description, "Updated description")
    
    def test_care_details_operations(self):
        """Test plant care details operations."""
        with app.app_context():
            # Create plant first
            plant = crud.create_plant("Test Plant For Care")
            
            # Create care details
            care_details = crud.create_plant_care_details(
                plant_id=plant.plant_id,
                watering_frequency="Weekly",
                sunlight_requirements=["Bright indirect"],
                difficulty_level="Easy"
            )
            self.assertIsNotNone(care_details)
            
            # Read care details
            retrieved_details = crud.get_care_details_by_plant_id(plant.plant_id)
            self.assertEqual(retrieved_details.watering_frequency, "Weekly")
            
            # Update care details
            updated_details = crud.update_plant_care_details(
                plant.plant_id, 
                watering_frequency="Bi-weekly"
            )
            self.assertEqual(updated_details.watering_frequency, "Bi-weekly")

if __name__ == '__main__':
    unittest.main()
    
    
    
        
    
