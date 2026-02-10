"""
Pytest configuration and shared fixtures for OpenHarmony open source tools tests.
"""
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_reference_data():
    """Sample reference data for testing OpenSourceValidator."""
    return [
        {
            "Name": "Software A",
            "License": "MIT",
            "Version Number": "1.0.0",
            "Upstream URL": "https://example.com"
        }
    ]
