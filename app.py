from flask import Flask, render_template, request, redirect, url_for, session, Response, make_response, flash, jsonify
from xhtml2pdf import pisa
import mysql.connector
import csv
import random
import string
import sys
from io import StringIO, BytesIO
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'trash-for-coin-secret-key-2025'


# --- Barcode Encoding/Decoding Functions ---

app = Flask(__name__)
app.secret_key = 'your_strong_and_secret_key_here' # *** สำคัญมาก: เปลี่ยนเป็นคีย์ลับที่ปลอดภัยของคุณ ***

# --- Barcode Encoding/Decoding Functions ---
def encode(x: int) -> int:
    a = 982451653
    b = 1234567891234
    m = 10000000000039 # จำนวนเฉพาะที่ใกล้เคียง 10^13
    return (a * x + b) % m

def decode(y: int) -> int:
    a = 982451653
    b = 1234567891234
    m = 10000000000039 # ต้องเป็นค่าเดียวกับ m ใน encode
    a_inv = pow(a, m - 2, m) # หา inverse ของ a mod m โดยใช้ Fermat's Little Theorem
    return (a_inv * (y - b)) % m


# Placeholder for role_required decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('loggedin'):
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator



# --- Database Connection ---
def get_db_connection():
    """
    Establishes a connection to the MySQL database.
    Returns the connection object or None if connection fails.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="project_bin"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

# --- Role-based Access Control (RBAC) Decorators ---
def role_required(allowed_roles):
    """
    Decorator to restrict access to routes based on user roles.
    If the user is not logged in, they are redirected to the login page.
    If the user's role is not in the allowed_roles list, they are redirected to the index page.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' not in session:
                flash('โปรดเข้าสู่ระบบเพื่อเข้าถึงหน้านี้', 'danger')
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash(f'คุณไม่มีสิทธิ์เข้าถึงหน้านี้ ยศของคุณคือ {session.get("role")}', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes ---

@app.route("/")
def root_redirect():
    """Redirects the root URL to the index page."""
    return redirect(url_for("index"))

@app.route("/index", methods=["GET", "POST"])
def index():
    """
    Home page of the Trash For Coin system, displaying usage statistics.
    Statistics are only fetched and displayed if a user is logged in.
    """
    stats = {
        'total_products': 0,
        'total_orders': 0,
        'total_categories': 0,
        'total_users': 0
    }
    
    if session.get('loggedin'):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Fetch total products
                cursor.execute("SELECT COUNT(*) FROM tbl_products")
                stats['total_products'] = cursor.fetchone()[0]
                
                # Fetch total orders
                cursor.execute("SELECT COUNT(*) FROM tbl_order")
                stats['total_orders'] = cursor.fetchone()[0]
                

                    

                # Fetch total categories
                cursor.execute("SELECT COUNT(*) FROM tbl_category")
                stats['total_categories'] = cursor.fetchone()[0]

                # Fetch total users (only for admin/moderator roles)
                if session.get('role') in ['root_admin', 'administrator', 'moderator']:
                    cursor.execute("SELECT COUNT(*) FROM tbl_users")
                    stats['total_users'] = cursor.fetchone()[0]
                
            except mysql.connector.Error as err:
                print(f"Error fetching stats: {err}")
            finally:
                cursor.close()
                conn.close()
    
    return render_template("index.html", stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    Authenticates user credentials against tbl_users table.
    Sets session variables upon successful login.
    """
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM tbl_users WHERE email = %s AND password = %s', (email, password,))
            account = cursor.fetchone()
            
            if account:
                session['loggedin'] = True
                session['id'] = account['id']
                session['email'] = account['email']
                session['firstname'] = account['firstname']
                session['lastname'] = account['lastname']
                session['role'] = account['role']
                msg = 'เข้าสู่ระบบสำเร็จ!'
                flash(msg, 'success')
                return redirect(url_for('index'))
            else:
                msg = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง!'
                flash(msg, 'danger')
            cursor.close()
            conn.close()
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles new user registration.
    Inserts new user data into tbl_users table with 'member' role by default.
    Checks for existing email addresses.
    """
    msg = ''
    if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and 'email' in request.form and 'password' in request.form:
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM tbl_users WHERE email = %s', (email,))
            account = cursor.fetchone()
            
            if account:
                msg = 'บัญชีนี้มีอยู่แล้ว!'
                flash(msg, 'danger')
            elif not firstname or not lastname or not email or not password:
                msg = 'กรุณากรอกข้อมูลให้ครบถ้วน!'
                flash(msg, 'danger')
            else:
                cursor.execute('INSERT INTO tbl_users (firstname, lastname, email, password, role) VALUES (%s, %s, %s, %s, %s)', (firstname, lastname, email, password, 'member',))
                conn.commit()
                msg = 'คุณสมัครสมาชิกสำเร็จแล้ว!'
                flash(msg, 'success')
                return redirect(url_for('login'))
            cursor.close()
            conn.close()
    elif request.method == 'POST':
        msg = 'กรุณากรอกข้อมูลให้ครบถ้วน!'
        flash(msg, 'danger')
    return render_template('register.html', msg=msg)

@app.route('/profile', methods=['GET', 'POST'])
@role_required(['root_admin', 'administrator', 'moderator', 'member', 'viewer'])
def profile():
    """
    Allows logged-in users to manage their profile information.
    Users can update their first name, last name, email, and optionally password.
    Prevents changing email to an already existing one (excluding their own).
    """
    msg = ''
    if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and 'email' in request.form:
        if 'loggedin' in session:
            new_firstname = request.form['firstname']
            new_lastname = request.form['lastname']
            new_email = request.form['email']
            new_password = request.form['password'] if 'password' in request.form and request.form['password'] else None

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Check if the new email already exists for another user
                cursor.execute('SELECT id FROM tbl_users WHERE email = %s AND id != %s', (new_email, session['id'],))
                existing_email = cursor.fetchone()
                if existing_email:
                    msg = 'อีเมลนี้มีผู้ใช้งานอื่นแล้ว!'
                    flash(msg, 'danger')
                    cursor.close()
                    conn.close()
                    return render_template('profile.html', msg=msg, session=session)

                # Update user information
                if new_password:
                    cursor.execute('UPDATE tbl_users SET firstname = %s, lastname = %s, email = %s, password = %s WHERE id = %s', (new_firstname, new_lastname, new_email, new_password, session['id'],))
                else:
                    cursor.execute('UPDATE tbl_users SET firstname = %s, lastname = %s, email = %s WHERE id = %s', (new_firstname, new_lastname, new_email, session['id'],))
                
                conn.commit()
                
                # Update session variables
                session['firstname'] = new_firstname
                session['lastname'] = new_lastname
                session['email'] = new_email
                msg = 'ข้อมูลโปรไฟล์ของคุณได้รับการอัปเดตสำเร็จ!'
                flash(msg, 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('profile'))
        else:
            msg = 'โปรดเข้าสู่ระบบเพื่ออัปเดตโปรไฟล์ของคุณ'
            flash(msg, 'danger')
    return render_template('profile.html', msg=msg, session=session)

@app.route('/logout')
def logout():
    """Logs out the current user by clearing session variables."""
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.pop('firstname', None)
    session.pop('lastname', None)
    session.pop('role', None)
    flash('คุณได้ออกจากระบบแล้ว', 'info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    """Displays the 'About Us' page."""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Handles the 'Contact Us' form submission.
    Currently, it just prints the form data and flashes a success message.
    """
    msg = ''
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        print(f"Contact Form: Name: {name}, Email: {email}, Subject: {subject}, Message: {message}")
        msg = 'ข้อความของคุณถูกส่งสำเร็จแล้ว!'
        flash(msg, 'success')
    return render_template('contact.html', msg=msg)

# --- Category Management ---
@app.route("/tbl_category", methods=["GET", "POST"])
@role_required(['root_admin', 'administrator', 'moderator'])
def tbl_category():
    """
    Manages product categories (e.g., PET, Aluminum, Glass, Burnable, Contaminated Waste).
    Supports adding, editing, deleting, and searching categories.
    """
    msg = ''
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return render_template("tbl_category.html", categories=[], search='')

    cursor = conn.cursor(dictionary=True)
    
    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add':
            category_id = request.form['category_id']
            category_name = request.form['category_name']
            try:
                cursor.execute("INSERT INTO tbl_category (category_id, category_name) VALUES (%s, %s)", (category_id, category_name))
                conn.commit()
                msg = 'เพิ่มหมวดหมู่สำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการเพิ่มหมวดหมู่: {err}"
                flash(msg, 'danger')

        elif action == 'edit':
            cat_id = request.form['cat_id']
            category_id = request.form['category_id']
            category_name = request.form['category_name']
            try:
                cursor.execute("UPDATE tbl_category SET category_id = %s, category_name = %s WHERE id = %s", (category_id, category_name, cat_id))
                conn.commit()
                msg = 'อัปเดตหมวดหมู่สำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการอัปเดตหมวดหมู่: {err}"
                flash(msg, 'danger')

        elif action == 'delete':
            cat_id = request.form['cat_id']
            try:
                cursor.execute("DELETE FROM tbl_category WHERE id = %s", (cat_id,))
                conn.commit()
                msg = 'ลบหมวดหมู่สำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการลบหมวดหมู่: {err}"
                flash(msg, 'danger')
        
        elif 'search' in request.form:
            search_query = request.form['search']
            cursor.execute("SELECT * FROM tbl_category WHERE category_name LIKE %s OR category_id LIKE %s ORDER BY id DESC", ('%' + search_query + '%', '%' + search_query + '%'))
            categories = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template("tbl_category.html", categories=categories, search=search_query, msg=msg)

    # Fetch all categories for initial display
    cursor.execute("SELECT * FROM tbl_category ORDER BY id DESC")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("tbl_category.html", categories=categories, search='', msg=msg)

@app.route("/tbl_products", methods=["GET", "POST"])
@role_required(['root_admin', 'administrator', 'moderator'])
def tbl_products():
    """
    Manages products.
    Supports adding, editing, deleting, and searching products.
    """
    msg = ''
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return render_template("tbl_products.html", products=[], categories=[], search='')

    cursor = conn.cursor(dictionary=True)
    
    # Fetch all categories for the product dropdown
    cursor.execute("SELECT category_id, category_name FROM tbl_category ORDER BY category_name")
    categories = cursor.fetchall()

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add':
            products_id = request.form['products_id']
            product_name = request.form['product_name']
            stock = request.form['stock']
            price = request.form['price']
            category_id = request.form['category_id']
            description = request.form['description']
            # ลบ barcode_id ออก
            try:
                cursor.execute("INSERT INTO tbl_products (products_id, products_name, stock, price, category_id, description) VALUES (%s, %s, %s, %s, %s, %s)", 
                               (products_id, product_name, stock, price, category_id, description))
                conn.commit()
                msg = 'เพิ่มสินค้าสำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการเพิ่มสินค้า: {err}"
                flash(msg, 'danger')

        elif action == 'edit':
            product_id = request.form['product_id']
            products_id = request.form['products_id']
            product_name = request.form['product_name']
            stock = request.form['stock']
            price = request.form['price']
            category_id = request.form['category_id']
            description = request.form['description']
            # ลบ barcode_id ออก
            try:
                cursor.execute("UPDATE tbl_products SET products_id = %s, products_name = %s, stock = %s, price = %s, category_id = %s, description = %s WHERE id = %s", 
                               (products_id, product_name, stock, price, category_id, description, product_id))
                conn.commit()
                msg = 'อัปเดตสินค้าสำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการอัปเดตสินค้า: {err}"
                flash(msg, 'danger')

        elif action == 'delete':
            product_id = request.form['product_id']
            try:
                cursor.execute("DELETE FROM tbl_products WHERE id = %s", (product_id,))
                conn.commit()
                msg = 'ลบสินค้าสำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการลบสินค้า: {err}"
                flash(msg, 'danger')

        elif 'search' in request.form:
            search_query = request.form['search']
            cursor.execute("""
                SELECT p.*, c.category_name 
                FROM tbl_products p
                LEFT JOIN tbl_category c ON p.category_id = c.category_id
                WHERE p.products_name LIKE %s OR p.products_id LIKE %s OR c.category_name LIKE %s 
                ORDER BY p.id DESC
            """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%')) # ลบ p.barcode_id LIKE %s ออก
            products = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template("tbl_products.html", products=products, categories=categories, search=search_query, msg=msg)

    # Fetch all products for initial display
    cursor.execute("""
        SELECT p.*, c.category_name 
        FROM tbl_products p
        LEFT JOIN tbl_category c ON p.category_id = c.category_id
        ORDER BY p.id DESC
    """)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("tbl_products.html", products=products, categories=categories, search='', msg=msg)
   
   
# --- Order Management ---
@app.route("/tbl_order", methods=["GET", "POST"])
@role_required(['root_admin', 'administrator', 'moderator', 'member', 'viewer'])
def tbl_order():
    """
    Manages customer orders, including quantity tracking and disposed quantity.
    Supports adding, editing, deleting, and searching orders.
    Stock is updated based on ordered quantity.
    """
    msg = ''
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return render_template("tbl_order.html", orders=[], products=[], users=[], search='')

    cursor = conn.cursor(dictionary=True)

    # Fetch all products for the product dropdowns in modals
    cursor.execute("SELECT products_id, products_name, stock, price, barcode_id FROM tbl_products ORDER BY products_name")
    products_data = cursor.fetchall()

    users_data = []
    # Fetch all users for the email dropdown in modals (if admin/moderator)
    if session.get('role') in ['root_admin', 'administrator', 'moderator']:
        cursor.execute("SELECT email, CONCAT(firstname, ' ', lastname) as fullname FROM tbl_users ORDER BY firstname")
        users_data = cursor.fetchall()

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add':
            # Check permissions for adding orders
            if session.get('role') in ['root_admin', 'administrator', 'moderator', 'member']:
                order_id = request.form['order_id']
                products_id = request.form['products_id']
                quantity = int(request.form['quantity'])
                # Receive disquantity and barcode_id directly from the form
                disquantity = int(request.form['disquantity'])
                # Strip whitespace from barcode_id; convert empty string to None if desired
                barcode_id = request.form['barcode_id'].strip() if request.form['barcode_id'] else None 
                
                # Determine order email based on user role
                email = request.form['email'] if session.get('role') in ['root_admin', 'administrator', 'moderator'] else session['email']

                try:
                    # Validate product existence and stock availability
                    cursor.execute("SELECT products_name, stock, price FROM tbl_products WHERE products_id = %s", (products_id,))
                    product_info = cursor.fetchone()

                    if not product_info:
                        msg = "ไม่พบสินค้า!"
                        flash(msg, 'danger')
                    elif quantity > product_info['stock']:
                        msg = f"สินค้า {product_info['products_name']} มีสต็อกไม่พอ. มีในสต็อก: {product_info['stock']}"
                        flash(msg, 'danger')
                    else:
                        products_name = product_info['products_name']
                        
                        # Insert new order with user-provided disquantity and barcode_id
                        cursor.execute("""
                            INSERT INTO tbl_order (order_id, products_id, products_name, quantity, disquantity, email, barcode_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (order_id, products_id, products_name, quantity, disquantity, email, barcode_id))

                        # Update product stock (deduct ordered quantity)
                        cursor.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (quantity, products_id))

                        conn.commit()
                        msg = 'เพิ่มคำสั่งซื้อสำเร็จและอัปเดตสต็อกสินค้าแล้ว!'
                        flash(msg, 'success')
                except mysql.connector.Error as err:
                    msg = f"เกิดข้อผิดพลาดในการเพิ่มคำสั่งซื้อ: {err}"
                    flash(msg, 'danger')
            else:
                msg = "คุณไม่มีสิทธิ์เพิ่มคำสั่งซื้อ"
                flash(msg, 'danger')

        elif action == 'edit':
            ord_id = request.form['ord_id']
            order_id = request.form['order_id']
            products_id = request.form['products_id']
            quantity = int(request.form['quantity'])
            # Receive disquantity and barcode_id directly from the form
            disquantity = int(request.form['disquantity']) 
            barcode_id = request.form['barcode_id'].strip() if request.form['barcode_id'] else None 
            email = request.form['email'] # Email from form, which might be read-only for members

            # --- DEBUG PRINT (for troubleshooting) ---
            print(f"DEBUG: Edit Order - ord_id: {ord_id}, order_id: {order_id}, products_id: {products_id}, quantity: {quantity}, disquantity: {disquantity}, barcode_id: {barcode_id}, email: {email}")
            # --- END DEBUG PRINT ---

            # Check permissions for editing
            if session.get('role') in ['root_admin', 'administrator', 'moderator'] or \
               (session.get('role') == 'member' and session.get('email') == email):
                try:
                    # Get current order information to calculate stock change
                    cursor.execute("SELECT products_id, quantity FROM tbl_order WHERE id = %s", (ord_id,))
                    old_order_info = cursor.fetchone()

                    if not old_order_info:
                        msg = "ไม่พบคำสั่งซื้อที่ต้องการแก้ไข!"
                        flash(msg, 'danger')
                    else:
                        old_products_id = old_order_info['products_id']
                        old_quantity = old_order_info['quantity']

                        # Get new product information and its current stock
                        cursor.execute("SELECT products_name, stock FROM tbl_products WHERE products_id = %s", (products_id,))
                        new_product_info = cursor.fetchone()

                        if not new_product_info:
                            msg = "ไม่พบสินค้าใหม่ที่เลือก!"
                            flash(msg, 'danger')
                        else:
                            products_name = new_product_info['products_name']
                            current_stock_of_new_product = new_product_info['stock']

                            # --- Stock Adjustment Logic ---
                            if products_id != old_products_id:
                                # If product ID changes, restore old product's stock
                                cursor.execute("UPDATE tbl_products SET stock = stock + %s WHERE products_id = %s", (old_quantity, old_products_id))
                                
                                # Then deduct from the new product's stock
                                if quantity > current_stock_of_new_product: # Check if new quantity exceeds available stock
                                    msg = f"สินค้า {products_name} มีสต็อกไม่พอสำหรับการสั่งซื้อใหม่. มีในสต็อก: {current_stock_of_new_product}"
                                    flash(msg, 'danger')
                                    conn.rollback() # Rollback if stock is insufficient
                                    return redirect(url_for('tbl_order'))
                                cursor.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (quantity, products_id))
                            else:
                                # If product ID is the same, adjust stock based on the difference in quantity
                                quantity_difference = quantity - old_quantity
                                if current_stock_of_new_product - quantity_difference < 0: # Check if stock becomes negative
                                    msg = f"สินค้า {products_name} มีสต็อกไม่พอสำหรับการเปลี่ยนแปลงจำนวน. มีในสต็อก: {current_stock_of_new_product}"
                                    flash(msg, 'danger')
                                    conn.rollback() # Rollback if stock is insufficient
                                    return redirect(url_for('tbl_order'))
                                cursor.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (quantity_difference, products_id))
                            
                            # Update the order in tbl_order with new values, including disquantity and barcode_id
                            cursor.execute("""
                                UPDATE tbl_order SET order_id = %s, products_id = %s, products_name = %s, quantity = %s, disquantity = %s, email = %s, barcode_id = %s
                                WHERE id = %s
                            """, (order_id, products_id, products_name, quantity, disquantity, email, barcode_id, ord_id))

                            conn.commit()
                            msg = 'อัปเดตคำสั่งซื้อสำเร็จและอัปเดตสต็อกสินค้าแล้ว!'
                            flash(msg, 'success')
                except mysql.connector.Error as err:
                    msg = f"เกิดข้อผิดพลาดในการอัปเดตคำสั่งซื้อ: {err}"
                    flash(msg, 'danger')
                    conn.rollback() # Rollback in case of error
            else:
                msg = "คุณไม่มีสิทธิ์แก้ไขคำสั่งซื้อนี้"
                flash(msg, 'danger')

        elif action == 'delete':
            ord_id = request.form['ord_id']
            order_email = request.form['email'] # Email from the form for permission check

            # Check permissions for deleting
            if session.get('role') in ['root_admin', 'administrator', 'moderator'] or \
               (session.get('role') == 'member' and session.get('email') == order_email):
                try:
                    # Get order information before deleting to restore stock
                    cursor.execute("SELECT products_id, quantity FROM tbl_order WHERE id = %s", (ord_id,))
                    order_to_delete = cursor.fetchone()

                    if not order_to_delete:
                        msg = "ไม่พบคำสั่งซื้อที่ต้องการลบ!"
                        flash(msg, 'danger')
                    else:
                        product_id_to_restore = order_to_delete['products_id']
                        quantity_to_restore = order_to_delete['quantity']

                        # Delete the order from tbl_order
                        cursor.execute("DELETE FROM tbl_order WHERE id = %s", (ord_id,))

                        # Restore product stock in tbl_products (based on original ordered quantity)
                        cursor.execute("UPDATE tbl_products SET stock = stock + %s WHERE products_id = %s", (quantity_to_restore, product_id_to_restore))

                        conn.commit()
                        msg = 'ลบคำสั่งซื้อสำเร็จและคืนสต็อกสินค้าแล้ว!'
                        flash(msg, 'success')
                except mysql.connector.Error as err:
                    msg = f"เกิดข้อผิดพลาดในการลบคำสั่งซื้อ: {err}"
                    flash(msg, 'danger')
                    conn.rollback() # Rollback in case of error
            else:
                msg = "คุณไม่มีสิทธิ์ลบคำสั่งซื้อนี้"
                flash(msg, 'danger')

        elif 'search' in request.form:
            search_query = request.form['search']
            query_params = ['%' + search_query + '%'] * 3

            # SQL query for searching orders, explicitly selecting barcode_id from tbl_order
            base_query = """
                SELECT 
                    o.id, 
                    o.order_id, 
                    o.products_id, 
                    o.products_name, 
                    o.quantity, 
                    o.disquantity, 
                    o.email, 
                    o.order_date,
                    o.barcode_id, -- Explicitly select barcode_id from tbl_order
                    p.category_id 
                FROM tbl_order o
                LEFT JOIN tbl_products p ON o.products_id = p.products_id
                WHERE o.order_id LIKE %s OR o.products_name LIKE %s OR o.email LIKE %s
            """
            if session.get('role') == 'member':
                base_query += " AND o.email = %s"
                query_params.append(session['email'])

            base_query += " ORDER BY o.id DESC"

            cursor.execute(base_query, tuple(query_params))
            orders = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template("tbl_order.html", orders=orders, products=products_data, users=users_data, search=search_query, msg=msg)

    # SQL query for initial display of orders, explicitly selecting barcode_id from tbl_order
    base_query = """
        SELECT 
            o.id, 
            o.order_id, 
            o.products_id, 
            o.products_name, 
            o.quantity, 
            o.disquantity, 
            o.email, 
            o.order_date,
            o.barcode_id, -- Explicitly select barcode_id from tbl_order
            p.category_id 
        FROM tbl_order o
        LEFT JOIN tbl_products p ON o.products_id = p.products_id
    """
    if session.get('role') == 'member':
        base_query += f" WHERE o.email = '{session['email']}'"

    base_query += " ORDER BY o.id DESC"

    cursor.execute(base_query)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("tbl_order.html", orders=orders, products=products_data, users=users_data, search='', msg=msg)

