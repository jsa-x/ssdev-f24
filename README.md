## Introduction

The **Keyboard Store Web Application** is a Flask-based project designed to simulate a functional online store specializing in keyboards. Users can browse products, manage their carts and wishlists, and complete purchases. Admins have access to user management and role assignment features. The project prioritizes security, user experience, and scalability.

---

## Features

### User Features:
- **Registration and Login**: Secure account creation and authentication.
- **Browse Catalog**: View product listings with details.
- **Shopping Cart**: Add, update, or remove items.
- **Wishlist Management**: Save favorite items for later.
- **Profile Management**: Edit user details and change passwords.

### Admin Features:
- **Admin Panel**: Manage users and view all accounts.
- **Role Management**: Update user roles to control access.

---

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, Jinja2 Templates, CSS (Bulma Framework)
- **Database**: MySQL
- **Security**:
  - CSRF Protection (`flask-wtf`)
  - Rate Limiting (`flask-limiter`)
  - Password Hashing (`werkzeug.security`)
---
#### Prerequisites
1. **System Requirements**:
   - Python 3.8 or higher
   - MySQL Server
   - Redis Server (for rate limiting)

2. **Dependencies**:
   Install Python dependencies:
   pip install -r requirements.txt
   
## Deployment Instructions

 ** Database Configuration:**
  1. Create a MySQL database:
  2. CREATE DATABASE keyboard_store;
  **Import the provided schema:**
  1. mysql -u <username> -p keyboard_store < schema.sql
  **Environment Variables: Set up a config.py file with the following:**
  1. MYSQL_HOST = 'localhost'
  2. MYSQL_USER = 'root'
  3. MYSQL_PASSWORD = 'your_password'
  4. MYSQL_DB = 'keyboard_store'
  5. SECRET_KEY = 'your_secret_key'
  
  **Running Locally**
**Clone the repository:**
1. git clone https://github.com/jsa-x/dga-utrgv24.git
2. cd keyboard_store
**Start the Redis server:**
1. redis-server
**Run the application:**
1. flask run
**Access the app:**
1. Visit http://127.0.0.1:5000 in your browser.

**Prerequisites for server**
A Linux server Ubuntu 20.04 or later
Gunicorn as the WSGI server.
Nginx as the web server.

**Install Dependencies:**
1. sudo apt update
2. sudo apt install python3-pip python3-venv mysql-server redis-server nginx
**Clone and Setup:**
1. git clone https://github.com/jsa-x/dga-utrgv24.git
2. cd keyboard_store
3. python3 -m venv venv
4. source venv/bin/activate
5. pip install -r requirements.txt
