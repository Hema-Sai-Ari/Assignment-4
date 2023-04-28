import json
import re   #regular expressions
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = 'your secret key'
sqlite_connection = sqlite3.connect('shopping.db')
sqlite_connection.execute('CREATE TABLE IF NOT EXISTS Customer ( id INTEGER PRIMARY KEY, firstName TEXT not null, lastName text not null, phone text not null, address text not null, email TEXT NOT NULL, password TEXT NOT NULL)')
sqlite_connection.execute('CREATE TABLE IF NOT EXISTS Cart (id INTEGER PRIMARY KEY, customer_id INTEGER, productName TEXT, originalPrice REAL, productPrice REAL, productImage TEXT, FOREIGN KEY(customer_id) REFERENCES Customer(id))')

@app.route('/')
def index():
    session.pop('_flashes', None) #to remove the already existing session messages
    logged_in = False
    if 'user_info' in session:
        conn = sqlite3.connect("shopping.db") 
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(session.get('user_info')), ))
        user = cursor.fetchone()
        logged_in = True
        return render_template('index.html', logged_in=logged_in, user = user)
    return render_template('index.html', logged_in=logged_in)

@app.route('/about')
def about():
    session.pop('_flashes', None)
    logged_in = False
    if 'user_info' in session:
        conn = sqlite3.connect("shopping.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(session.get('user_info')), ))
        user = cursor.fetchone()
        logged_in = True
        return render_template('about2.html', logged_in=logged_in, user = user)
    return render_template('about2.html', logged_in=logged_in)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    session.pop('_flashes', None)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not email or not password:
            flash('Please Enter your email and password', category='error')
        elif not re.match(r'[^@]+@[^@]+.[^@]+', email):
            flash("You entered an invalid email", category='error')
        elif not len(password) > 3:
            flash('Password must contain minimum of 4 characters', category='error')
        else:
            sqlite_connection = sqlite3.connect('shopping.db')
            sqlite_cursor = sqlite_connection.cursor()
            sqlite_cursor.execute("Select * from Customer where email = ? and password = ?", (email, password))
            user_detail = sqlite_cursor.fetchone()
            if user_detail:
                session['user_info'] = user_detail[0]
                flash("Logged in Successfully", category='success')
                return render_template('index.html', user = user_detail)
            else:
                flash("You have entered invalid email/password", category='error')
    return render_template('signin2.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session.pop('_flashes', None)
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        phone = request.form['phone']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        confPassword = request.form['confPassword']
        phone_regex = re.compile(r'^\d{3}-?\d{3}-?\d{4}$')
        if not firstName or not lastName or not phone or not address or not email or not password or not confPassword:
            flash('Please Enter your email and password', category='error')
        elif not bool(re.match(phone_regex, phone)):
            flash("You entered an invalid phone number", category='error')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("You entered an invalid email", category='error')
        elif not len(password) > 3:
            flash('Password must contain minimum of 4 characters', category='error')
        elif not password == confPassword:
            flash('Password and confirm password should be same', category='error')
        else:
            sqlite_connection = sqlite3.connect('shopping.db')
            sqlite_cursor = sqlite_connection.cursor()
            sqlite_cursor.execute("Select * from Customer where email = ?", (email, ))
            isUserExisted = sqlite_cursor.fetchone()
            if not isUserExisted:
                sqlite_connection = sqlite3.connect('shopping.db')
                sqlite_cursor = sqlite_connection.cursor()
                sqlite_cursor.execute('Insert into Customer (firstName, lastName, phone, address, email, password) values (?, ?, ?, ?, ?, ?)', (firstName, lastName, phone, address, email, password))
                sqlite_connection.commit()
                sqlite_cursor.execute("Select * from Customer where email = ? and password = ?", (email, password))
                user_detail = sqlite_cursor.fetchone()
                session['user_info'] = user_detail[0]
                flash("Profile created Successfully", category='success')
                return render_template('index.html', user = user_detail)
            else:
                flash("Account already exists. Please try to login.", category='error')
    return render_template('signup2.html')

@app.route('/check-user')
def check_user():
    logged_in = False
    if 'user_info' in session:
        conn = sqlite3.connect("shopping.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(session.get('user_info')), ))
        user = cursor.fetchone()
        logged_in = True
        return jsonify(logged_in=logged_in, user = user)
    return jsonify(logged_in=logged_in)

@app.route('/addToCart', methods=["POST"])
def addToCart():
    if 'user_info' in session:
        item = request.json.get('item')
        customer_id = item.get('customer_id')
        product_name = item.get('productName')
        original_price = item.get('originalPrice')
        product_price = item.get('productPrice')
        product_image = item.get('productImage')
        sqlite_connection = sqlite3.connect('shopping.db')
        sqlite_cursor = sqlite_connection.cursor()
        sqlite_cursor.execute("Insert into Cart (customer_id, productName, originalPrice, productPrice, productImage) values (?, ?, ?, ?, ?)", (customer_id, product_name, original_price, product_price, product_image))
        sqlite_connection.commit()
        return jsonify(success=True)
    else:
        return jsonify(success = False)

@app.route('/remove_item', methods=["POST"])
def remove_item():
    if 'user_info' in session:
        item_id = request.form["item_id"]
        sqlite_connection = sqlite3.connect('shopping.db')
        sqlite_cursor = sqlite_connection.cursor()
        sqlite_cursor.execute("delete from Cart where id = ?", (int(item_id), ))
        sqlite_connection.commit()
        return  redirect(url_for('cart'))
    else:
        return  redirect(url_for('cart'))

@app.route('/cart')
def cart():
    user_info = session.get('user_info')
    if user_info:
        # User is logged in, display icon and signout button
        sqlite_connection = sqlite3.connect("shopping.db")
        sqlite_cursor = sqlite_connection.cursor()
        sqlite_cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(user_info), ))
        user = sqlite_cursor.fetchone()
        sqlite_cursor.execute("select * from Cart where customer_id = ?", (int(user_info), ))
        cart_items = sqlite_cursor.fetchall()
        total_price = sum(item[4] for item in cart_items)
        return render_template('cart.html', logged_in=True, user=user, cart_items = cart_items, total_price = total_price)
    return redirect('/signin')

@app.route('/checkout', methods=["GET", "POST"])
def checkout():
    print(f'asdfghtr')
    user_info = session.get('user_info')
    if user_info:
        sqlite_connection = sqlite3.connect("shopping.db")
        sqlite_cursor = sqlite_connection.cursor()
        sqlite_cursor.execute('DELETE FROM Cart WHERE customer_id = ? ', (int(user_info), ))
        sqlite_connection.commit()
        sqlite_cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(user_info), ))
        user = sqlite_cursor.fetchone()
        return render_template('cart.html', user = user)
    return jsonify(errorDeleting = True)

