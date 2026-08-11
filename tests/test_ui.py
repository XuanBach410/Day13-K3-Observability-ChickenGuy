from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ui_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "ChickenGuy AI Observer" in response.text
