#!/bin/bash
# 1. Wait a few seconds to ensure the backend and DB containers are fully awake
echo "Waiting 10 seconds for containers to initialize..."
sleep 10

# 2. Hit the signup API to securely hash the password and create the user
echo "Creating user Ravi via API..."
curl -s -X POST http://food_app_backend:8000/signup \
     -H "Content-Type: application/json" \
     -d '{"username": "Ravi", "password": "admin123"}'

# 3. Promote the user to an Admin directly in the database
echo "Promoting Ravi to admin role..."
sudo docker exec food_app_db psql -U admin -d foodbooking -c "UPDATE users SET role = 'admin' WHERE username = 'Ravi';"

echo "Admin setup complete!"