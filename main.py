from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from firebase import Firebase
from flaskext.mysql import MySQL
import uuid
import MySQLdb.cursors
from flask_datepicker import datepicker
import MySQLdb.cursors, re, hashlib
from flask_debug import Debug
from functools import wraps
from flask import abort

app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Initialize MySQL
mysql = MySQL()

# MySQL configuration
app.config['MYSQL_DATABASE_HOST'] = '35.212.183.7'
app.config['MYSQL_DATABASE_USER'] = 'common'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dbpassword'
app.config['MYSQL_DATABASE_DB'] = 'inf2003'

mysql.init_app(app)
app.secret_key = 'secret'
Debug(app)

@app.route('/', methods=['GET', 'POST'])
def login():

    # Output a message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'Email' in request.form and 'Password' in request.form:

        # Check if email and password exist in database
        email = request.form['Email']
        password = request.form['Password']
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM UserAccounts WHERE Email = %s AND Password = %s', (email, password,))
        account = cursor.fetchone()

        # If account exists in accounts table in out database
        if account:
            session['loggedin'] = True
            session['UserID'] = account[0]
            session['Email'] = account[1]

            return 'Logged in successfully!'
        
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'

    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
   
# Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('UserID', None)
   session.pop('Email', None)

   # Redirect to login page
   return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():

    # Output message if something goes wrong...
    msg = ''

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'Name' in request.form and 'Password' in request.form and 'Age' in request.form and 'PhoneNo' in request.form and 'Email' in request.form:

        #Check for if account used to register exist in database
        name = request.form['Name']
        password = request.form['Password']
        age = request.form['Age']
        phoneno = request.form['PhoneNo']
        email = request.form['Email']

        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM UserAccounts WHERE Email = %s', (email,))
        account = cursor.fetchone()

        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Name must contain only characters!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
           #hash = password + app.secret_key
           # hash = hashlib.sha1(hash.encode())
           # password = hash.hexdigest()

            # Account doesn't exist, and the form data is valid, so insert the new account into the UserAccounts table
            cursor.execute('INSERT INTO UserAccounts VALUES (NULL, %s, %s, %s, %s, %s, NULL, NULL)', (password, name, age, phoneno, email))
            mysql.get_db().commit()
            msg = 'You have successfully registered!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)