@app.route('/analytics')
def analytics():
    user_info = session.get('user_info')
    if user_info:
        # User is logged in, display icon and signout button
        conn = sqlite3.connect("shopping.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Customer WHERE id = ? ', (int(user_info), ))
        user = cursor.fetchone()
        return render_template('analytics2.html', logged_in=True, user=user)
    return render_template('analytics2.html')

# Signout route
@app.route('/logout')
def logout():
    session.pop('user_info', None)
    session.pop('_flashes', None)
    return redirect('/signin')

# Users list
@app.route('/user_db')
def user_db():
    sqlite_connection=sqlite3.connect('shopping.db')
    sqlite_connection.row_factory = sqlite3.Row
    
    sqlite_cursor = sqlite_connection.cursor()
    
    sqlite_cursor.execute('Select * from Customer')
    rows = sqlite_cursor.fetchall()
    return render_template('user_db.html', rows = rows)

# Users list
@app.route('/cart_db')
def cart_db():
    sqlite_connection=sqlite3.connect('shopping.db')
    sqlite_connection.row_factory = sqlite3.Row
    
    sqlite_cursor = sqlite_connection.cursor()
    
    sqlite_cursor.execute('Select * from Cart')
    rows = sqlite_cursor.fetchall()
    return render_template('cart_db.html', rows = rows)