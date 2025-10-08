from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.userModels import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

@app.route('/') # Homepage route
def homepage():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('homepage.html', logged_in=logged_in, **user_data)

@app.route('/register') # Registration page route
def register_page():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('registration.html', logged_in=logged_in, **user_data)

@app.route('/login') # Login page route
def login_page():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('login.html', logged_in=logged_in, **user_data)

@app.route("/contact") # Contact page route     
def contact_page():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('contact.html', logged_in=logged_in, **user_data)




@app.route("/registerRoute", methods=['POST']) # 
def register():
    # Validate input data
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()
    
    # Server-side validation
    errors = []
    
    if len(first_name) < 2:
        errors.append("First name must be at least 2 characters")
    
    if len(last_name) < 2:
        errors.append("Last name must be at least 2 characters")
    
    if not email or '@' not in email:
        errors.append("Please enter a valid email address")
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    if len(phone) < 10:
        errors.append("Please enter a valid phone number")
    
    # Check if email already exists
    existing_user = User.getUserByEmail({'email': email})
    if existing_user:
        errors.append("An account with this email already exists. Please try logging in instead.")
    
    if errors:
        for error in errors:
            flash(error)
        return redirect("/register")
    
    pw_hash = bcrypt.generate_password_hash(password)

    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': pw_hash,
        'phone': phone,
    }
    
    try:
        id = User.register(data)
        session['user_id'] = id
        print(f"New user created with ID: {id}")
        return redirect(url_for('success'))
    except Exception as e:
        flash("Registration failed. Please try again.")
        print(f"Registration error: {e}")
        return redirect("/register")


@app.route('/loginRoute', methods=['POST']) # Login route
def login():
    data = {
        'email': request.form['email']
    }
    print(data)
    userDB = User.getUserByEmail(data)
    if not userDB:
        flash("Invalid email or password. Please check your credentials and try again.")
        print("email is wrong")
        return redirect("/login")
    if not bcrypt.check_password_hash(userDB.password, request.form["password"]):
        flash("Invalid email or password. Please check your credentials and try again.")
        print("Password is wrong")
        return redirect("/login")
    session['user_id'] = userDB.user_id
    return redirect(url_for('success'))


@app.route('/success') # Success page route
def success():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('eventList.html', logged_in=logged_in, **user_data)

@app.route('/navComponent')
def navComponent():
    logged_in = "user_id" in session
    user_data = {}
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id
            }
    return render_template('navbar.html', logged_in=logged_in, **user_data)

@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect("/")

@app.route('/profile') # Profile page route
def profile_page():
    logged_in = "user_id" in session
    if not logged_in:
        flash("Please log in to access your profile")
        return redirect("/login")
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    if not user:
        session.clear()
        return redirect("/login")
    
    user_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'user_id': user.user_id
    }
    return render_template('profile.html', logged_in=logged_in, **user_data)

@app.route('/settings') # Settings page route
def settings_page():
    logged_in = "user_id" in session
    if not logged_in:
        flash("Please log in to access settings")
        return redirect("/login")
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    if not user:
        session.clear()
        return redirect("/login")
    
    user_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'user_id': user.user_id
    }
    return render_template('settings.html', logged_in=logged_in, **user_data)

@app.route('/update_profile', methods=['POST']) # Update profile route
def update_profile():
    logged_in = "user_id" in session
    if not logged_in:
        flash("Please log in to update your profile")
        return redirect("/login")
    
    user_id = session["user_id"]
    data = {
        'user_id': user_id,
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'phone': request.form['phone']
    }
    
    # Update user data
    success = User.updateProfile(data)
    if success:
        flash("Profile updated successfully!", "success")
    else:
        flash("Failed to update profile. Please try again.", "error")
    
    return redirect("/settings")

@app.route('/change_password', methods=['POST']) # Change password route
def change_password():
    logged_in = "user_id" in session
    if not logged_in:
        flash("Please log in to change your password")
        return redirect("/login")
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    
    if not user:
        session.clear()
        return redirect("/login")
    
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # Verify current password
    if not bcrypt.check_password_hash(user.password, current_password):
        flash("Current password is incorrect", "error")
        return redirect("/settings")
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect("/settings")
    
    # Hash new password and update
    pw_hash = bcrypt.generate_password_hash(new_password)
    data = {
        'user_id': user_id,
        'password': pw_hash
    }
    
    success = User.updatePassword(data)
    if success:
        flash("Password updated successfully!", "success")
    else:
        flash("Failed to update password. Please try again.", "error")
    
    return redirect("/settings")
        
        
    