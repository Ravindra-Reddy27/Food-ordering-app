# backend/test_main.py
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

# Generate unique credentials for this specific test run
test_username = f"testuser_{uuid.uuid4().hex[:8]}"
test_password = "securepassword123"
test_user_id = None  # We will save this during login to use for ordering

def test_read_openapi_docs():
    response = client.get("/openapi.json")
    assert response.status_code == 200

def test_read_items():
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_signup():
    """Test the registration flow."""
    response = client.post(
        "/signup",
        json={"username": test_username, "password": test_password}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"

def test_login():
    """Test the login flow and capture the user_id."""
    global test_user_id
    response = client.post(
        "/login",
        json={"username": test_username, "password": test_password}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "user_id" in data
    
    # Save the user ID for the next test
    test_user_id = data["user_id"]

def test_place_order():
    """Test placing an order using the logged-in user's ID."""
    # We use item_id: 1 because we know Margherita Pizza was created by init.sql
    response = client.post(
        "/order",
        json={"user_id": test_user_id, "item_id": 1}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Order placed successfully"

def test_get_admin_orders():
    """Test the admin dashboard endpoint."""
    response = client.get("/admin/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)