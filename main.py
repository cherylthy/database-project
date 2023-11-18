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
import logging
from datetime import datetime, timedelta

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

@app.route('/')
def select_all_from_table():
    try:
        # Fetch distinct car makes for the dropdown
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT DISTINCT car_make FROM CarInventory")
        car_makes = [make[0] for make in cursor.fetchall()]
        
        # Get filtering and sorting parameters from the request
        make_filter = request.args.get('make', default=None, type=str)
        sort_by = request.args.get('sort_by', default='car_make', type=str)
        sort_order = request.args.get('sort_order', default='asc', type=str)
        page = request.args.get('page', default=1, type=int)

        # Pagination settings
        items_per_page = 15  # Adjust this based on your preference
        offset = (page - 1) * items_per_page

        # Build the SQL query based on filtering and sorting parameters
        query = "SELECT license_plate, car_make, car_model, daily_rate FROM CarInventory"

        # Check if there's a make_filter parameter
        if make_filter:
            query += f" WHERE car_make = '{make_filter}'"

        query += f" ORDER BY {sort_by} {sort_order} LIMIT {offset}, {items_per_page}"

        cursor = mysql.get_db().cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()

        # Get total count for pagination
        total_query = "SELECT COUNT(*) FROM CarInventory"

        # Check if there's a make_filter parameter
        if make_filter:
            total_query += f" WHERE car_make = '{make_filter}'"

        cursor = mysql.get_db().cursor()
        cursor.execute(total_query)
        total_items = cursor.fetchone()[0]
        cursor.close()

        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0)

        return render_template('CarList.html', data=data, current_page=page, total_pages=total_pages, car_makes=car_makes)
    
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output a message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'Email' in request.form and 'Password' in request.form:
        # Check if email and password exist in the database
        email = request.form['Email']
        password = request.form['Password']
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM UserAccounts WHERE Email = %s AND Password = %s', (email, password,))
        account = cursor.fetchone()

        # If account exists in the accounts table in your database
        if account:
            session['loggedin'] = True
            session['UserID'] = account[0]
            session['Email'] = account[1]

            # Redirect the user to the "CarList" page after successful login
            return redirect(url_for('select_all_from_table'))

        else:
            # Account doesn't exist or username/password is incorrect
            msg = 'Incorrect username/password!'

    is_user_logged_in = 'loggedin' in session and session['loggedin']

    # Show the login form with a message (if any)
    return render_template('login.html', msg=msg, is_user_logged_in=is_user_logged_in)

    
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
        cursor.execute("SELECT DISTINCT * FROM CarInventory INNER JOIN Rentals ON CarInventory.license_plate = Rentals.PlateID WHERE Rentals.UserID =  %s LIMIT 5", (user_id))
        booking_data = cursor.fetchall()
        cursor.close()
        if booking_data:
            session['RentalID'] = booking_data[0][0]  # Store the RentalID from the first row of the data
            # Check if user exists
        if not booking_data:
            # return jsonify({'error': 'User not found'})
            pass

        return render_template('account_page.html', data=data, booking_data=booking_data)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update', methods=['POST'])
def update_account():
    try:
         if 'UserID' in session:
            user_id = session['UserID']
            new_name = request.form.get('name')
            new_email = request.form.get('email')
            new_age = request.form.get('age')
            
            # Update the user information in the database using SQL UPDATE statement
            cursor = mysql.get_db().cursor()
            cursor.execute("UPDATE UserAccounts SET Name=%s, Email=%s, Age=%s WHERE UserID=%s",
                            (new_name, new_email, new_age, user_id))
            mysql.get_db().commit()
            cursor.close()
            
            return redirect('/account')  # Redirect to account page after successful update
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'UserID' not in session:
        return jsonify({'error': 'User not logged in'})
    
    user_id = session['UserID']
    cursor = mysql.get_db().cursor()
    cursor.execute("DELETE FROM UserAccounts WHERE UserID = %s", (user_id ))
    mysql.get_db().commit()
    cursor.close()

    return redirect('/login')

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if 'UserID' not in session:
        return jsonify({'error': 'User not logged in'})
    user_id = session['UserID']
    booking_id = request.form.get('booking_id')
    cursor = mysql.get_db().cursor()
    cursor.execute("DELETE FROM Rentals WHERE UserID = %s AND RentalID = %s", (user_id, booking_id))
    mysql.get_db().commit()
    cursor.close()
    return redirect('/bookings-overview')

