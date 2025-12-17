import os
import sys
from dotenv import load_dotenv

def load_config():
    """
    Loads environment variables based on the current context.
    If running tests (detected via TESTING env var or pytest in modules),
    loads .env_test. Otherwise, loads .env.
    """
    # Check for explicit testing environment variable
    is_testing_env = os.environ.get("TESTING", "false").lower() == "true"
    
    # Check if running under pytest
    is_pytest = "pytest" in sys.modules
    
    if is_testing_env or is_pytest:
        # Determine the path to .env_test relative to this file
        # This file is in backend/src/config.py
        # We want to find backend/.env_test
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_test_path = os.path.join(base_dir, '.env_test')
        
        # Fallback to just .env_test if the calculated path doesn't exist
        # (e.g. if structure is different than expected)
        path_to_load = env_test_path if os.path.exists(env_test_path) else '.env_test'
        
        # print(f"Loading test configuration from {path_to_load}")
        load_dotenv(path_to_load, override=True)
    else:
        # Standard load_dotenv looks for .env
        load_dotenv()

# Load configuration immediately upon import
load_config()
