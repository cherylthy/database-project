from flask import Flask, render_template, request, jsonify
from firebase import Firebase
from flaskext.mysql import MySQL
import math

app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Initialize MySQL
mysql = MySQL()

# MySQL configuration
app.config['MYSQL_DATABASE_HOST'] = '35.212.183.7'
app.config['MYSQL_DATABASE_USER'] = 'common'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dbpassword'
app.config['MYSQL_DATABASE_DB'] = 'inf2003'

mysql.init_app(app)

# Function to get the total number of rows in the table
def get_total_rows():
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT COUNT(*) FROM CarInventory")
        total_rows = cursor.fetchone()[0]
        cursor.close()
        return total_rows
    except Exception as e:
        return jsonify({'error': str(e)})

# Function to calculate the total number of pages
def calculate_total_pages(total_rows, per_page):
    return int(math.ceil(total_rows / per_page))

@app.route('/CarList')
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
        query = "SELECT car_make, car_model, daily_rate FROM CarInventory"

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

        return render_template('cars.html', data=data, current_page=page, total_pages=total_pages, car_makes=car_makes)

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
