from flask import Flask, render_template, jsonify
from firebase import Firebase
from flaskext.mysql import MySQL
import uuid

app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Initialize MySQL
mysql = MySQL()

# MySQL configuration
app.config['MYSQL_DATABASE_HOST'] = '35.212.183.7'
app.config['MYSQL_DATABASE_USER'] = 'samuel'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dbpassword'
app.config['MYSQL_DATABASE_DB'] = 'inf2003'

mysql.init_app(app)


@app.route('/CarList')
def select_all_from_table():
    try:
        cursor = mysql.get_db().cursor()
        cursor.execute("SELECT CarMake, CarModel FROM CarInventory")
        data = cursor.fetchall()
        cursor.close()
        return render_template('cars.html', data=data)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)