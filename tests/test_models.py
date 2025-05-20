import unittest
from datetime import datetime, timedelta
from server import app
from model import db, connect_to_db
import crud

class ModelTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rootly_test'
        self.client = app.test_client()
        
        # Fix #1: Avoid calling connect_to_db() which causes the duplicate registration
        # Instead, just create the tables within the app context
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_operations(self):
        """Test user CRUD operations."""
        # Fix #2: Wrap all database operations in an app context
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
        # Fix #2: Wrap all database operations in an app context
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

if __name__ == '__main__':
    unittest.main()import unittest
from datetime import datetime, timedelta
from server import app
from model import connect_to_db, db
import crud

class ModelTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rootly_test'
        self.client = app.test_client()
        
        with app.app_context():
            connect_to_db(app)
            db.create_all()
    
    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_operations(self):
        """Test user CRUD operations."""
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

if __name__ == '__main__':
    unittest.main()
