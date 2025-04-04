import unittest
import sys
from pathlib import Path

# Add the root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

def run_tests():
    """Discover and run all tests in the Tests directory"""
    # Initialize the test loader
    loader = unittest.TestLoader()
    
    # Discover all tests in the current directory
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Initialize the test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the test suite
    result = runner.run(suite)
    
    # Return 0 if all tests passed, 1 otherwise
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    import os
    sys.exit(run_tests()) 