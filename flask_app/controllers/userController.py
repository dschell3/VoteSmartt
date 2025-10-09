from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template
from flask_app import app
from flask_app.models.userModels import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# ================================
# HELPER FUNCTIONS
# ================================

def get_user_session_data():
    """Helper function to get user session data for templates"""
    logged_in = "user_id" in session
    user_data = {'logged_in': logged_in}
    
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id,
                'created_at': user.created_at
            })
    
    return user_data

def get_user_voting_stats(user_id):
    """Get voting statistics for dashboard (placeholder data)"""
    # TODO: Replace with actual database queries when voting system is implemented
    return {
        'total_votes': 'N/A',  # Will be replaced with actual count
        'participation_rate': 'N/A',  # Will be calculated from events participated / total events
        'events_participated': 'N/A',  # Count of events user voted in
        'last_vote_date': 'N/A'  # Date of most recent vote
    }

def get_recent_votes(user_id, limit=3):
    """Get recent voting activity (placeholder data)"""
    # TODO: Replace with actual database queries when voting system is implemented
    return []  # Will return list of recent votes

def get_upcoming_elections(limit=10):
    """Get upcoming elections for voting guides (placeholder data)"""
    # TODO: Replace with actual database queries when event system is expanded
    return []  # Will return list of upcoming elections

def require_login(redirect_to="/login"):
    """Helper function to check if user is logged in"""
    if "user_id" not in session:
        flash("Please log in to access this page")
        return redirect_to
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    if not user:
        session.clear()
        flash("Session expired. Please log in again.")
        return redirect_to
    
    return None  # No redirect needed

# ================================
# PUBLIC PAGES (No login required)
# ================================

@app.route('/') # Homepage route
def homepage():
    user_data = get_user_session_data()
    return render_template('homepage.html', **user_data)

@app.route('/register') # Registration page route
def register_page():
    user_data = get_user_session_data()
    user_data['page_type'] = 'register'
    return render_template('auth.html', **user_data)

@app.route('/login') # Login page route
def login_page():
    user_data = get_user_session_data()
    user_data['page_type'] = 'login'
    return render_template('auth.html', **user_data)

@app.route("/contact") # Contact page route     
def contact_page():
    user_data = get_user_session_data()
    return render_template('contact.html', **user_data)

# Navbar component route - DEPRECATED: Now using unified base.html template
# @app.route('/navComponent') # Navbar component route
# def navComponent():
#     user_data = get_user_session_data()
#     return render_template('navbar.html', **user_data)

# ================================
# AUTHENTICATION ROUTES
# ================================

@app.route("/registerRoute", methods=['POST']) # Registration handler
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
    
    # Create new user
    pw_hash = bcrypt.generate_password_hash(password)
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': pw_hash,
        'phone': phone,
    }
    
    try:
        user_id = User.register(data)
        session['user_id'] = user_id
        print(f"New user created with ID: {user_id}")
        return redirect(url_for('success'))
    except Exception as e:
        flash("Registration failed. Please try again.")
        print(f"Registration error: {e}")
        return redirect("/register")

@app.route('/loginRoute', methods=['POST']) # Login handler
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash("Please enter both email and password")
        return redirect("/login")
    
    # Check user credentials
    user = User.getUserByEmail({'email': email})
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash("Invalid email or password. Please check your credentials and try again.")
        return redirect("/login")
    
    # Login successful
    session['user_id'] = user.user_id
    return redirect(url_for('success'))

@app.route("/logout", methods=['POST']) # Logout handler
def logout():
    session.clear()
    return redirect("/")

# ================================
# PROTECTED PAGES (Login required)
# ================================

@app.route('/success') # Dashboard/Success page
def success():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_data = get_user_session_data()
    return render_template('eventList.html', **user_data)

@app.route('/profile') # Profile page
def profile_page():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_data = get_user_session_data()
    user_id = session.get("user_id")
    
    # Add voting dashboard data
    user_data.update({
        'user_stats': get_user_voting_stats(user_id),
        'recent_votes': get_recent_votes(user_id),
        'upcoming_elections': get_upcoming_elections()
    })
    
    return render_template('profile.html', **user_data)

@app.route('/settings') # Settings page (unified with profile)
def settings_page():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_data = get_user_session_data()
    # Use unified profile template for both profile and settings
    return render_template('profile.html', **user_data)

# ================================
# PROFILE MANAGEMENT ROUTES
# ================================

@app.route('/update_profile', methods=['POST']) # Update profile handler
def update_profile():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_id = session["user_id"]
    data = {
        'user_id': user_id,
        'first_name': request.form.get('first_name', '').strip(),
        'last_name': request.form.get('last_name', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'phone': request.form.get('phone', '').strip()
    }
    
    # Update user data
    try:
        success = User.updateProfile(data)
        if success:
            flash("Profile updated successfully!", "success")
        else:
            flash("Failed to update profile. Please try again.", "error")
    except Exception as e:
        flash("Failed to update profile. Please try again.", "error")
        print(f"Profile update error: {e}")
    
    return redirect("/settings")

@app.route('/change_password', methods=['POST']) # Change password handler
def change_password():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required", "error")
        return redirect("/settings")
    
    # Verify current password
    if not bcrypt.check_password_hash(user.password, current_password):
        flash("Current password is incorrect", "error")
        return redirect("/settings")
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect("/settings")
    
    # Validate new password strength
    if len(new_password) < 8:
        flash("New password must be at least 8 characters", "error")
        return redirect("/settings")
    
    # Update password
    try:
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
    except Exception as e:
        flash("Failed to update password. Please try again.", "error")
        print(f"Password update error: {e}")
    
    return redirect("/settings")