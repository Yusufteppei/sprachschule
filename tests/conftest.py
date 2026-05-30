import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_story_agent

# 1. Create a Mock Agent
class MockStoryteller:
    async def run(self, level: str):
        return {"text": "Once upon a time in Berlin...", "level": level}

# 2. The Fixture to override dependencies
@pytest.fixture
def client():
    # Override the real agent with our mock
    app.dependency_overrides[get_story_agent] = lambda: MockStoryteller()
    with TestClient(app) as c:
        yield c
    # Clean up after the test
    app.dependency_overrides.clear()