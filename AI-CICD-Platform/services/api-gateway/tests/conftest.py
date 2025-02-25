import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)
