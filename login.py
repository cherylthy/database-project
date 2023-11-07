from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from firebase import Firebase
from flaskext.mysql import MySQL
import uuid
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# MySQL configuration
app.config['MYSQL_DATABASE_HOST'] = '35.212.183.7'
app.config['MYSQL_DATABASE_USER'] = 'samuel'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dbpassword'
app.config['MYSQL_DATABASE_DB'] = 'inf2003'

# Initialize MySQL
mysql = MySQL(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'Email' in request.form and 'Password' in request.form:
        # Create variables for easy access
        email = request.form['Email']
        password = request.form['Password']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        #cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM UserAccounts WHERE Email = %s AND Password = %s', (email, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['UserID'] = account[0]
            session['Email'] = account[1]
            # Redirect to home page
            return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)