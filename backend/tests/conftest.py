import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def set_testing_env():
    """
    Automatically set the TESTING environment variable for all tests.
    """
    os.environ["TESTING"] = "true"
