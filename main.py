from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_file, abort
from firebase import Firebase
from flaskext.mysql import MySQL
import uuid
import MySQLdb.cursors, re, hashlib
from flask_debug import Debug
from functools import wraps
import logging
from datetime import datetime, timedelta
from flask_paginate import Pagination
from firebase_admin import storage
import os
from google.cloud import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from MySQL_cred import MYSQL_CONFIG



app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Initialize MySQL
mysql = MySQL()

# MySQL configuration
app.config['MYSQL_DATABASE_HOST'] = MYSQL_CONFIG['host']
app.config['MYSQL_DATABASE_USER'] = MYSQL_CONFIG['user']
app.config['MYSQL_DATABASE_PASSWORD'] = MYSQL_CONFIG['password']
app.config['MYSQL_DATABASE_DB'] = MYSQL_CONFIG['db']

mysql.init_app(app)
app.secret_key = 'secret'
Debug(app)

# Generate a random unique identifier
def generate_document_id():
    unique_id = str(uuid.uuid4())
    return f"reviews-{unique_id}"

# Generate a unique identifier (UUID) and append it to the original filename
def generate_unique_filename(original_filename):
    unique_id = str(uuid.uuid4())
    _, file_extension = os.path.splitext(original_filename)
    unique_filename = f"{unique_id}{file_extension}"
    return unique_filename

def upload_image_to_storage(image):
    bucket = storage.bucket()
    # Generate a unique filename or use other logic
    filename = f"review_images/{generate_unique_filename(image.filename)}"
    
    blob = bucket.blob(filename)
    blob.upload_from_string(image.read(), content_type=image.content_type)
    blob.make_public()

    # Get the public URL of the uploaded image
    image_url = blob.public_url
    return image_url

@app.route('/')
def select_all_from_table():
    try:
        # Fetch distinct car makes for the dropdown
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT DISTINCT car_make FROM CarInformation")
        car_makes = [make[0] for make in cursor.fetchall()]
        
        # Get filtering and sorting parameters from the request
        make_filter = request.args.get('make', default=None, type=str)
        sort_by = request.args.get('sort_by', default='car_make', type=str)
        sort_order = request.args.get('sort_order', default='asc', type=str)
        page = request.args.get('page', default=1, type=int)

        # Pagination settings
        items_per_page = 15
        offset = (page - 1) * items_per_page

        # Build the SQL query based on filtering and sorting parameters
        query = """
        SELECT v.license_plate, f.car_make, v.car_model, f.daily_rate, i.image_path 
        FROM ((CarInventory v INNER JOIN CarInformation f ON v.car_model = f.car_model) 
        INNER JOIN CarImage i ON v.car_model = i.car_model)
        """


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
            # Account doesn't exist, and the form data is valid, so insert the new account into the UserAccounts table
            cursor.callproc('AddUserAccount', (password, name, age, phoneno, email))
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

        # Call the stored procedure
        admin_cursor = mysql.get_db().cursor()
        admin_cursor.callproc('ValidateAdminCredentials', (email, password))
        p_is_valid = admin_cursor.fetchone()

        if p_is_valid:
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
        cursor.callproc('GetUserAccountData', (user_id,))
        data = cursor.fetchall()
        cursor.callproc('GetDistinctBookingForUser', (user_id,))
        booking_data = cursor.fetchall()
        cursor.close()
        if booking_data:

            # Store the RentalID from the first row of the data
            session['RentalID'] = booking_data[0][0] 

            # Check if user exists
        if not booking_data:
            # return jsonify({'error': 'User not found'})
            pass

        all_reviews = crud.get("reviews")
        reviews = [review for review in all_reviews if review.get("userID") == user_id]

        return render_template('account_page.html', data=data, booking_data=booking_data, reviews=reviews)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update', methods=['POST'])
def update_account():
    try:
         if 'UserID' in session:
            user_id = session['UserID']
            print(user_id)
            new_name = request.form.get('name')
            new_age = request.form.get('age')
            
            # Input validation
            if not new_name or not new_age:
                return jsonify({'error': 'Incomplete data provided'})

            cursor = mysql.get_db().cursor()
            cursor.callproc('UpdateUserAccount', (user_id, new_name, new_age))
            mysql.get_db().commit()
            cursor.close()
                
            return redirect('/account')
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'UserID' not in session:
        return jsonify({'error': 'User not logged in'})
    
    user_id = session['UserID']
    cursor = mysql.get_db().cursor()
    cursor.callproc('DeleteUserAccount', (user_id,))
    mysql.get_db().commit()
    cursor.close()

    return redirect('/login')

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if 'UserID' not in session:
        return jsonify({'error': 'User not logged in'})
    
    user_id = session['UserID']
    
    # Check if 'booking_id' is present in the form data
    if 'rental_id' not in request.form:
        return jsonify({'error': 'Booking ID not found in form data'})

    rental_id = request.form.get('rental_id')

    cursor = mysql.get_db().cursor()
    cursor.callproc('CancelBooking', (user_id, rental_id))
    mysql.get_db().commit()
    cursor.close()

    return redirect('/account')


    
