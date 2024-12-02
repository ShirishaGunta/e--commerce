from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Message
from flask_mail import Mail
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session management
app.config['MAIL_USERNAME'] = 'shirishagunta3@gmail.com'
app.config['MAIL_PASSWORD'] = 'zfoq klpt qfqb iyrr'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
# Database Setup
def setup_database():
    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()
    # cursor.execute('DROP TABLE IF EXISTS users;')

    # Create Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
  );''')
    
    # Create Products Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    image_url TEXT,
    category TEXT
);
''')

    # Create Orders Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        total_price REAL NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(user_id),
                        FOREIGN KEY(product_id) REFERENCES products(product_id)
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
''')
#     cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
#     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     order_date TEXT NOT NULL,
#     total_amount REAL NOT NULL,
#     FOREIGN KEY (user_id) REFERENCES users(user_id)
# );
# ''')
#     cursor.execute('''CREATE TABLE orders (
#     order_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     order_date TEXT NOT NULL,
#     total_amount REAL NOT NULL,
#     FOREIGN KEY (user_id) REFERENCES users(user_id)
# );
# ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS order_details (
    order_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
''')

    # Prepopulate Products
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
  
       cursor.execute('''
    INSERT INTO products (product_name, description, price, image_url, category)
    VALUES 
        ('Smartphone', 'Latest Android smartphone', 699.99, '/static/images/smartphone.jpg', 'Electronics'),
        ('Laptop', 'High-performance laptop', 1299.99, '/static/images/laptop.jpg', 'Computers'),
        ('Headphones', 'Noise-cancelling headphones', 199.99, '/static/images/headphones.jpg', 'Audio'),
        ('Smartwatch', 'Feature-rich smartwatch', 299.99, '/static/images/smartwatch.jpg', 'Wearables');
