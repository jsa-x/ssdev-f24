from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuration for MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'jesus'
app.config['MYSQL_PASSWORD'] = 'CyberSec@24'
app.config['MYSQL_DB'] = 'keyboard_store'

# Initialize MySQL connection
mysql = MySQL(app)

# Secret key for session management
app.config['SECRET_KEY'] = 'cybersecurity'

# Default route to redirect to login page
@app.route('/')
def home():
    return redirect(url_for('login'))

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    # Simulate fetching user data (username and email from the session for now)
    if 'user' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))

    user = session['user']  # Assuming user details are stored in session after login

    # Sample user dashboard data (could later be expanded with actual orders, etc.)
    return render_template('dashboard.html', user=user)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Fetch the form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Check if the email is already registered
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        existing_user = cur.fetchone()

        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        # Insert the new user into the database
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                    (username, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']  # Fetch the username from the form
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])  # Query by username
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user'] = {'username': user[1], 'email': user[2]}  # Store username and email in session
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


# Palcehodlers for products sold
@app.route('/catalog')
def catalog():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    
    # Map the database fields to product keys
    products_list = []
    for product in products:
        products_list.append({
            'name': product[1],
            'description': product[2],
            'price': f"${product[3]:.2f}",
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
