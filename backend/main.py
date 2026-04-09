# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware 
import os

app = FastAPI(title="Food Booking API")

# --- Add this CORS block ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    try:
        # We use the service name "db" defined in docker-compose.yml as the host
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("DB_NAME", "foodbooking"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "secretpassword")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# --- Data Models (for receiving data from the frontend) ---
class UserAuth(BaseModel):
    username: str
    password: str

class OrderRequest(BaseModel):
    user_id: int
    item_id: int

# 1. New Model for completing orders
class CompleteOrderReq(BaseModel):
    username: str
    
# --- API Endpoints ---

@app.post("/signup")
def signup(user: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash password and insert
    hashed_password = pwd_context.hash(user.password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'user')",
            (user.username, hashed_password)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error creating user")
    finally:
        cursor.close()
        conn.close()
        
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
    db_user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_user or not pwd_context.verify(user.password, db_user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Return the user info and role so the frontend knows where to redirect
    return {
        "message": "Login successful", 
        "user_id": db_user['id'], 
        "username": db_user['username'], 
        "role": db_user['role']
    }

@app.get("/items")
def get_items():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

@app.post("/order")
def place_order(order: OrderRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, item_id) VALUES (%s, %s)",
        (order.user_id, order.item_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Order placed successfully"}

    
# 2. Updated GET route with filters for "today" vs "history"
@app.get("/admin/orders")
def get_all_orders(filter: str = 'today'):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if filter == 'history':
        # Show ONLY completed orders (History)
        query = """
            SELECT orders.id, users.username, items.item_name, orders.order_date, orders.status 
            FROM orders
            JOIN users ON orders.user_id = users.id
            JOIN items ON orders.item_id = items.id
            WHERE orders.status = 'completed'
            ORDER BY orders.order_date DESC
        """
    else:
        # Show ONLY pending orders from TODAY
        query = """
            SELECT orders.id, users.username, items.item_name, orders.order_date, orders.status 
            FROM orders
            JOIN users ON orders.user_id = users.id
            JOIN items ON orders.item_id = items.id
            WHERE orders.status = 'pending' AND DATE(orders.order_date) = CURRENT_DATE
            ORDER BY orders.order_date DESC
        """
        
    cursor.execute(query)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

# 3. New PUT route to update order status
@app.put("/admin/orders/complete")
def complete_orders(req: CompleteOrderReq):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Update all pending orders for this specific user to 'completed'
    query = """
        UPDATE orders 
        SET status = 'completed' 
        WHERE status = 'pending' 
        AND user_id = (SELECT id FROM users WHERE username = %s)
    """
    try:
        cursor.execute(query, (req.username,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update orders")
    finally:
        cursor.close()
        conn.close()
        
    return {"message": "Orders marked as completed"}