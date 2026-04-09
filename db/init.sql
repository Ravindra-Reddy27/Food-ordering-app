-- db/init.sql

-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

-- Create Menu Items Table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(5, 2)
);

-- Create Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item_id INTEGER REFERENCES items(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Insert a default Admin user (password should be hashed in production, using plain text for initial testing setup)
-- We will use 'admin123' as a placeholder password hash for now.
-- INSERT INTO users (username, password_hash, role) VALUES ('Ravi', 'admin123', 'admin');

-- Insert some default food items
INSERT INTO items (item_name, description, price) VALUES 
('Margherita Pizza', 'Classic cheese and tomato pizza', 12.99),
('Chicken Biryani', 'Aromatic rice dish with spiced chicken', 14.50),
('Paneer Tikka Masala', 'Grilled paneer in a spicy gravy', 11.00);