@app.route('/listing/<car_id>')
def display_car_details(car_id):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory v INNER JOIN CarInformation f ON v.car_model = f.car_model INNER JOIN CarImage i ON v.car_model = i.car_model WHERE license_plate = %s", (car_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            column_names = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(column_names, data))

            license_plate = row_dict['license_plate']
            car_make = row_dict['car_make']
            car_model = row_dict['car_model']
            body_type = row_dict['body_type']
            engine_size = row_dict['engine_size']
            color = row_dict['color']
            transmission_type = row_dict['transmission_type']
            price = row_dict['daily_rate']
            safety_features = row_dict['safety_features']
            entertainment_features = row_dict['entertainment_features']
            interior_features = row_dict['interior_features']
            exterior_features = row_dict['exterior_features']
            image_path = row_dict['image_path']
            
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT color, license_plate FROM CarInventory WHERE car_model = %s AND color != %s", (car_model, color,))
        colors = cursor.fetchall()
        cursor.close()
        
        table = crud.db.collection("reviews")
        query = table.order_by("reviewDate", direction=firestore.Query.DESCENDING)
        results = query.get()
        reviews = [review.to_dict() for review in results]
        reviews = [review for review in reviews if review.get("plateID") == car_id]

        return render_template('listing.html', license_plate=license_plate, car_make=car_make, car_model=car_model, 
                               body_type=body_type, color=color, transmission_type=transmission_type, price=price, 
                               safety_features=safety_features, entertainment_features=entertainment_features, 
                               interior_features=interior_features, exterior_features=exterior_features, 
                               image_path=image_path, engine_size=engine_size, car_id=car_id, colors=colors, reviews=reviews)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/booking/<car_id>')
