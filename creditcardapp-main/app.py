from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your_secret_key_here")

# Initialize the database
def init_db():
    conn = sqlite3.connect('credit_card.db')
    cursor = conn.cursor()
    
    # Create User table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        zip TEXT NOT NULL,
        occupation TEXT NOT NULL,
        employment TEXT NOT NULL,
        credit_card TEXT NOT NULL,
        monthly_income REAL NOT NULL,
        annual_income REAL NOT NULL,
        credit_card_type TEXT NOT NULL,
        permit_amount REAL NOT NULL,
        aadhaar_id TEXT NOT NULL,
        pan_card TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create Application table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Under Review',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        logging.debug(f"Login attempt for email: {email}")
        
        conn = sqlite3.connect('credit_card.db')
        cursor = conn.cursor()
        
        # Check if admin login
        if email == 'admin@gmail.com' and password == 'admin123':
            session['admin'] = True
            conn.close()
            logging.debug("Admin login successful")
            return redirect(url_for('admin'))
        else:
            # First check if the email exists
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                logging.debug(f"Login failed: Email {email} does not exist")
                flash('Invalid email or password')
                conn.close()
                return render_template('login.html')
                
            # Debug the stored password
            logging.debug(f"Stored password for {email}: {user[2]}, Provided password: {password}")
            
            # Now check if password matches (case-insensitive)
            if user[2].lower() == password.lower():
                session['user_id'] = user[0]
                conn.close()
                logging.debug(f"Login successful for user {email}, user_id: {user[0]}")
                return redirect(url_for('account_details'))
            else:
                logging.debug(f"Login failed: Password does not match for {email}")
                flash('Invalid email or password')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            # Extract form data
            logging.debug("Processing application form submission")
            first_name = request.form['firstName']
            last_name = request.form['lastName']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirmPassword']
            phone = request.form['phone']
            dob = request.form['dob']
            gender = request.form['gender']
            address = request.form['address']
            city = request.form['city']
            zip_code = request.form['zip']
            occupation = request.form['occupation']
            employment = request.form['employment']
            credit_card = request.form['creditCard']
            
            # Convert numeric values
            try:
                monthly_income = float(request.form['monthlyIncome'])
                annual_income = float(request.form['annualIncome'])
            except ValueError as e:
                logging.error(f"Error converting income values: {e}")
                flash('Please enter valid income values')
                return redirect(url_for('apply'))
                
            credit_card_type = request.form['creditCardType']
            aadhaar_id = request.form['aadhaarId']
            pan_card = request.form['panCard']
            
            # Log the form data for debugging
            logging.debug(f"Form data: {email}, {first_name}, {last_name}, Card Type: {credit_card_type}")
            
            # Calculate permit amount based on card type
            if credit_card_type == 'Regular':
                permit_amount = monthly_income * 2
            elif credit_card_type == 'Premium':
                permit_amount = monthly_income * 3
            elif credit_card_type == 'SuperPremium':
                permit_amount = monthly_income * 4
            elif credit_card_type == 'CoBranded':
                permit_amount = monthly_income * 2.5
            elif credit_card_type == 'Business':
                permit_amount = monthly_income * 5
            elif credit_card_type == 'Cashback':
                permit_amount = monthly_income * 2.5
            elif credit_card_type == 'Secured':
                permit_amount = monthly_income * 1  # Secured cards typically match the security deposit
            elif credit_card_type == 'Travel':
                permit_amount = monthly_income * 3.5
            else:
                permit_amount = monthly_income * 2  # Default value
            
            if password != confirm_password:
                flash('Passwords do not match')
                return redirect(url_for('apply'))
            
            conn = sqlite3.connect('credit_card.db')
            cursor = conn.cursor()
            
            try:
                # Insert user into database
                insert_query = '''
                INSERT INTO users (email, password, first_name, last_name, phone, dob, gender, address, city, zip, 
                                  occupation, employment, credit_card, monthly_income, annual_income, 
                                  credit_card_type, permit_amount, aadhaar_id, pan_card, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(insert_query, (
                    email, password, first_name, last_name, phone, dob, gender, address, city, zip_code,
                    occupation, employment, credit_card, monthly_income, annual_income, credit_card_type,
                    permit_amount, aadhaar_id, pan_card, created_at
                ))
                
                # Get the user ID
                user_id = cursor.lastrowid
                logging.debug(f"User inserted successfully with ID: {user_id}")
                
                # Create application entry
                cursor.execute('INSERT INTO applications (user_id) VALUES (?)', (user_id,))
                logging.debug(f"Application created for user ID: {user_id}")
                
                # Commit the transaction
                conn.commit()
                
                # Store the user ID in session
                session['user_id'] = user_id
                logging.debug(f"User ID {user_id} stored in session")
                
                flash('Application submitted successfully')
                return redirect(url_for('success'))
            except sqlite3.IntegrityError as e:
                logging.error(f"Database integrity error: {e}")
                flash('Email already registered. Please login with your existing account.')
                conn.rollback()
                return redirect(url_for('login'))
            except Exception as e:
                logging.error(f"Unexpected error during database operation: {e}")
                flash('An error occurred during registration')
                conn.rollback()
            finally:
                conn.close()
        except Exception as e:
            logging.error(f"Unexpected error processing form: {e}")
            flash('An error occurred. Please try again.')
    
    return render_template('apply.html')

@app.route('/account_details')
def account_details():
    if 'user_id' not in session:
        logging.debug("No user_id in session, redirecting to login")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    logging.debug(f"Getting account details for user_id: {user_id}")
    
    conn = sqlite3.connect('credit_card.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        logging.debug(f"User with ID {user_id} not found")
        flash('User not found')
        conn.close()
        return redirect(url_for('login'))
    
    # Log user data for debugging (excluding password)
    logging.debug(f"User data: ID={user[0]}, Email={user[1]}, Name={user[3]} {user[4]}, Card Type={user[16]}")
    
    cursor.execute("SELECT status FROM applications WHERE user_id = ?", (user_id,))
    application = cursor.fetchone()
    logging.debug(f"Application status: {application[0] if application else 'None'}")
    
    conn.close()
    
    return render_template('account_details.html', user=user, application_status=application[0] if application else 'Under Review')

@app.route('/admin')
def admin():
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('credit_card.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT u.id, u.first_name || ' ' || u.last_name AS full_name, u.email, u.occupation, a.status
    FROM users u
    INNER JOIN applications a ON u.id = a.user_id
    ''')
    
    applications = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', applications=applications)

@app.route('/update_status/<int:user_id>/<status>')
def update_status(user_id, status):
    if 'admin' not in session or not session['admin']:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('credit_card.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE applications SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/card')
def card():
    return render_template('card.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/apply_Business')
def apply_Business():
    return render_template('apply_Business.html')

@app.route('/apply_Cashback')
def apply_Cashback():
    return render_template('apply_Cashback.html')

@app.route('/apply_CoBranded')
def apply_CoBranded():
    return render_template('apply_Co-branded.html')

@app.route('/apply_premium')
def apply_premium():
    return render_template('apply_premium.html')

@app.route('/apply_Secured')
def apply_Secured():
    return render_template('apply_Secured.html')

@app.route('/apply_superpremium')
def apply_superpremium():
    return render_template('apply_superpremium.html')

@app.route('/apply_Travel')
def apply_Travel():
    return render_template('apply_Travel.html')

@app.route('/apply_regular')
def apply_regular():
    return render_template('apply-regular.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
