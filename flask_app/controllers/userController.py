from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.userModels import User
from flask_bcrypt import Bcrypt

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
    bcrypt = Bcrypt(app)
    pw_hash = bcrypt.generate_password_hash(request.form['password'])

    data = {
         
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': pw_hash,
        'phone': request.form['phone'],
        'username': request.form['username']
        
    }
    User.register(data)
    return redirect('/')