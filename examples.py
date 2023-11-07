#This file is for examples on how to select data from firebase and mysql, DO NOT RUN

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from firebase import Firebase
from flaskext.mysql import MySQL
import uuid
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

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

# Generate random document id
def generate_document_id():
    # Generate a random unique identifier
    unique_id = str(uuid.uuid4())
    return f"reviews-{unique_id}"

# add users for firestore (firebase db)
@app.route('/')
def display_reviews():
    result = crud.get("reviews")
    document_id = generate_document_id()
    
    # Add a document to a collection with a specific ID
    data = {"userID": 5432, "carID": 3333, "comments": "This car sucks", "ratings":4.5}
    crud.add('reviews', data=data, document_id=document_id)
    
    return render_template('test.html', reviews=result)

# select data from mysql
@app.route('/')
def select_all_from_table():
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT * FROM CarInventory")
        data = cursor.fetchall()
        cursor.close()
        return render_template('sql_test.html', data=data)
    
    except Exception as e:
        return jsonify({'error': str(e)})