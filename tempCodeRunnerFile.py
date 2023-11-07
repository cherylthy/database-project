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
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()

            # Account doesn't exist, and the form data is valid, so insert the new account into the UserAccounts table
            cursor.execute('INSERT INTO UserAccounts VALUES (NULL, %s, %s, %s, %s, %s, NULL)', (password, name, age, phoneno, email))
            mysql.get_db().commit()
            msg = 'You have successfully registered!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)