datepicker(app)
    
@app.route('/listing/<car_id>')
def display_car_details(car_id):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory WHERE license_plate = %s", (car_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            column_names = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(column_names, data))

            # Now you can access the values using column names
            license_plate = row_dict['license_plate']
            car_make = row_dict['car_make']
            car_model = row_dict['car_model']
            body_type = row_dict['body_type']
            # year = row_dict['year']
            color = row_dict['color']
            transmission_type = row_dict['transmission_type']
            # seats = row_dict['seats']
            price = row_dict['daily_rate']
            safety_features = row_dict['safety_features']
            entertainment_features = row_dict['entertainment_features']
            interior_features = row_dict['interior_features']
            exterior_features = row_dict['exterior_features']
            
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT color, license_plate FROM CarInventory WHERE car_model = %s AND color != %s", (car_model, color,))
        colors = cursor.fetchall()
        cursor.close()
        
        all_reviews = crud.get("reviews")
        reviews = [review for review in all_reviews if review.get("carID") == car_id]
        
        return render_template('listing.html', license_plate=license_plate, car_make=car_make, car_model=car_model, 
                               body_type=body_type, color=color, transmission_type=transmission_type, price=price, 
                               safety_features=safety_features, entertainment_features=entertainment_features, 
                               interior_features=interior_features, exterior_features=exterior_features, 
                               car_id=car_id, colors=colors, reviews=reviews)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/booking/<car_id>')
def booking_page(car_id):
    try:
        user_id = session['UserID']
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM UserAccounts WHERE UserID = %s", (user_id,))
        userdetails = cursor.fetchone()
        cursor.close()
        if userdetails:
            name = userdetails[2]
            phone_no = userdetails[4]
            email = userdetails[5]
        
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory WHERE license_plate = %s", (car_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            license_plate = data[0]
            car_make = data[1]
            car_model = data[2]
            year = data[3]
            body_type = data[4]
            price = data[16]
            
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM Rentals WHERE PlateID = %s", (car_id,))
        rentals = cursor.fetchall()
        cursor.close()
        
        booked_dates = []
        for rental in rentals:
            start_date = rental[3]
            end_date = rental[4]
            
            current_date = start_date
            while current_date <= end_date:
                booked_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        return render_template('booking.html', license_plate=license_plate, car_make=car_make, car_model=car_model, 
                               year=year, body_type=body_type, car_id=car_id, name=name, phone_no=phone_no, email=email, price=price, booked_dates=booked_dates)

    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/checkout', methods=['POST'])
def pass_to_checkout():
    try:
        license_plate = request.form['license_plate']
        date_range = request.form['booking_date']
        total_amount = request.form['final_amount']
        date_range = date_range.split(" to ")
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            # If there's only one date, set both start_date and end_date to that date
            start_date = date_range[0]
            end_date = date_range[0]
        user_id = session['UserID']
        
        return render_template('checkout.html', license_plate=license_plate, start_date=start_date, end_date=end_date, user_id=user_id, total_amount=total_amount)
    except Exception as e:
        return jsonify({'error': str(e)})
    
def post_rental(user_id, plate_id, start_date, end_date):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute('INSERT INTO Rentals VALUES (NULL, %s, %s, %s, %s)', (user_id, plate_id, start_date, end_date))
        mysql.get_db().commit()
        rental_id = cursor.lastrowid
        cursor.close()
        
        return rental_id
    except Exception as e:
        print(str(e))
        return None
    
@app.route('/handle_booking', methods=['POST'])
def handle_booking():
    try:
        user_id = session['UserID']
        plate_id = request.form['license_plate']
        date_range = request.form['booking_date']
        date_range = date_range.split(" to ")
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            # If there's only one date, set both start_date and end_date to that date
            start_date = date_range[0]
            end_date = date_range[0]

        # Insert rental information and redirect to rental page
        rental_id = post_rental(user_id, plate_id, start_date, end_date)
        if rental_id is not None:
            return jsonify({'rental_id': rental_id})
        else:
            return jsonify({'error': 'Failed to insert rental information.'})
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/rental/<rental_id>')
def load_rental(rental_id):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT CarInventory.car_make, CarInventory.car_model, CarInventory.license_plate, Rentals.StartDate, Rentals.EndDate FROM CarInventory INNER JOIN Rentals ON CarInventory.license_plate = Rentals.PlateID WHERE RentalID = %s", (rental_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            car_make, car_model, license_plate, StartDate, EndDate = data
            
            return render_template('rental.html', start_date=StartDate, end_date=EndDate, rental_id=rental_id, car_type=car_make + car_model, license_plate=license_plate)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/create_listings', methods=['GET', 'POST'])