#ADMIN
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''  # Output a message if something goes wrong...

    if request.method == 'POST' and 'Email' in request.form and 'Password' in request.form:
        email = request.form['Email']
        password = request.form['Password']

        # Check if the credentials belong to an admin
        admin_cursor = mysql.get_db().cursor()
        admin_cursor.execute('SELECT * FROM UserAccounts WHERE Email = %s AND Password = %s AND IsAdmin = 1', (email, password,))
        admin_account = admin_cursor.fetchone()

        if admin_account:
            session['admin_loggedin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Incorrect admin credentials!'

    return render_template('admin_login.html', msg=msg)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    cursor = mysql.get_db().cursor()
    cursor.execute("SELECT `license_plate`, `car_make`, `car_model`, `body_type`, `engine_size`, `transmission_type`,  `daily_rate` FROM CarInventory")
    data = cursor.fetchall()
    cursor.close()
    return render_template('admin_dashboard.html', data=data)




@app.route('/account')
def accounts():
    try:
        # Check if the user is logged in
        if 'UserID' not in session:
            return jsonify({'error': 'User not logged in'})

        user_id = session['UserID']

        cursor = mysql.get_db().cursor()
        # Fetch data only for the logged-in user
        cursor.execute("SELECT * FROM UserAccounts WHERE UserID = %s", (user_id,))
        data = cursor.fetchall()
        cursor.close()
        
        # Check if user exists
        if not data:
            return jsonify({'error': 'User not found'})

        return render_template('accounts_page.html', data=data)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update', methods=['POST'])
def update_account():
    try:
        if 'UserID' in session:
            user_id = session['UserID']
            new_name = request.form.get('name')
            new_email = request.form.get('email')
            new_password = request.form.get('password')
            
            # Update the user information in the database using SQL UPDATE statement
            cursor = mysql.get_db().cursor()
            cursor.execute("UPDATE UserAccounts SET Name=%s, Email=%s, Password=%s WHERE UserID=%s",
                           (new_name, new_email, new_password, user_id))
            mysql.get_db().commit()
            cursor.close()
            
            return redirect('/account')  # Redirect to account page after successful update
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
datepicker(app)

@app.route('/carlist')
def select_all_from_table():
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT license_plate, car_make, car_model FROM CarInventory")
        data = cursor.fetchall()
        cursor.close()
        return render_template('homepage.html', data=data)

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/listing/<carId>')
def display_car_details(carId):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory WHERE license_plate = %s", (carId,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            license_plate = data[0]
            car_make = data[1]
            car_model = data[2]
            year = data[3]
            body_type = data[4]
            
            return render_template('listing.html', license_plate=license_plate, car_make=car_make, car_model=car_model, year=year, body_type=body_type, carId=carId)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/booking/<carId>')
def booking_page(carId):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory WHERE license_plate = %s", (carId,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            license_plate = data[0]
            car_make = data[1]
            car_model = data[2]
            year = data[3]
            body_type = data[4]
            
            return render_template('booking.html', license_plate=license_plate, car_make=car_make, car_model=car_model, year=year, body_type=body_type, carId=carId)

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/checkout', methods=['POST'])
def pass_to_checkout():
    try:
        license_plate = request.form['licensePlate']
        # start_date = request.form['startDate']
        # end_date = request.form['endDate']
        date_range = request.form['bookingDate']
        date_range = date_range.split(" to ")
        start_date = date_range[0]
        end_date = date_range[1]
        UserId = session['UserID']
        
        return render_template('checkout.html', license_plate=license_plate, start_date=start_date, end_date=end_date, UserId=UserId)
    except Exception as e:
        return jsonify({'error': str(e)})
    
def post_rental(UserId, PlateId, StartDate, EndDate):
    try:
        # UserId = session['UserID']
        # PlateId = request.form['plateId']
        # StartDate = request.form['start_date']
        # EndDate = request.form['end_date']
        
        cursor = mysql.get_db().cursor()
        cursor.execute('INSERT INTO Rentals VALUES (NULL, %s, %s, %s, %s)', (UserId, PlateId, StartDate, EndDate))
        mysql.get_db().commit()
        rentalId = cursor.lastrowid
        cursor.close()
        
        return rentalId
        # return jsonify({'rentalId': rentalId})
    except Exception as e:
        print(str(e))  # Print the error for debugging
        return None
    
@app.route('/handle_booking', methods=['POST'])
def handle_booking():
    try:
        UserId = session['UserID']
        PlateId = request.form['licensePlate']
        # StartDate = request.form['start_date']
        # EndDate = request.form['end_date']
        dateRange = request.form['bookingDate']
        dateRange = dateRange.split(" to ")
        StartDate = dateRange[0]
        EndDate = dateRange[1]
        # Check the payment type
        # selected_payment_type = request.form['paymentType']

        # if selected_payment_type == 'codForm':
        #     # Show a confirmation popup for Cash on Delivery
        #     # return render_template('confirmation_popup.html', UserId=UserId, PlateId=PlateId, StartDate=StartDate, EndDate=EndDate)
        #     return jsonify({'message': 'Cash on delivery form submitted.'})

        # elif selected_payment_type == 'ccForm':
            # Insert rental information and redirect to rental page
        rentalId = post_rental(UserId, PlateId, StartDate, EndDate)
        if rentalId is not None:
            # return redirect(url_for('load_rental', rentalId=rentalId))
            return jsonify({'rentalId': rentalId})
        else:
            return jsonify({'error': 'Failed to insert rental information.'})
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/rental/<rentalId>')
def load_rental(rentalId):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM Rentals WHERE RentalID = %s", (rentalId,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            start_date = data[3]
            end_date = data[4]
            
            return render_template('rental.html', start_date=start_date, end_date=end_date, rentalId=rentalId)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
