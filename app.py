# SSDEV - 4326
# Jesus Sanchez, Edison Amigon, Sergio Bautista
# Secure Keyboard Store

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import re
import config  # Import the configuration file
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from functools import wraps  # Import wraps
from flask import abort 

app = Flask(__name__)

csrf = CSRFProtect(app)

# Flask-Limiter Configuration
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="redis://localhost:6379"
)

# Config from config.py
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['SECRET_KEY'] = config.SECRET_KEY

# Initialize MySQL connection
mysql = MySQL(app)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Secret key for session management
#app.config['SECRET_KEY'] = 'cybersecurity'

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.error(f"CSRF Error: {e.description}")
    flash("The form submission has expired or is invalid. Please try again.", "danger")
    return redirect(url_for('home'))

# Utility function for role-based access
def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the user is logged in
            if 'user' not in session:
                flash('You need to log in first!', 'danger')
                return redirect(url_for('login'))
            
            # Check if the user has the required role
            if session['user'].get('role') != required_role:
                flash('You do not have access to this page.', 'danger')
                return abort(403)  # HTTP 403 Forbidden
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Default route to redirect to login page
@app.route('/')
def home():
    return redirect(url_for('login'))

# Dashboard Route (Accessible to all authenticated users)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    user = session['user']
    return render_template('dashboard.html', user=user)

# Admin Panel Route (Only admins can access)
@app.route('/admin')
@role_required('admin')
def admin_panel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email, role FROM users")  # Fetch all users
    users = cur.fetchall()
    cur.close()

    # Convert users to a list of dictionaries for easy rendering in Jinja2
    users_list = [
        {'id': user[0], 'username': user[1], 'email': user[2], 'role': user[3]}
        for user in users
    ]
    return render_template('admin_panel.html', users=users_list)

def is_password_strong(password):
    """
    Checks if the password meets the following criteria:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if (len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
        return True
    return False

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not is_password_strong(password):
            flash('Password must be at least 8 characters long, include uppercase, lowercase, a number, and a special character.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        existing_user = cur.fetchone()

        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", 
                    (username, email, hashed_password, 'user'))  # Default role: 'user'
        mysql.connection.commit()
        cur.close()

        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user'] = {'id': user[0], 'username': user[1], 'email': user[2], 'role': user[4]}
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

#logging out function
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    # Ensure the user is logged in
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    
    user = session['user']  # Assuming user details are stored in the session

    # Render the profile page with user details
    return render_template('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    
    user = session['user']

    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        cur = mysql.connection.cursor()

        # Update username and email
        cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", 
                    (new_username, new_email, user['id']))
        
        # If the user wants to change their password
        if current_password and new_password:
            # Fetch current hashed password from the database
            cur.execute("SELECT password FROM users WHERE id = %s", [user['id']])
            db_password = cur.fetchone()[0]

            # Verify the current password
            if not check_password_hash(db_password, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('edit_profile'))

            # Validate new password strength
            if not is_password_strong(new_password):
                flash('New password must meet complexity requirements.', 'danger')
                return redirect(url_for('edit_profile'))

            # Hash the new password and update it in the database
            hashed_password = generate_password_hash(new_password)
            cur.execute("UPDATE users SET password = %s WHERE id = %s", 
                        (hashed_password, user['id']))
            flash('Password updated successfully!', 'success')

        mysql.connection.commit()
        cur.close()

        # Update session with new information
        session['user'] = {
            'id': user['id'],
            'username': new_username,
            'email': new_email,
            'role': user['role']  # Preserve role
        }
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)


# Admin: View Users and Manage Roles
@app.route('/admin/manage_users')
@role_required('admin')  # Ensure only admins can access this route
def manage_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email, role FROM users")  # Fetch user data
    users = cur.fetchall()
    cur.close()
    return render_template('manage_users.html', users=users)

# Admin: Update User Role
@app.route('/update_role/<int:user_id>', methods=['POST'])
@role_required('admin')  # Only accessible by admins
def update_role(user_id):
    new_role = request.form['role']

    # Ensure the role is valid (either 'user' or 'admin')
    if new_role not in ['user', 'admin']:
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('admin_panel'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    mysql.connection.commit()
    cur.close()

    flash('User role updated successfully!', 'success')
    return redirect(url_for('admin_panel'))


# Palcehodlers for products sold
@app.route('/catalog')
def catalog():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    
    # Map the database fields to product keys and ensure price is a float
    products_list = []
    for product in products:
        products_list.append({
            'name': product[1],
            'description': product[2],
            'price': float(product[3]),  # Convert price to float
            'image_url': product[4]
        })
    
    return render_template('catalog.html', products=products_list)

# Product Detail Route
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", [product_id])
    product = cur.fetchone()
    cur.close()

    if product:
        product_data = {
            'id': product[0],  # Ensure 'id' is passed to the template
            'name': product[1],
            'description': product[2],
            'price': f"${product[3]:.2f}",
            'image_url': product[4]
        }
        return render_template('product_detail.html', product=product_data)
    else:
        flash('Product not found!', 'danger')
        return redirect(url_for('catalog'))
    

# Shopping Cart Route
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    # Convert price and quantity to float and int respectively to avoid any type mismatch
    total = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


# Add to Cart Route
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", [product_id])
    product = cur.fetchone()
    cur.close()

    if product:
        item = {
    'id': product[0],
    'name': product[1],
    'price': float(product[3]),  # Make sure price is a float
    'quantity': 1,
    'image_url': product[4]
}


        # Initialize the cart if it's empty
        if 'cart' not in session:
            session['cart'] = []

        # Check if the product is already in the cart
        for cart_item in session['cart']:
            if cart_item['id'] == product_id:
                cart_item['quantity'] += 1
                break
        else:
            session['cart'].append(item)

        session.modified = True
        flash('Product added to cart!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

# Remove from Cart Route
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_items = session.get('cart', [])
    session['cart'] = [item for item in cart_items if item['id'] != product_id]
    session.modified = True
    flash('Product removed from cart.', 'success')
    return redirect(url_for('cart'))

# Checkout Route
@app.route('/checkout')
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('catalog'))

    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

# Confirm Order Route
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('catalog'))

    # Clear the cart (Simulate purchase)
    session.pop('cart', None)
    session.modified = True

    flash('Thank you for your purchase!', 'success')
    return redirect(url_for('thank_you'))

# Thank You Page Route
@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

# Wishlist Route
@app.route('/wishlist')
def wishlist():
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT products.id, products.name, products.price, products.image_url 
        FROM wishlist 
        JOIN products ON wishlist.product_id = products.id 
        WHERE wishlist.user_id = %s
    """, [user_id])
    wishlist_items = cur.fetchall()
    cur.close()
    
    # Convert each item to a dictionary
    wishlist_items = [
        {'id': item[0], 'name': item[1], 'price': item[2], 'image_url': item[3]}
        for item in wishlist_items
    ]
    
    return render_template('wishlist.html', wishlist_items=wishlist_items)


@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    cur = mysql.connection.cursor()
    
    # Check if the product is already in the wishlist
    cur.execute("SELECT * FROM wishlist WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    existing_entry = cur.fetchone()
    
    if existing_entry:
        flash('This item is already in your wishlist!', 'info')
    else:
        cur.execute("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
        mysql.connection.commit()
        flash('Added to your wishlist!', 'success')
    
    cur.close()
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM wishlist WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Removed from your wishlist.', 'info')
    return redirect(url_for('wishlist'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