def add_listing():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        car_make = request.form['car_make']
        car_model = request.form['car_model']
        body_type = request.form['body_type']
        engine_size = request.form['engine_size']
        transmission_type = request.form['transmission_type']
        price = request.form['price']

        cursor = mysql.get_db().cursor()
        
        cursor.execute('INSERT INTO CarInventory VALUES (%s, %s, %s, %s, NULL, NULL, NULL, %s, NULL, %s, NULL, NULL, NULL, NULL, NULL, NULL, %s)', (license_plate, car_make, car_model, body_type, engine_size, transmission_type, price))
        mysql.get_db().commit()
        # Success message or redirect
        cursor.close()
        # Redirect to the same page after successful form submission
        return redirect(url_for('add_listing'))
    
    return render_template('create_listings.html', message='You have successfully listed a car!')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'GET':
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT `license_plate`, `car_make`, `car_model`, `body_type`, `engine_size`, `transmission_type`,  `daily_rate` FROM CarInventory")
        data = cursor.fetchall()
        cursor.close()
        return render_template('admin_dashboard.html', data=data)
    elif request.method == 'POST':
        try:
            # Get the selected rows from the request
            selected_rows = request.get_json().get('rows')

            # Delete selected rows from the database
            delete_car_inventory(selected_rows)

            return jsonify({'message': 'Rows deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)})
    
    return render_template('admin_dashboard.html', data=data)
def fetch_car_inventory():
    # Fetch data from the CarInventory table
    with mysql.get_db.cursor() as cursor:
        cursor.execute("SELECT * FROM CarInventory")
        data = cursor.fetchall()
    return data

def delete_car_inventory(selected_rows):
    # Assuming 'license_plate' is the primary key column
    with mysql.get_db().cursor() as cursor:
        for license_plate in selected_rows:
            cursor.execute("DELETE FROM CarInventory WHERE license_plate = %s", (license_plate,))
    mysql.get_db().commit()


@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'admin_loggedin' in session and session['admin_loggedin']:
        if request.method == 'GET':
            data = fetch_user_accounts()
            return render_template('manage_users.html', data=data)

        elif request.method == 'POST':
            try:
                # Get the selected users from the request
                selected_users = request.get_json().get('users')

                # Delete selected users from the database
                delete_selected_users(selected_users)

                return jsonify({'message': 'Users deleted successfully'})
            except Exception as e:
                return jsonify({'error': str(e)})
    
    else:
        abort(403)  # HTTP status code for forbidden access

def fetch_user_accounts():
    with mysql.get_db().cursor() as cursor:
            cursor.execute("SELECT 'UserId', `Name`, `Age`, `PhoneNo`, `Email` FROM UserAccounts")
            data = cursor.fetchall()
    return data

def delete_selected_users(selected_users):
    with mysql.get_db().cursor() as cursor:
        for userid in selected_users:
            cursor.execute("DELETE FROM UserAccounts WHERE UserID = %s", (userid,))
    mysql.get_db().commit()

    

@app.route('/all-reviews')
def reviews():
    try:
        # Check if the user is logged in
        if 'UserID' not in session:
            return jsonify({'error': 'User not logged in'})

        user_id = session['UserID']

        result = crud.get("reviews")
        # document_id = generate_document_id()
        
        # Add a document to a collection with a specific ID
        # data = {"userID": 5432, "carID": 3333, "comments": "This car sucks", "ratings":4.5}
        # crud.add('reviews', data=data, document_id=document_id)
        
        return render_template('all_reviews.html', reviews=result)

        # cursor = mysql.get_db().cursor()
        # cursor.execute("SELECT * FROM CarInventory")
        # data = cursor.fetchall()
        # cursor.close()
        # return render_template('sql_test.html', data=data)

        # cursor = mysql.get_db().cursor()
        # # Fetch data only for the logged-in user
        # cursor.execute("SELECT * FROM UserAccounts WHERE UserID = %s", (user_id,))
        # data = cursor.fetchall()
        # cursor.close()
        
        # Check if user exists
        if not data:
            return jsonify({'error': 'User not found'})

        # return render_template('all_reviews.html', data=data)
    
    except Exception as e:
        return jsonify({'error': str(e)})
    

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
