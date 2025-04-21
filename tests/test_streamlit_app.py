# Create a new directory for tests
# Add a test file for streamlit_app.py

# tests/test_streamlit_app.py
import sys
import os
import warnings

# Suppress specific DeprecationWarning in tests
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"datetime.datetime.utcfromtimestamp\(\) is deprecated"
)

# Add the parent directory to the Python path to resolve the import issue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from streamlit_app import generate_mystery, get_daily_mystery, get_weekly_mysteries

@patch('streamlit_app.collection')
def test_get_daily_mystery(mock_collection):
    # Mock MongoDB collection behavior
    mock_collection.find_one.return_value = {
        "date": "2025-04-21",
        "mystery": "Test Mystery",
        "answer": "Test Answer"
    }

    result = get_daily_mystery()
    assert result["date"] == "2025-04-21"
    assert result["mystery"] == "Test Mystery"
    assert result["answer"] == "Test Answer"

@patch('streamlit_app.collection')
def test_get_weekly_mysteries(mock_collection):
    # Mock MongoDB collection behavior
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = [
        {
            "date": "2025-04-20",
            "mystery": "Weekly Mystery 1",
            "answer": "Answer 1"
        },
        {
            "date": "2025-04-19",
            "mystery": "Weekly Mystery 2",
            "answer": "Answer 2"
        }
    ]
    mock_collection.find.return_value = mock_cursor

    result = get_weekly_mysteries()
    assert len(result) == 2
    assert result[0]["date"] == "2025-04-20"
    assert result[1]["date"] == "2025-04-19"

@patch('streamlit_app.genai.Client')
def test_generate_mystery(mock_genai_client):
    # Mock Gemini AI client behavior
    mock_response = MagicMock()
    mock_response.text = "Mystery: Test Mystery\nAnswer: Test Answer"
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    result = generate_mystery()
    assert result["mystery"] == "Mystery: Test Mystery"
    assert result["answer"] == "Test Answer"