# --- User Management ---
@app.route("/tbl_users", methods=["GET", "POST"])
@role_required(['root_admin', 'administrator'])
def tbl_users():
    """
    Manages user accounts and their roles (root_admin, administrator, moderator, member, viewer).
    Supports adding, searching, editing, and deleting users.
    Root admin cannot be deleted. Administrators cannot create/edit root_admin users.
    """
    msg = ''
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return render_template("tbl_users.html", users=[], search='')

    cursor = conn.cursor(dictionary=True)

    root_admin_id = None
    try:
        cursor.execute("SELECT id FROM tbl_users WHERE role = 'root_admin' LIMIT 1")
        result = cursor.fetchone()
        if result:
            root_admin_id = result['id']
    except mysql.connector.Error as err:
        print(f"Error fetching root_admin_id: {err}")

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add':
            # Permission check for adding users
            if session.get('role') == 'root_admin' or \
               (session.get('role') == 'administrator' and request.form.get('role') != 'root_admin'):
                
                firstname = request.form['firstname']
                lastname = request.form['lastname']
                email = request.form['email']
                password = request.form['password']
                role = request.form['role']
                
                try:
                    cursor.execute('INSERT INTO tbl_users (firstname, lastname, email, password, role) VALUES (%s, %s, %s, %s, %s)', (firstname, lastname, email, password, role))
                    conn.commit()
                    msg = 'เพิ่มผู้ใช้งานสำเร็จ!'
                    flash(msg, 'success')
                except mysql.connector.Error as err:
                    msg = f"เกิดข้อผิดพลาดในการเพิ่มผู้ใช้งาน: {err}"
                    flash(msg, 'danger')
            else:
                msg = "คุณไม่มีสิทธิ์เพิ่มผู้ใช้งานด้วยยศนี้"
                flash(msg, 'danger')

        elif action == 'edit':
            user_id = request.form['user_id']
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            email = request.form['email']
            password = request.form['password'] if 'password' in request.form and request.form['password'] else None
            role = request.form['role']

            # Prevent editing root_admin role by non-root_admin or changing root_admin's role
            cursor.execute("SELECT role FROM tbl_users WHERE id = %s", (user_id,))
            target_user_role = cursor.fetchone()['role']

            if session.get('role') == 'root_admin':
                # Root admin can edit anyone, even other root admins, but cannot change their own role to non-root admin
                if target_user_role == 'root_admin' and role != 'root_admin' and str(user_id) == str(session['id']):
                    msg = "คุณไม่สามารถเปลี่ยนยศของ Root Admin ที่เข้าสู่ระบบอยู่ได้"
                    flash(msg, 'danger')
                    conn.rollback()
                    return redirect(url_for('tbl_users'))
                pass # Root admin has full permission
            elif session.get('role') == 'administrator':
                if target_user_role == 'root_admin' or role == 'root_admin':
                    msg = "คุณไม่มีสิทธิ์แก้ไขผู้ใช้งาน Root Admin หรือกำหนดให้เป็น Root Admin"
                    flash(msg, 'danger')
                    conn.rollback()
                    return redirect(url_for('tbl_users'))
            else: # Moderator, Member, Viewer cannot edit users via this route (already handled by role_required)
                msg = "คุณไม่มีสิทธิ์แก้ไขผู้ใช้งาน"
                flash(msg, 'danger')
                conn.rollback()
                return redirect(url_for('tbl_users'))

            try:
                # Check for duplicate email (excluding current user)
                cursor.execute('SELECT id FROM tbl_users WHERE email = %s AND id != %s', (email, user_id,))
                existing_email = cursor.fetchone()
                if existing_email:
                    msg = 'อีเมลนี้มีผู้ใช้งานอื่นแล้ว!'
                    flash(msg, 'danger')
                    conn.rollback()
                    return redirect(url_for('tbl_users'))

                if password:
                    cursor.execute('UPDATE tbl_users SET firstname = %s, lastname = %s, email = %s, password = %s, role = %s WHERE id = %s', 
                                   (firstname, lastname, email, password, role, user_id))
                else:
                    cursor.execute('UPDATE tbl_users SET firstname = %s, lastname = %s, email = %s, role = %s WHERE id = %s', 
                                   (firstname, lastname, email, role, user_id))
                conn.commit()
                msg = 'อัปเดตผู้ใช้งานสำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการอัปเดตผู้ใช้งาน: {err}"
                flash(msg, 'danger')
                conn.rollback()

        elif action == 'delete':
            user_id = request.form['user_id']
            
            # Prevent deleting the currently logged-in user
            if str(user_id) == str(session['id']):
                msg = "คุณไม่สามารถลบบัญชีผู้ใช้ของคุณเองได้!"
                flash(msg, 'danger')
                return redirect(url_for('tbl_users'))

            # Prevent deleting the root_admin by anyone other than root_admin (or even by root_admin if only one exists)
            cursor.execute("SELECT role FROM tbl_users WHERE id = %s", (user_id,))
            target_user_role = cursor.fetchone()['role']
            
            if target_user_role == 'root_admin':
                cursor.execute("SELECT COUNT(*) FROM tbl_users WHERE role = 'root_admin'")
                root_admin_count = cursor.fetchone()[0]
                if root_admin_count <= 1: # Prevent deleting the last root_admin
                    msg = "ไม่สามารถลบ Root Admin คนสุดท้ายได้!"
                    flash(msg, 'danger')
                    return redirect(url_for('tbl_users'))
                if session.get('role') != 'root_admin':
                    msg = "คุณไม่มีสิทธิ์ลบผู้ใช้งาน Root Admin"
                    flash(msg, 'danger')
                    return redirect(url_for('tbl_users'))
            
            if session.get('role') == 'administrator' and target_user_role == 'administrator':
                msg = "Administrator ไม่สามารถลบ Administrator ด้วยกันได้"
                flash(msg, 'danger')
                return redirect(url_for('tbl_users'))

            try:
                cursor.execute("DELETE FROM tbl_users WHERE id = %s", (user_id,))
                conn.commit()
                msg = 'ลบผู้ใช้งานสำเร็จ!'
                flash(msg, 'success')
            except mysql.connector.Error as err:
                msg = f"เกิดข้อผิดพลาดในการลบผู้ใช้งาน: {err}"
                flash(msg, 'danger')

        elif 'search' in request.form:
            search_query = request.form['search']
            cursor.execute("SELECT * FROM tbl_users WHERE firstname LIKE %s OR lastname LIKE %s OR email LIKE %s OR role LIKE %s ORDER BY id DESC", 
                           ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template("tbl_users.html", users=users, search=search_query, msg=msg)

    # Fetch all users for initial display
    cursor.execute("SELECT * FROM tbl_users ORDER BY id DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("tbl_users.html", users=users, search='', msg=msg)

# --- Report Generation ---
@app.route("/export_products_csv")
@role_required(['root_admin', 'administrator', 'moderator'])
def export_products_csv():
    """Exports product data to a CSV file."""
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return redirect(url_for('tbl_products'))
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT products_id, products_name, stock, price, category_id, description, barcode_id FROM tbl_products")
        products = cursor.fetchall()
        
        si = StringIO()
        cw = csv.writer(si)
        
        cw.writerow(['Product ID', 'Product Name', 'Stock', 'Price', 'Category ID', 'Description', 'Barcode ID'])
        
        for product in products:
            cw.writerow([product['products_id'], product['products_name'], product['stock'], product['price'], product['category_id'], product['description'], product['barcode_id']])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=products_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except mysql.connector.Error as err:
        flash(f"เกิดข้อผิดพลาดในการส่งออกข้อมูลสินค้า: {err}", 'danger')
        return redirect(url_for('tbl_products'))
    finally:
        cursor.close()
        conn.close()
      





# --- Route จัดการคำสั่งซื้อ (cart) ---
@app.route("/cart", methods=["GET", "POST"])
@role_required(['root_admin', 'administrator', 'moderator', 'member', 'viewer'])
def cart():
    msg = ''
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return render_template("cart.html", orders=[], products_data_string='', users=[], search='', current_auto_order_id='',
                               selected_product_details_display='เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล',
                               selected_product_barcode='')

    cursor = conn.cursor(dictionary=True)

    # --- Logic สำหรับสร้าง/จัดการ current_order_id และ barcode_id สำหรับ order นั้นๆ ---
    current_order_id = session.get('current_order_id')
    current_order_barcode = session.get('current_order_barcode') # เก็บ barcode ของ order ปัจจุบัน

    if not current_order_id:
        try:
            # ดึง max order_id
            cursor.execute("SELECT MAX(CAST(order_id AS UNSIGNED)) AS max_order_id FROM tbl_order WHERE order_id REGEXP '^[0-9]+$'")
            result = cursor.fetchone()
            if result and result['max_order_id'] is not None:
                current_order_id = str(int(result['max_order_id']) + 1)
            else:
                current_order_id = '100001' # ID เริ่มต้นหากยังไม่มีข้อมูล
            session['current_order_id'] = current_order_id # Store in session

            # *** สุ่ม barcode_id ใหม่ สำหรับ order_id นี้เท่านั้น ***
            new_barcode = ''
            is_unique = False
            attempts = 0
            max_attempts = 5000 

            # ดึงบาร์โค้ดทั้งหมดที่มีอยู่ใน tbl_order เพื่อใช้ตรวจสอบการซ้ำซ้อน
            cursor.execute("SELECT barcode_id FROM tbl_order WHERE barcode_id IS NOT NULL AND barcode_id != ''")
            existing_barcode_ids_in_db = {item['barcode_id'] for item in cursor.fetchall()}

            while not is_unique and attempts < max_attempts:
                seed = random.randint(10**11, 10**12 - 1)
                encoded_barcode_int = encode(seed)
                new_barcode = str(encoded_barcode_int).zfill(13) 

                if new_barcode not in existing_barcode_ids_in_db:
                    is_unique = True
                attempts += 1
            
            if not is_unique:
                flash("ไม่สามารถสร้างบาร์โค้ดที่ไม่ซ้ำกันสำหรับคำสั่งซื้อใหม่ได้. โปรดลองอีกครั้ง.", 'warning')
                conn.close()
                return redirect(url_for('cart')) 
            
            current_order_barcode = new_barcode
            session['current_order_barcode'] = current_order_barcode # เก็บ barcode ของ order ปัจจุบันใน session

        except mysql.connector.Error as err:
            flash(f"เกิดข้อผิดพลาดในการดึงรหัสคำสั่งซื้อ/สร้างบาร์โค้ดล่าสุด: {err}", 'warning')
            current_order_id = 'ERROR_ID'
            current_order_barcode = ''
            session['current_order_id'] = current_order_id
            session['current_order_barcode'] = current_order_barcode

    # ดึงข้อมูลสินค้าทั้งหมดจากฐานข้อมูลเพื่อส่งไปยัง frontend
    cursor.execute("SELECT products_id, products_name, stock, price, barcode_id FROM tbl_products ORDER BY products_id")
    products_data = cursor.fetchall()
    
    # --- เตรียม products_data สำหรับ HTML ในรูปแบบ String ---
    products_data_parts = []
    for p in products_data:
        safe_products_name = str(p['products_name']).replace('|', ' ').replace('///', ' ')
        safe_barcode_id = str(p['barcode_id'] or '').replace('|', ' ').replace('///', ' ') 
        
        products_data_parts.append(
            f"{p['products_id']}|{safe_products_name}|{p['stock']}|{safe_barcode_id}"
        )
    products_data_string = "///".join(products_data_parts)
    
    users_data = []
    if session.get('role') in ['root_admin', 'administrator', 'moderator']:
        cursor.execute("SELECT email, CONCAT(firstname, ' ', lastname) as fullname FROM tbl_users ORDER BY firstname")
        users_data = cursor.fetchall()

    # --- Initialize display variables for the HTML template ---
    selected_product_details_display = 'จะแสดงที่นี่หลังจากระบุรหัสสินค้า'
    selected_product_barcode = current_order_barcode or '' 

    pre_filled_products_id_input = request.form.get('products_id_input') if request.method == 'POST' else ''

    if pre_filled_products_id_input:
        found_product = next((p for p in products_data if str(p['products_id']) == pre_filled_products_id_input), None)
        if found_product:
            selected_product_details_display = f"{found_product['products_name']} | สต็อก: {found_product['stock']}"
        else:
            selected_product_details_display = 'ไม่พบสินค้าที่ระบุ'

    # --- Handle 'complete_order' action ---
    if request.method == "POST" and request.form.get('action') == 'complete_order':
        try:
            session.pop('current_order_id', None) 
            session.pop('current_order_barcode', None) 
            flash('คำสั่งซื้อเสร็จสมบูรณ์แล้ว! พร้อมสำหรับคำสั่งซื้อใหม่.', 'success')
            
        except Exception as err: 
            flash(f"เกิดข้อผิดพลาดในการดำเนินการเสร็จสิ้นคำสั่งซื้อ: {err}", 'danger')
        finally:
            if conn:
                conn.close()
        return redirect(url_for('cart'))

    # --- Main logic for adding item automatically when product_id_input length is 13 ---
    if request.method == "POST" and 'products_id_input' in request.form:
        products_id_input = request.form.get('products_id_input')
        # ตรวจสอบว่า action ไม่ใช่ 'complete_order' และ products_id_input มีความยาว 13
        if request.form.get('action') != 'complete_order' and products_id_input and len(products_id_input) == 13:
            # จำลองการเพิ่มรายการ
            order_id_to_use = session.get('current_order_id')
            barcode_to_use_for_add = session.get('current_order_barcode') 

            if not order_id_to_use or not barcode_to_use_for_add:
                flash("ไม่สามารถดำเนินการได้: รหัสคำสั่งซื้อหรือบาร์โค้ดคำสั่งซื้อปัจจุบันไม่พร้อมใช้งาน.", 'danger')
                conn.close()
                return render_template("cart.html", orders=[], products_data_string=products_data_string, users=users_data, msg=msg,
                                       current_auto_order_id=order_id_to_use,
                                       request_form_data=request.form,
                                       selected_product_details_display=selected_product_details_display,
                                       selected_product_barcode=selected_product_barcode,
                                       pre_filled_products_id_input=pre_filled_products_id_input)

            email = request.form.get('email')
            if session.get('role') == 'member':
                email = session['email']
            elif not email:
                msg = "กรุณาระบุอีเมลลูกค้า."
                flash(msg, 'danger')
                conn.close()
                return render_template("cart.html", orders=[], products_data_string=products_data_string, users=users_data, msg=msg,
                                       current_auto_order_id=order_id_to_use,
                                       request_form_data=request.form,
                                       selected_product_details_display=selected_product_details_display,
                                       selected_product_barcode=selected_product_barcode,
                                       pre_filled_products_id_input=pre_filled_products_id_input)

            if session.get('role') in ['root_admin', 'administrator', 'moderator', 'member']:
                quantity = 1 
                disquantity = 0 
                
                product_info = None
                try:
                    cursor.execute("SELECT products_name, stock, price, barcode_id FROM tbl_products WHERE products_id = %s", (products_id_input,))
                    product_info = cursor.fetchone()
                except mysql.connector.Error as err:
                    flash(f"เกิดข้อผิดพลาดในการตรวจสอบสินค้า: {err}", 'danger')
                    conn.close()
                    return render_template("cart.html", orders=[], products_data_string=products_data_string, users=users_data, msg=msg,
                                           current_auto_order_id=order_id_to_use,
                                           request_form_data=request.form,
                                           selected_product_details_display='เกิดข้อผิดพลาดในการดึงข้อมูลสินค้า',
                                           selected_product_barcode=selected_product_barcode,
                                           pre_filled_products_id_input=pre_filled_products_id_input)

                if not product_info:
                    msg = "ไม่พบสินค้าตามรหัสสินค้าที่ระบุ!"
                    flash(msg, 'danger')
                    conn.close()
                    return render_template("cart.html", orders=[], products_data_string=products_data_string, users=users_data, msg=msg,
                                           current_auto_order_id=order_id_to_use,
                                           request_form_data=request.form,
                                           selected_product_details_display='ไม่พบสินค้าที่ระบุ',
                                           selected_product_barcode=selected_product_barcode,
                                           pre_filled_products_id_input=products_id_input)
                elif quantity > product_info['stock']: 
                    msg = f"สินค้า {product_info['products_name']} มีสต็อกไม่พอ. มีในสต็อก: {product_info['stock']}"
                    flash(msg, 'danger')
                    conn.close()
                    return render_template("cart.html", orders=[], products_data_string=products_data_string, users=users_data, msg=msg,
                                           current_auto_order_id=order_id_to_use,
                                           request_form_data=request.form,
                                           selected_product_details_display=selected_product_details_display,
                                           selected_product_barcode=selected_product_barcode,
                                           pre_filled_products_id_input=pre_filled_products_id_input)
                else:
                    products_name = product_info['products_name']
                    
                    cursor.execute("SELECT id, quantity FROM tbl_order WHERE products_id = %s AND order_id = %s AND email = %s",
                                   (products_id_input, order_id_to_use, email))
                    existing_order_item = cursor.fetchone()

                    try:
                        if existing_order_item:
                            new_qty = existing_order_item['quantity'] + quantity
                            if new_qty > product_info['stock']:
                                msg = f"ไม่สามารถเพิ่มได้ สินค้า {products_name} มีสต็อกไม่พอสำหรับยอดรวม. มีในสต็อก: {product_info['stock']}"
                                flash(msg, 'danger')
                            else:
                                cursor.execute("UPDATE tbl_order SET quantity = %s WHERE id = %s", (new_qty, existing_order_item['id']))
                                cursor.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (quantity, products_id_input))
                                conn.commit()
                                msg = f'เพิ่มจำนวนสินค้า {products_name} ในรายการสั่งซื้อ {order_id_to_use} สำเร็จ และอัปเดตสต็อกแล้ว!'
                                flash(msg, 'success')
                        else:
                            cursor.execute("""
                                INSERT INTO tbl_order (order_id, products_id, products_name, quantity, disquantity, email, barcode_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (order_id_to_use, products_id_input, products_name, quantity, disquantity, email, barcode_to_use_for_add))
                            cursor.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (quantity, products_id_input))
                            conn.commit()
                            msg = 'เพิ่มคำสั่งซื้อสำเร็จและอัปเดตสต็อกสินค้าแล้ว!'
                            flash(msg, 'success')

                    except mysql.connector.Error as err:
                        msg = f"เกิดข้อผิดพลาดในการดำเนินการคำสั่งซื้อ: {err}"
                        flash(msg, 'danger')
                    finally:
                        conn.close()
                        return redirect(url_for('cart')) 

            else:
                msg = "คุณไม่มีสิทธิ์เพิ่มคำสั่งซื้อ"
                flash(msg, 'danger')
                conn.close()
                return redirect(url_for('cart'))

    # --- สำหรับ GET Request และการแสดงผลครั้งสุดท้าย ---
    orders_data = []
    try:
        if session.get('role') == 'member':
            cursor.execute("""
                SELECT o.*, p.price
                FROM tbl_order o
                JOIN tbl_products p ON o.products_id = p.products_id
                WHERE o.email = %s AND o.order_id = %s
                ORDER BY o.id DESC
            """, (session['email'], current_order_id))
        elif session.get('role') in ['root_admin', 'administrator', 'moderator', 'viewer']:
            cursor.execute("""
                SELECT o.*, p.price
                FROM tbl_order o
                JOIN tbl_products p ON o.products_id = p.products_id
                WHERE o.order_id = %s
                ORDER BY o.id DESC
            """, (current_order_id,))
        orders_data = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูลคำสั่งซื้อ: {err}", 'danger')
    finally:
        if conn:
            conn.close()

    return render_template("cart.html",
                           orders=orders_data,
                           products_data_string=products_data_string, 
                           users=users_data,
                           search='',
                           msg=msg,
                           current_auto_order_id=current_order_id,
                           request_form_data=request.form if request.method == 'POST' else {},
                           selected_product_details_display=selected_product_details_display,
                           selected_product_barcode=selected_product_barcode, 
                           pre_filled_products_id_input=pre_filled_products_id_input)

# --- Routes สำหรับแก้ไขและลบรายการในตะกร้า (ย้ายมาอยู่นอกฟังก์ชัน cart()) ---

# แก้ไขรายการในตะกร้า
@app.route("/cart/edit/<int:item_id>", methods=["POST"])
@role_required(['root_admin', 'administrator', 'moderator', 'member'])
def edit_cart_item(item_id):
    conn_edit = get_db_connection()
    if not conn_edit:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return redirect(url_for('cart'))

    cursor_edit = conn_edit.cursor(dictionary=True)
    try:
        new_quantity = int(request.form['quantity'])
        new_disquantity = int(request.form['disquantity'])
        original_product_id = request.form['products_id'] # ต้องส่ง products_id มาด้วย
        original_order_id = request.form['order_id'] # ต้องส่ง order_id มาด้วย
        
        # ดึงข้อมูลสินค้านั้นๆ เพื่อตรวจสอบสต็อก
        cursor_edit.execute("SELECT stock, products_name FROM tbl_products WHERE products_id = %s", (original_product_id,))
        product_info = cursor_edit.fetchone()

        if not product_info:
            flash(f"ไม่พบสินค้า ID {original_product_id} สำหรับแก้ไข.", 'danger')
            conn_edit.close()
            return redirect(url_for('cart'))

        current_stock = product_info['stock']

        # ดึงปริมาณเดิมของรายการในคำสั่งซื้อเพื่อคำนวณการเปลี่ยนแปลงสต็อก
        cursor_edit.execute("SELECT quantity FROM tbl_order WHERE id = %s", (item_id,))
        current_order_qty_result = cursor_edit.fetchone()
        current_order_qty = current_order_qty_result['quantity'] if current_order_qty_result else 0

        # คำนวณความแตกต่างของจำนวนที่เปลี่ยนไป
        qty_change = new_quantity - current_order_qty

        if new_quantity <= 0:
            flash("จำนวนสินค้าต้องมากกว่า 0 หากต้องการลบ กรุณากดปุ่มลบ.", 'warning')
            conn_edit.close()
            return redirect(url_for('cart'))
        
        # ตรวจสอบสต็อกหลังจากปรับเปลี่ยน
        # if current_stock - qty_change < 0: # <-- แก้ไข logic นี้เล็กน้อย
        if current_stock < qty_change: # ถ้าสต็อกปัจจุบันน้อยกว่าจำนวนที่เพิ่มขึ้นจากเดิม
            flash(f"ไม่สามารถแก้ไขได้: สินค้า {product_info['products_name']} มีสต็อกไม่พอ. มีในสต็อก: {current_stock} ต้องการเพิ่ม {qty_change} ชิ้น", 'danger')
            conn_edit.close()
            return redirect(url_for('cart'))

        cursor_edit.execute("""
            UPDATE tbl_order
            SET quantity = %s, disquantity = %s
            WHERE id = %s AND order_id = %s
        """, (new_quantity, new_disquantity, item_id, original_order_id)) # เพิ่ม order_id ใน WHERE เพื่อความปลอดภัย

        # อัปเดตสต็อกใน tbl_products
        cursor_edit.execute("UPDATE tbl_products SET stock = stock - %s WHERE products_id = %s", (qty_change, original_product_id))

        conn_edit.commit()
        flash(f'แก้ไขรายการ ID {item_id} ในคำสั่งซื้อ {original_order_id} สำเร็จแล้ว!', 'success')

    except ValueError:
        flash("จำนวนและทิ้งต้องเป็นตัวเลขที่ถูกต้อง.", 'danger')
    except mysql.connector.Error as err:
        flash(f"เกิดข้อผิดพลาดในการแก้ไขรายการ: {err}", 'danger')
        conn_edit.rollback()
    finally:
        if conn_edit:
            conn_edit.close()
    return redirect(url_for('cart'))

# ลบรายการในตะกร้า
@app.route("/cart/delete/<int:item_id>", methods=["POST"])
@role_required(['root_admin', 'administrator', 'moderator', 'member'])
def delete_cart_item(item_id):
    conn_del = get_db_connection()
    if not conn_del:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return redirect(url_for('cart'))

    cursor_del = conn_del.cursor(dictionary=True)
    try:
        # ดึงข้อมูลรายการที่จะลบ เพื่อคืนสต็อก
        cursor_del.execute("SELECT products_id, quantity, order_id FROM tbl_order WHERE id = %s", (item_id,))
        item_to_delete = cursor_del.fetchone()

        if not item_to_delete:
            flash("ไม่พบรายการที่จะลบ.", 'danger')
            conn_del.close()
            return redirect(url_for('cart'))

        # คืนสต็อกสินค้า
        cursor_del.execute("UPDATE tbl_products SET stock = stock + %s WHERE products_id = %s",
                           (item_to_delete['quantity'], item_to_delete['products_id']))

        # ลบรายการออกจาก tbl_order
        cursor_del.execute("DELETE FROM tbl_order WHERE id = %s", (item_id,))
        
        conn_del.commit()
        flash(f'ลบรายการ ID {item_id} ออกจากคำสั่งซื้อ {item_to_delete["order_id"]} สำเร็จแล้ว!', 'success')

    except mysql.connector.Error as err:
        flash(f"เกิดข้อผิดพลาดในการลบรายการ: {err}", 'danger')
        conn_del.rollback()
    finally:
        if conn_del:
            conn_del.close()
    return redirect(url_for('cart'))





@app.route("/export_orders_pdf")
@role_required(['root_admin', 'administrator', 'moderator', 'member'])
def export_orders_pdf():
    """Exports order data to a PDF file."""
    conn = get_db_connection()
    if not conn:
        flash("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล.", 'danger')
        return redirect(url_for('tbl_order'))

    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch orders, ensuring barcode_id is from tbl_order
        base_query = """
            SELECT 
                o.id, 
                o.order_id, 
                o.products_id, 
                o.products_name, 
                o.quantity, 
                o.disquantity, 
                o.email, 
                o.order_date,
                o.barcode_id, 
                p.category_id 
            FROM tbl_order o
            LEFT JOIN tbl_products p ON o.products_id = p.products_id
        """
        query_params = []
        if session.get('role') == 'member':
            base_query += " WHERE o.email = %s"
            query_params.append(session['email'])
        
        base_query += " ORDER BY o.order_date DESC"
        
        cursor.execute(base_query, tuple(query_params))
        orders = cursor.fetchall()

        # Render HTML template for PDF
        html = render_template("pdf_template_orders.html", orders=orders)
        
        # Create a PDF from HTML
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            html,                # the HTML to convert
            dest=pdf_buffer)     # file handle to receive result

        if pisa_status.err:
            flash(f"เกิดข้อผิดพลาดในการสร้าง PDF: {pisa_status.err}", 'danger')
            return redirect(url_for('tbl_order'))

        pdf_buffer.seek(0)
        
        response = make_response(pdf_buffer.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=orders_report.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response
    except mysql.connector.Error as err:
        flash(f"เกิดข้อผิดพลาดในการส่งออกรายงานคำสั่งซื้อ: {err}", 'danger')
        return redirect(url_for('tbl_order'))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)