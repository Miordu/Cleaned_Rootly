import unittest
import sys

# Import all test modules
from tests.test_models import ModelTests
from tests.test_integration import IntegrationTests
from tests.test_routes import RouteTests
from tests.test_performance import PerformanceTests

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(ModelTests))
    test_suite.addTest(unittest.makeSuite(IntegrationTests))
    test_suite.addTest(unittest.makeSuite(RouteTests))
    test_suite.addTest(unittest.makeSuite(PerformanceTests))
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Return proper exit code
    sys.exit(not result.wasSuccessful())
