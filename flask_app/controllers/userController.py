from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.userModels import User

@app.route('/') # Homepage route
def homepage():
    return render_template('homepage.html')

@app.route('/register') # Registration page route
def register_page():
    return render_template('registration.html')

@app.route('/login') # Login page route
def login_page():
    return render_template('login.html')
@app.route("/registerRoute", methods=['POST']) # 
def register():
     data = {
        'fn': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': request.form['password'],
        'phone': request.form['phone'],
        'username': request.form['username']
        
    }
     User.register(data)
     return redirect('/')