''')



    conn.commit()
    conn.close()


# Routes
@app.route("/")
def home():
    return render_template("home.html")
# @app.route("/")
# @app.route("/home")
# def home():
#     conn = sqlite3.connect("commerce_app.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM products")
#     products = [
#         {"product_id": row[0], "product_name": row[1], "price": row[3], "image_url": "static/product.png"}
#         for row in cursor.fetchall()
#     ]
#     conn.close()
#     return render_template("home.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Connect to the database
        conn = sqlite3.connect("commerce_app.db")
        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("Username already taken. Please choose a different one.", "danger")
        else:
            # Insert new user into the database
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Validate the login credentials
        conn = sqlite3.connect("commerce_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:  # user[2] is the password column
            session["user_id"] = user[0]  # Store user ID in the session
            flash("Login successful!", "success")
            return redirect(url_for("home"))  # Redirect to home page after successful login
        else:
            flash("Invalid username or password. Please try again.", "danger")
    
    return render_template("login.html")



# @app.route("/products")
# def products():
#     conn = sqlite3.connect("commerce_app.db")
#     cursor = conn.cursor()

#     # Fetch all products
#     cursor.execute("""
#         SELECT product_id, product_name, description, price, image_url
#         FROM products
#     """)
#     rows = cursor.fetchall()
#     conn.close()

#     # Prepare products data for rendering
#     products = [{
#         "id": row[0],
#         "name": row[1],
#         "description": row[2],
#         "price": row[3],
#         "image_url": row[4] if row[4] else "/static/images/default-product.jpg"
#     } for row in rows]

#     return render_template("products.html", products=products)

@app.route("/products")
def products():
    search_query = request.args.get("search", "").strip()
    sort_option = request.args.get("sort", "")
    category_filter = request.args.get("category", "")

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Fetch unique categories for the filter dropdown
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]

    # Base SQL query for fetching products
    sql_query = """
        SELECT product_id, product_name, description, price, image_url, category
        FROM products
        WHERE 1=1
    """
    params = []

    # Search functionality
    if search_query:
        sql_query += " AND product_name LIKE ?"
        params.append(f"%{search_query}%")

    # Category filter
    if category_filter:
        sql_query += " AND category = ?"
        params.append(category_filter)

    # Sorting
    if sort_option == "low_to_high":
        sql_query += " ORDER BY price ASC"
    elif sort_option == "high_to_low":
        sql_query += " ORDER BY price DESC"

    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    conn.close()

    # Prepare products data for rendering
    products = [{
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": row[3],
        "image_url": row[4] if row[4] else "/static/images/default-product.jpg",
        "category": row[5]
    } for row in rows]

    return render_template("products.html", products=products, categories=categories)


@app.route("/purchase/<int:product_id>", methods=["POST"])
def purchase(product_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    quantity = int(request.form["quantity"])
    user_id = session["user_id"]

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    cursor.execute("SELECT product_name, price, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    if product:
        product_name, price, stock = product
        if stock >= quantity:
            total_price = quantity * price
            cursor.execute("INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (?, ?, ?, ?)",
                           (user_id, product_id, quantity, total_price))
            cursor.execute("UPDATE products SET stock = stock - ? WHERE product_id = ?", (quantity, product_id))
            conn.commit()
            flash(f"Purchased {quantity} {product_name}(s) for ${total_price:.2f}", "success")
        else:
            flash(f"Only {stock} {product_name}(s) are available.", "danger")
    conn.close()
    return redirect(url_for("products"))


# @app.route("/logout")
# def logout():
#     session.clear()
#     flash("Logged out successfully.", "info")
#     return redirect(url_for("home"))
@app.route("/my_account")
def my_account():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access your account.", "danger")
        return redirect(url_for("home"))
    
    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    user_data = {"username": user[0], "password": user[1]} if user else None
    return render_template("my_account.html", user=user_data)
@app.route("/cart")
def cart():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your cart.", "danger")
        return redirect(url_for("home"))
    
    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.cart_id, p.product_name, c.quantity, p.price, (c.quantity * p.price) AS total
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    """, (user_id,))
    cart_items = [
        {"cart_id": row[0], "product_name": row[1], "quantity": row[2], "price": row[3], "total": row[4]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return render_template("cart.html", cart_items=cart_items)
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to add items to your cart.", "danger")
        return redirect(url_for("login"))
    
    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Check if the product is already in the user's cart
    cursor.execute("""
        SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))
    cart_item = cursor.fetchone()

    if cart_item:
        # Update quantity if item already exists in the cart
        cursor.execute("""
            UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
    else:
        # Add a new item to the cart
        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)
        """, (user_id, product_id))

    conn.commit()
    conn.close()

    flash("Item added to cart successfully!", "success")
    return redirect(url_for("home"))
@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to manage your cart.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Delete the item from the cart
    cursor.execute("""
        DELETE FROM cart WHERE cart_id = ? AND user_id = ?
    """, (cart_id, user_id))

    conn.commit()
    conn.close()

    flash("Item removed from cart successfully!", "info")
    return redirect(url_for("cart"))
@app.route("/update_cart/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to manage your cart.", "danger")
        return redirect(url_for("login"))

    new_quantity = request.form.get("quantity", type=int)

    if new_quantity <= 0:
        flash("Quantity must be at least 1.", "danger")
        return redirect(url_for("cart"))

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Update the quantity in the cart
    cursor.execute("""
        UPDATE cart SET quantity = ? WHERE cart_id = ? AND user_id = ?
    """, (new_quantity, cart_id, user_id))

    conn.commit()
    conn.close()

    flash("Cart updated successfully!", "success")
    return redirect(url_for("cart"))

@app.route("/edit_account", methods=["GET", "POST"])
def edit_account():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to edit your account.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Get updated user details from the form
        new_username = request.form.get("username")
        new_password = request.form.get("password")

        # Update the user information in the database
        cursor.execute("""
            UPDATE users
            SET username = ?, password = ?
            WHERE user_id = ?
        """, (new_username, new_password, user_id))
        conn.commit()

        flash("Account details updated successfully!", "success")
        return redirect(url_for("my_account"))

    # Fetch the current user details to prefill the form
    cursor.execute("SELECT username, password FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    user_data = {"username": user[0], "password": user[1]} if user else None
    return render_template("edit_account.html", user=user_data)


def send_order_confirmation_email(user_id, order_id):
    """Send order confirmation email after successful order placement."""
    
    # Fetch user details (e.g., email)
    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    print(user,446)

    if user:
        username, password = user

        # Create the email content
        subject = "Order Confirmation - E-Commerce"
        body = f"""
        Hello {username},

        Thank you for your order. Your order ID is {order_id}.
        We are processing your order and will notify you once it's shipped.

        Order Details:
        -----------------
        - Order ID: {order_id}
        - Total Amount: ${{total_amount}}
        
        Thank you for shopping with us!

        Regards,
        E-Commerce Team
        """

        # Create the email message
        msg = Message(subject,sender="shirishagunta3@gmail.com", recipients=["hasinichaithanya04@gmail.com"])
        msg.body=body
        # Send the email
        try:
            mail.send(msg)
            print("Confirmation email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
            


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to proceed to checkout.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Retrieve items from the cart
    cursor.execute("""
        SELECT c.product_id, c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    """, (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        flash("Your cart is empty. Add items before checking out.", "info")
        return redirect(url_for("cart"))

    # Calculate the total amount
    total_amount = sum(item[1] * item[2] for item in cart_items)

    # Create a new order
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO orders (user_id, order_date, total_amount)
        VALUES (?, ?, ?)
    """, (user_id, order_date, total_amount))
    order_id = cursor.lastrowid

    # Add items to the order details
    for item in cart_items:
        product_id, quantity, price = item
        cursor.execute("""
            INSERT INTO order_details (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, product_id, quantity, price))

    # Clear the user's cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    # Send confirmation email
    send_order_confirmation_email(user_id, order_id)

    flash("Order placed successfully! Thank you for your purchase.", "success")
    return redirect(url_for("order_history"))



@app.route("/order_history")
def order_history():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your order history.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect("commerce_app.db")
    cursor = conn.cursor()

    # Fetch orders for the user
    cursor.execute("""
        SELECT order_id, order_date, total_amount
        FROM orders
        WHERE user_id = ?
        ORDER BY order_date DESC
    """, (user_id,))
    orders = cursor.fetchall()

    # Fetch order details for each order
    order_data = []
    for order in orders:
        cursor.execute("""
            SELECT p.product_name, d.quantity, d.price
            FROM order_details d
            JOIN products p ON d.product_id = p.product_id
            WHERE d.order_id = ?
        """, (order[0],))
        details = cursor.fetchall()
        order_data.append({
            "order_id": order[0],
            "order_date": order[1],
            "total_amount": order[2],
            "details": [{"product_name": d[0], "quantity": d[1], "price": d[2]} for d in details]
        })

    conn.close()
    return render_template("order_history.html", orders=order_data)
@app.route("/logout")
def logout():
    session.pop("user_id", None)  # Remove the user_id from the session
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

# Run App
if __name__ == "__main__":
   
    app.run(debug=True)
