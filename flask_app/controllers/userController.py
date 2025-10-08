from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.userModels import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

@app.route('/') # Homepage route
def homepage():
    return render_template('homepage.html')

@app.route('/register') # Registration page route
def register_page():
    return render_template('registration.html')

@app.route('/login') # Login page route
def login_page():
    return render_template('login.html')

@app.route("/contact") # Contact page route     
def contact_page():
    return render_template('contact.html')


@app.route('/contactRoute', methods=['POST'])
def contact_route():
    # Basic handling for contact form — flash a confirmation and redirect back to the contact page.
    first = request.form.get('first_name', '')
    email = request.form.get('email', '')
    message = request.form.get('message', '')
    # Here you would normally store the message or send an email. We'll flash a friendly message.
    flash('Thanks for your message — we\'ll get back to you at {}'.format(email))
    return redirect(url_for('contact_page'))

@app.route("/registerRoute", methods=['POST']) # 
def register():
    pw_hash = bcrypt.generate_password_hash(request.form['password'])

    data = {
         
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': pw_hash,
        'phone': request.form['phone'],
        
        
    }
    User.register(data)
    return redirect(url_for('success'))


@app.route('/loginRoute', methods=['POST']) # Login route
def login():
    data = {
        'email': request.form['email']
    }
    print(data)
    userDB = User.getUserByEmail(data)
    if not userDB:
        flash("Invalid email/password")
        print("email is wrong")
        return redirect("/login")
    if not bcrypt.check_password_hash(userDB.password, request.form["password"]):
        flash("Invalid Email/Password")
        print("Password is wrong")
        return redirect("/login")
    session['user_id'] = userDB.user_id
    return redirect(url_for('success'))

@app.route('/success') # Success page route
def success():
    loggedIn = "user_id" in session
    if loggedIn:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
    return render_template('eventList.html', user = user)

@app.route('/navComponent')
def navComponent():
    loggedIn = "user_id" in session
    if loggedIn:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        firstInitial = user.first_name[0]
        lastInitial = user.last_name[0]
    return render_template()

@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect("/")
        
        
    