import unittest
import time
from server import app
from model import connect_to_db, db
import crud

class PerformanceTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rootly_test'
        self.client = app.test_client()
        
        with app.app_context():
            connect_to_db(app)
            db.create_all()
            
            # Create multiple plants for performance testing
            for i in range(10):  # Limiting to 10 for quicker tests
                crud.create_plant(
                    scientific_name=f"Performance Plant {i}",
                    common_name=f"Test Plant {i}",
                    indoor=True
                )
    
    def tearDown(self):
        """Clean up after test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_search_performance(self):
        """Test search performance."""
        start_time = time.time()
        results = crud.search_plants("Performance")
        end_time = time.time()
        
        self.assertGreaterEqual(len(results), 5)  # Should find most of our test plants
        search_time = end_time - start_time
        self.assertLess(search_time, 0.5)  # Should execute in under 500ms
    
    def test_plants_page_load_time(self):
        """Test plants page load time."""
        start_time = time.time()
        response = self.client.get('/plants')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        load_time = end_time - start_time
        self.assertLess(load_time, 1.0)  # Should load in under 1 second

if __name__ == '__main__':
    unittest.main()
