from flask import Flask, jsonify
from flask_mysqldb import MySQL
import sshtunnel

app = Flask(__name__)

# SSH tunnel connection details
ssh_host = '35.212.183.7'
ssh_port = 22
ssh_user = 'dev1'
ssh_password = 'inf2003@DB'

# MySQL server details
mysql_host = 'localhost'
mysql_port = 3306  # Use the correct MySQL port here
mysql_user = 'dev1'
mysql_password = 'inf2003@DB'
mysql_db = 'inf2003'

# Create the SSH tunnel
with sshtunnel.SSHTunnelForwarder(
    (ssh_host, ssh_port),
    ssh_username=ssh_user,
    ssh_password=ssh_password,
    remote_bind_address=('127.0.0.1', mysql_port)
) as tunnel:
    if tunnel.is_active:
        print("SSH tunnel successfully created.")
        
        # Configure MySQL connection to use the SSH tunnel
        app.config['MYSQL_HOST'] = 'localhost'  # Use 'localhost' when using an SSH tunnel
        app.config['MYSQL_PORT'] = 3306
        app.config['MYSQL_USER'] = mysql_user
        app.config['MYSQL_PASSWORD'] = mysql_password
        app.config['MYSQL_DB'] = mysql_db

        mysql = MySQL(app)
    else:
        print("SSH tunnel creation failed.")
        raise Exception("SSH tunnel creation failed")

    @app.route('/')
    def select_all_from_table():
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM CarInventory")
            data = cursor.fetchall()
            cursor.close()
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