def booking_page(car_id):
    try:
        user_id = session['UserID']
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM UserAccounts WHERE user_id = %s", (user_id,))
        userdetails = cursor.fetchone()
        cursor.close()
        if userdetails:
            name = userdetails[2]
            phone_no = userdetails[4]
            email = userdetails[5]
        
        cursor = mysql.get_db().cursor()
        cursor.execute('''SELECT v.license_plate, f.car_make, v.car_model, f.daily_rate, i.image_path FROM ((CarInventory v INNER JOIN CarInformation f ON v.car_model = f.car_model) 
                       INNER JOIN CarImage i ON v.car_model = i.car_model) WHERE license_plate = %s''', (car_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            license_plate = data[0]
            car_make = data[1]
            car_model = data[2]
            price = data[3]
            image_path = data[4]
            
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM Rentals WHERE license_plate = %s", (car_id,))
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
                               image_path=image_path, car_id=car_id, name=name, phone_no=phone_no, email=email, price=price, booked_dates=booked_dates)

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
    
def post_rental(user_id, plate_id, start_date, end_date, total_amount, timestamp):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute('INSERT INTO Rentals VALUES (NULL, %s, %s, %s, %s, %s, %s)', (user_id, plate_id, start_date, end_date, total_amount, timestamp))
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
        total_amount = request.form['final_amount']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        date_range = date_range.split(" to ")
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            # If there's only one date, set both start_date and end_date to that date
            start_date = date_range[0]
            end_date = date_range[0]

        # Insert rental information and redirect to rental page
        rental_id = post_rental(user_id, plate_id, start_date, end_date, total_amount, timestamp)
        if rental_id is not None:
            return jsonify({'rental_id': rental_id})
        else:
            return jsonify({'error': 'Failed to insert rental information.'})
            
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/rental/<rental_id>', methods=['GET', 'POST'])
def load_rental(rental_id):
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute('''SELECT R.user_id, R.license_plate, R.start_date, R.end_date, R.total_amount, R.timestamp, A.name, F.car_make, F.car_model
                       FROM Rentals R
                       INNER JOIN UserAccounts A ON R.user_id = A.user_id
                       INNER JOIN CarInventory V ON R.license_plate = V.license_plate
                       INNER JOIN CarInformation F ON V.car_model = F.car_model
                       WHERE R.rental_id = %s''', (rental_id,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            user_id, license_plate, StartDate, EndDate, total_amount, timestamp, name, car_make, car_model, = data

            # Store data in session
            session['user_id'] = user_id
            session['user_name'] = name
            session['plate_id'] = license_plate
            session['rental_id'] = rental_id


        return render_template('rental.html', start_date=StartDate, end_date=EndDate, rental_id=rental_id, car_type=car_make + car_model, license_plate=license_plate, total_amount=total_amount, timestamp=timestamp, message='You have successfully returned the car!')
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_review():
    try:
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        plate_id = session.get('plate_id')
        rental_id = session.get('rental_id')

        review_description = request.form.get('review_description')
        selected_rating = request.form.get('rate')  # Retrieve the selected rating
        if selected_rating is not None and selected_rating.isdigit():
            selected_rating = int(selected_rating)
        else:
            selected_rating = 0

        # Generate a document ID or use any logic suitable for your application
        '''this is for firebase'''
        document_id = generate_document_id()
        # Set the review date to the current date and time
        current_date = datetime.now()
        review_date = current_date.strftime('%Y-%m-%d %H:%M:%S')

        # Access uploaded files
        images = request.files.getlist('image[]')

        # Process and save the images as needed
        image_urls = []
        for image in images:
            if allowed_file(image.filename):
                image_url = upload_image_to_storage(image)
                image_urls.append(image_url)

        # Add data to Firestore
        if image_urls:
            firestore_data = {
                'userID': user_id,
                'plateID': plate_id,
                'comments': review_description,
                'name': user_name,
                'rating': selected_rating,
                'rentalID': rental_id,
                'reviewDate': SERVER_TIMESTAMP,
                'images': image_urls 
            }
        else:
            firestore_data = {
                'userID': user_id,
                'plateID': plate_id,
                'comments': review_description,
                'name': user_name,
                'rating': selected_rating,
                'rentalID': rental_id,
                'reviewDate': SERVER_TIMESTAMP,
            }

        crud.add('reviews', data=firestore_data, document_id=document_id)

        return "Images uploaded successfully"
    
    except Exception as e:
            return jsonify({'error': str(e)})

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
        color = request.form['color']

        # Check if car_model exists in CarInformation
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInformation WHERE car_model = %s", (car_model,))
        existing_car = cursor.fetchone()

        if existing_car:
            # Car model exists in CarInformation, insert into CarInventory
            car_inventory_query = """
                INSERT INTO CarInventory (license_plate, car_model, color)
                VALUES (%s, %s, %s)
            """
            car_inventory_data = (license_plate, car_model, color) 

            cursor.execute(car_inventory_query, car_inventory_data)
            mysql.get_db().commit()

        else:
            # Car model doesn't exist in CarInformation, insert into both tables
            car_info_query = """
                INSERT INTO CarInformation (car_model, car_make, engine_size, transmission_type, body_type, daily_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            car_info_data = (car_model, car_make, engine_size, transmission_type, body_type, price)

            car_inventory_query = """
                INSERT INTO CarInventory (license_plate, car_model, color)
                VALUES (%s, %s, %s)
            """
            car_inventory_data = (license_plate, car_model, color)

            cursor.execute(car_info_query, car_info_data)
            cursor.execute(car_inventory_query, car_inventory_data)
            mysql.get_db.commit()

        # Redirect to the same page after successful form submission
        return redirect(url_for('add_listing'))

    return render_template('create_listings.html', message='You have successfully listed a car!')

def update_car_inventory(license_plate, car_make, car_model, body_type, engine_size, transmission_type, daily_rate):
    try:
        cursor = mysql.get_db().cursor()

        # Update the CarInventory table based on the provided information
        update_inventory_query = """
            UPDATE CarInventory
            SET car_model = %s
            WHERE license_plate = %s
        """
        cursor.execute(update_inventory_query, (car_model, license_plate))

        # Update the CarInformation table based on the provided information
        update_information_query = """
            UPDATE CarInformation
            SET
                car_make = %s,
                car_model = %s,
                body_type = %s,
                engine_size = %s,
                transmission_type = %s,
                daily_rate = %s
            WHERE car_model = %s
        """
        cursor.execute(update_information_query, (car_make, car_model, body_type, engine_size, transmission_type, daily_rate, car_model))

        mysql.get_db().commit()
        cursor.close()

    except Exception as e:
        # Rollback the changes in case of an error
        mysql.get_db().rollback()
        raise e

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():

    page = request.args.get('page', 1, type=int)
    per_page = 15

    if request.method == 'GET':
        cursor = mysql.get_db().cursor()
        cursor.execute("""
                SELECT cinv.license_plate, ci.car_make, ci.car_model, ci.body_type, ci.engine_size, ci.transmission_type, ci.daily_rate
                FROM CarInformation ci
                INNER JOIN CarInventory cinv ON ci.car_model = cinv.car_model
                ORDER BY cinv.license_plate ASC
            """)
        data = cursor.fetchall()
        cursor.close()

        pagination = Pagination(page=page, per_page=per_page, total=len(data), record_name='data')
        paginated_data = data[(page-1)*per_page:page*per_page]


        return render_template('admin_dashboard.html', data=paginated_data, pagination=pagination)
    elif request.method == 'POST':
        try:
            # Check if the request is for deleting rows
            if request.json and 'rows' in request.json:
                # Get the selected rows from the request
                selected_rows = request.json.get('rows')

                # Delete selected rows from the database
                delete_car_inventory(selected_rows)

                return jsonify({'message': 'Rows deleted successfully'})
            
            # Check if the request is for updating a single row
            elif request.json and 'license_plate' in request.json:
                # Get the values for updating the row
                license_plate = request.json.get('license_plate')
                car_make = request.json.get('car_make')
                car_model = request.json.get('car_model')
                body_type = request.json.get('body_type')
                engine_size = request.json.get('engine_size')
                transmission_type = request.json.get('transmission_type')
                daily_rate = request.json.get('daily_rate')

                # Update the row in the database
                update_car_inventory(license_plate, car_make, car_model, body_type, engine_size, transmission_type, daily_rate)

                return jsonify({'message': 'Row updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)})
    
    return render_template('admin_dashboard.html',  data=data, pagination=pagination)


def fetch_car_inventory():
    # Fetch data from the CarInventory table
    with mysql.get_db.cursor() as cursor:
        cursor.execute("SELECT * FROM CarInventory")
        data = cursor.fetchall()

    # Paginate the data
    pagination = Pagination(page=page, per_page=per_page, total=len(data), record_name='data')
    paginated_data = data[(page-1)*per_page:page*per_page]

    return render_template('admin_dashboard.html', data=paginated_data, pagination=pagination)

def delete_car_inventory(selected_rows):
    with mysql.get_db().cursor() as cursor:
        for license_plate in selected_rows:
            cursor.execute("DELETE FROM CarInventory WHERE license_plate = %s", (license_plate,))
    mysql.get_db().commit()


@app.route('/admin_dashboard/manage_users', methods=['GET', 'POST'])
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
        abort(403) 

def fetch_user_accounts():
    with mysql.get_db().cursor() as cursor:
            cursor.execute("SELECT 'user_id', `name`, `age`, `phone_no`, `email` FROM UserAccounts")
            data = cursor.fetchall()
    return data

def delete_selected_users(selected_users):
    with mysql.get_db().cursor() as cursor:
        for userid in selected_users:
            cursor.execute("DELETE FROM UserAccounts WHERE user_id = %s", (userid,))
    mysql.get_db().commit()
    
    
@app.route('/admin_metrics', methods=['GET'])
def admin_metrics():
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT CONCAT(YEAR(start_date), '-', LPAD(MONTH(start_date), 2, '0')) AS month, SUM(total_amount) AS monthly_sales FROM Rentals GROUP BY month")
        monthly_sales = cursor.fetchall()
        
        cursor.execute("SELECT CONCAT(YEAR(start_date), '-', LPAD(MONTH(start_date), 2, '0')) AS month, COUNT(rental_id) AS monthly_count FROM Rentals GROUP BY month")
        monthly_count = cursor.fetchall()
        
        cursor.execute("SELECT SUM(total_amount) as yearly_sales, YEAR(start_date) as start_month from Rentals GROUP BY YEAR(start_date)")
        yearly_sales = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(rental_id) as yearly_count, YEAR(start_date) as start_month from Rentals GROUP BY YEAR(start_date)")
        yearly_count = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(license_plate) as car_count FROM CarInventory")
        car_count = cursor.fetchone()
        car_count = car_count[0]
        
        cursor.execute("SELECT * FROM CarInventory WHERE license_plate = (SELECT license_plate FROM Rentals GROUP BY license_plate ORDER BY COUNT(*) DESC LIMIT 1)")
        top_rented = cursor.fetchone()
        
        cursor.close()
        
        return render_template('admin_metrics.html', monthly_sales=monthly_sales, monthly_count=monthly_count, yearly_sales=yearly_sales, yearly_count=yearly_count, car_count=car_count, top_rented=top_rented)

    except Exception as e:
        return jsonify({'error': str(e)})
    
    

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
