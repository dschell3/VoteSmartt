'''
==============================================================================
User Controller - Handles HTTP routes for user management and authentication
==============================================================================

This module provides Flask route handlers for user registration, authentication,
profile management, password reset flows, and public informational pages within
the VoteSmartt system.

Routes (organized by category):

    ERROR PAGES:
        - GET /unauthorized         : Access denied page

    PUBLIC PAGES (No login required):
        - GET /                     : Homepage
        - GET /about                : Team member information (JSON-driven)
        - GET /credits              : Team credits/contributions (JSON-driven)
        - GET /register             : Registration form page
        - GET /login                : Login form page
        - GET /contact              : Contact form page
        - POST /contactRoute        : Contact form submission handler

    AUTHENTICATION ROUTES:
        - POST /registerRoute       : Process new user registration
        - POST /loginRoute          : Process user login
        - POST /logout              : Clear session and logout

    PASSWORD RESET ROUTES:
        - GET /forgot_password      : Password reset request page
        - POST /forgotPassword      : Process reset request, send email
        - POST /forgotRoute         : Alias for /forgotPassword
        - GET /reset_password       : Token-based password reset page
        - POST /resetPassword       : Process password reset with token

    PROTECTED PAGES (Login required):
        - GET /profile              : User profile and voting dashboard

    PROFILE MANAGEMENT ROUTES:
        - POST /update_profile      : Update user profile information
        - POST /change_password     : Change user password (requires current)

Model Dependencies:
    - User: Registration, authentication, profile updates, password reset
    - Events: Retrieve upcoming elections for dashboard
    - Vote: Retrieve user voting statistics and history

Security Features:
    - Passwords hashed with bcrypt before storage
    - Password reset tokens with expiration
    - Session-based authentication
    - Generic messages to prevent email enumeration attacks
'''

from flask import request, flash, url_for, redirect, session, render_template
from flask_app import app
from flask_app.models.eventsModels import Events
from flask_app.models.userModels import User
from flask_bcrypt import Bcrypt
from flask_app.utils.helpers import require_login, get_user_session_data, get_current_user
from flask_app.utils.validators import format_phone, validate_all_registration_fields, validate_email, validate_password, validate_phone, validate_name
from flask_app.models.voteModels import Vote
from flask import current_app
from flask_app.utils.mailer import send_contact_email
import json, os
from datetime import datetime

# Initialize bcrypt for pw hashing
bcrypt = Bcrypt(app)

# =============================================================================
# HELPER FUNCTIONS - Internal utilities for controller routes
# =============================================================================

def get_user_voting_stats(user_id):
    """
    Get voting statistics for dashboard display.
    
    Args:
        user_id (int): ID of the user to get stats for
    Returns:
        dict: Statistics containing total_votes, participation_rate,
              events_participated, and last_vote_date
    """
    try:
        return Vote.getStatsForUser({'user_id': user_id})
    except Exception as e:
        print(f"Error getting user voting stats: {e}")
        # Return safe defaults on error
        return {
            'total_votes': 0,
            'participation_rate': 0.0,
            'events_participated': 0,
            'last_vote_date': 'N/A'
        }

def get_recent_votes(user_id, limit=3):
    """
    Retrieve user's recent voting activity for dashboard display.
    
    Args:
        user_id (int): ID of the user
        limit (int): Maximum number of recent votes to retrieve (default: 3)
    Returns:
        list: Recent vote records with event information 
    """
    return Vote.getRecentForUser({'user_id': user_id, 'limit': limit})

def get_upcoming_elections(limit=10):
    """
    Retrieve upcoming elections for voting guides display.
    
    Args:
        limit (int): Maximum number of elections to retrieve (default: 10)
    Returns:
        list: Upcoming event records
    """
    return Events.getUpcoming(limit=limit)

def send_email(to_address, subject, body):
    """
    Send an email to specified address using the mail helper.
    
    Wraps the mailer utility so controller routes can call send_email directly
    without importing the mailer module.
    
    Args:
        to_address (str): Recipient email address
        subject (str): Email subject line
        body (str): Email body content
    """
    recipients = [to_address]
    send_contact_email(subject, body, recipients)

# Base path for JSON data files (about.json, credits.json)
_DATA_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'data')

def _load_json(filename, fallback):
    """
    Load a JSON file from static/data directory with fallback on failure.
    This keeps page rendering robust and avoids 500 errors when JSON
    files are missing, corrupted, or have invalid syntax.
    
    Args:
        filename (str): Name of JSON file to load (e.g., 'about.json')
        fallback (dict): Default data to return on any failure
    Returns:
        dict: Parsed JSON data or fallback on error
    """
    path = os.path.join(_DATA_BASE_PATH, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ABOUT/CREDITS] Failed loading {filename}: {e}")
        return fallback


# =============================================================================
# ERROR & UNAUTHORIZED PAGES
# =============================================================================

@app.route('/unauthorized')
def unauthorized_page():
    """
    Display access denied page for unauthorized access attempts.
    """
    user_data = get_user_session_data()
    return render_template('unauthorized.html', **user_data)

# =============================================================================
# PUBLIC PAGES (No login required)
# =============================================================================

@app.route('/') # Homepage route
def homepage():
    """
    Display the application homepage.
    """
    user_data = get_user_session_data()
    return render_template('homepage.html', **user_data)

# =============================================================================
# PUBLIC PAGE ROUTES - ABOUT & CREDITS 
# =============================================================================

@app.route('/about')
def about_page():
    """
    Display the About Us page with team member information.
    """
    user_data = get_user_session_data()
    data = _load_json('about.json', { 'title': 'About Us', 'intro': 'Content coming soon.', 'members': [] })
    return render_template('about.html', data=data, **user_data)

@app.route('/credits')
def credits_page():
    """
    Display the Credits page with team contributions.
    """
    user_data = get_user_session_data()
    # Load credits data
    data = _load_json('credits.json', { 'title': 'CREDITS', 'people': [] })
    # Also load about.json so we can show avatars next to credit entries when available
    about_data = _load_json('about.json', { 'title': 'About Us', 'intro': '', 'members': [] })
    # Build a simple name -> avatar_url map for quick lookup in the template
    about_map = {}
    try:
        for m in about_data.get('members', []):
            name = m.get('name')
            avatar = m.get('avatar_url')
            if name and avatar:
                about_map[name] = avatar
    except Exception:
        about_map = {}

    return render_template('credits.html', data=data, about_map=about_map, **user_data)

# =============================================================================
# PUBLIC PAGE ROUTES - Registration, Login, Contact pages
# =============================================================================

@app.route('/register') 
def register_page():
    """
    Display the user registration page.
    """
    user_data = get_user_session_data()
    user_data['page_type'] = 'register'
    return render_template('auth.html', **user_data)

@app.route('/login')
def login_page():
    """
    Display the user login page.
    """
    user_data = get_user_session_data()
    user_data['page_type'] = 'login'
    return render_template('auth.html', **user_data)

@app.route("/contact")    
def contact_page():
    """
    Display the contact form page.
    """
    user_data = get_user_session_data()
    return render_template('contact.html', **user_data)


@app.route('/contactRoute', methods=['POST'])
def contact_route():
    """
    Handle contact form submissions and send email to site admin.
    
    Process:
        1. Collect form data (name, email, phone, message)
        2. Validate required fields (name, email, message)
        3. Compose email
        4. Check email configuration exists
        5. Send email via mail helper

    Redirects:
        /contact with success or error flash message
    """
    """Handle contact form submissions and send an email to site admin."""
    # 1. Collect form data
    name = request.form.get('first_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message', '').strip()

    # 2. Basic validation
    if not name or not email or not message:
        flash('Please provide your name, email, and message.', 'error')
        return redirect('/contact')

    # 3. Compose subject & body
    subject = f"New contact form submission from {name}"
    body_lines = [
        f"Name: {name}",
        f"Email: {email}",
        f"Phone: {phone}",
        "",
        "Message:",
        message,
    ]
    body = "\n".join(body_lines)

    # 4. Check email configuration
    recipient = current_app.config.get('MAIL_USERNAME')
    if not recipient:
        # If no recipient configured, fail gracefully
        flash('Mailing is not configured on this server. Please contact support another way.', 'error')
        return redirect('/contact')

    # 5. Send email via mail helper
    try:
        send_email(recipient, subject, body)
        flash('Thanks — your message has been sent. We will reply shortly.', 'success')
    except Exception as e:
        print(f"Error sending contact email: {e}")
        flash('There was a problem sending your message. Please try again later.', 'error')

    return redirect('/contact')

# ================================
# AUTHENTICATION ROUTES
# ================================

@app.route("/registerRoute", methods=['POST']) 
def register():
    """Handle user registration with validation"""
    """
    Handle user registration with validation.
    
    Process:
        1. Get form data
        2. Validate all fields using centralized validators
        3. Check for existing email (prevent duplicates)
        4. Hash password with bcrypt
        5. Create user record in database
        6. Log user in automatically (set session)
    
    Redirects:
        - /register: On validation errors (with flash messages)
        - /eventList: On successful registration
    """
    # 1. Get form data
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()
    
    # 2. Validate all registration fields at once
    errors = validate_all_registration_fields(first_name, last_name, email, password, phone)

    # 3. Check if email already exists (custom validation)
    existing_user = User.getUserByEmail({'email': email})
    if existing_user:
        errors.append("An account with this email already exists. Please try logging in instead.")
    
    # If there are any errors, show them and redirect back
    if errors:
        for error in errors:
            flash(error)
        return redirect("/register")
    
    # Format phone number consistently
    formatted_phone = format_phone(phone)
    
    # 4. Hash pw with bcrypt
    pw_hash = bcrypt.generate_password_hash(password)
    
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': pw_hash,
        'phone': formatted_phone,  # Use formatted phone
    }
    
    # 5. Create new user record
    try:
        user_id = User.register(data)
        # 6. Log-In after registering
        session['user_id'] = user_id
        session['first_name'] = first_name
        print(f"New user created with ID: {user_id}")
        return redirect(url_for('eventList'))
    except Exception as e:
        flash("Registration failed. Please try again.")
        print(f"Registration error: {e}")
        return redirect("/register")


@app.route('/loginRoute', methods=['POST']) 
def login():
    """
    Handle user login authentication.
    
    Process:
        1. Extract and sanitize credentials
        2. Validate both fields are provided
        3. Look up user by email
        4. Verify password with bcrypt
        5. Set session variables on success

    Redirects:
        - /login: On validation failure or invalid credentials
        - /eventList: On successful login
    """
    # 1. Get login credentials
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    # 2. Validate both were provided
    if not email or not password:
        flash("Please enter both email and password")
        return redirect("/login")
    
    # 3. Check user credentials
    user = User.getUserByEmail({'email': email})
    
    # 4. Verify pw with bcrypt
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash("Invalid email or password. Please check your credentials and try again.")
        return redirect("/login")
    
    # 5. Login successful, set session variables
    session['user_id'] = user.user_id
    session['first_name'] = user.first_name
    return redirect(url_for('eventList'))


@app.route("/logout", methods=['POST']) 
def logout():
    """
    Handle user logout by clearing session.
    
    Redirects:
        / (homepage)
    """
    session.clear()
    return redirect("/")

# =============================================================================
# PASSWORD RESET ROUTES - Forgot password and reset flows
# =============================================================================

@app.route("/forgot_password", methods=['GET']) 
def forgot_password_page():
    """
    Display the password reset request page.
    """
    user_data = get_user_session_data()
    return render_template('forgot_password.html', **user_data)


@app.route("/forgotPassword", methods=['POST']) 
def forgot_password_request():
    """
    Process password reset request and send reset email.
    
    Process:
        1. Extract and validate email
        2. Check throttle (60 second cooldown per session)
        3. Create reset token (even if email doesn't exist - security)
        4. Build reset URL with token
        5. Attempt to send email (log fallback for dev viz)
        6. Show generic success message (prevents email enumeration)
  
    Security Notes:
        - Generic success message regardless of email existence
        - 60 second throttle prevents brute-force enumeration
        - Token is hashed before database storage
    
    Redirects:
        - /forgot_password: On throttle violation
        - /login: On success (with generic message)
    """
    # Get and validate email
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash("Please enter your email address", "error")
        return redirect("/forgot_password")

    # 2. Throttle: allow one request per 60 seconds per session
    now_ts = datetime.utcnow().timestamp()
    last_ts = session.get('forgot_last_ts')
    if last_ts and (now_ts - float(last_ts)) < 60:
        remaining = int(60 - (now_ts - float(last_ts))) or 1
        flash(f"Please wait {remaining} seconds before requesting another reset link.", "error")
        return redirect('/forgot_password')

    # 3. Create token (return generic success even if email does not exist to avoid information leakage)
    _, raw_token = User.createPasswordResetToken(email)

    # Compose reset link with token
    try:
        # 4. Build reset URL
        reset_url = url_for('reset_password_page', token=raw_token, _external=True) if raw_token else None
        
        # Check mail configuration    
        mail_user = current_app.config.get('MAIL_USERNAME')
        mail_pass = current_app.config.get('MAIL_PASSWORD') or current_app.config.get('MAIL_PASSWORD')
        
        # 5. Only attempt to send if mail credentials appear configured
        if reset_url and mail_user and mail_pass:
            try:
                send_email(email, "Password Reset Request", f"Click the link below to reset your password:\n{reset_url}\n\nIf you did not request this, you can safely ignore this email.")
            except Exception as e:
                # TODO- Remove Fallback before turn-in: log link for developer visibility
                print(f"[DEV][PASSWORD RESET] Email send failed: {e}; reset link for {email}: {reset_url}")
        else:
            # Dev fallback when mail not configured
            if reset_url:
                # TODO- Remove Fallback before turn-in
                print(f"[DEV][PASSWORD RESET] Mail config missing; reset link for {email}: {reset_url}")
    except Exception as e:
        # Broad catch in case url_for/external building fails unexpectedly
        print(f"[DEV][PASSWORD RESET] Unexpected failure preparing reset email: {e}")

    # 6. Show success message
    flash("If an account with that email exists, a reset link has been sent.", "success")
    
    # Record throttle timestamp on success path as well (regardless of whether email exists)
    session['forgot_last_ts'] = now_ts
    return redirect("/login")

@app.route("/forgotRoute", methods=['POST'])
def forgot_password_request_alias():
    """
    Backward-compatible alias for /forgotPassword route.
    Delegates entirely to forgot_password_request()
    
    Note:
        Maintained for older templates/modals that may reference this endpoint
    """
    return forgot_password_request()


@app.route("/reset_password", methods=['GET']) 
def reset_password_page():
    """
    Display the password reset form (token-based).

    Redirects:
        /forgot_password: If token is invalid or expired
    """
    # Get token
    token = request.args.get('token', '').strip()
    
    # Validate token
    info = User.verifyPasswordResetToken(token)
    if not token or not info:
        flash("The reset link is invalid or has expired.", "error")
        return redirect("/forgot_password")

    return render_template("reset_password.html", token=token)
    

@app.route("/resetPassword", methods=['POST']) 
def reset_password_submit():
    """
    Process password reset with token validation.
    
    Process:
        1. Extract form data (token, passwords)
        2. Validate all fields provided
        3. Verify passwords match
        4. Validate password strength
        5. Re-verify token (prevent race conditions)
        6. Check new password differs from current
        7. Hash and update password
        8. Consume (invalidate) token

    Redirects:
        - referrer or /: On validation errors
        - /forgot_password: On invalid/expired token
        - /: On success (login page)
    """
    # 1. Get form data
    token = request.form.get('token', '').strip()
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    # 2. Validate all fields
    if not token or not new_password or not confirm_password:
        flash("All fields are required", "error")
        return redirect(request.referrer or '/')

    # 3. Verify passwords match
    if new_password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect(request.referrer or '/')

    # 4. Validate pw strength using centralized validator (detailed message)
    pw_error = validate_password(new_password)
    if pw_error:
        flash(pw_error, "error")
        return redirect(request.referrer or '/')

    # 5. Verify token again to prevent reuse and race conditions
    info = User.verifyPasswordResetToken(token)
    if not info:
        flash("The reset link is invalid or has expired.", "error")
        return redirect('/forgot_password')

    # 6. Disallow reusing current password
    try:
        if bcrypt.check_password_hash(info['password'], new_password):
            flash("New password cannot be the same as your current password.", "error")
            return redirect(request.referrer or '/')
    except Exception:
        pass

    # 7. Hash and update pw
    pw_hash = bcrypt.generate_password_hash(new_password)
    ok = User.updatePassword({'user_id': info['user_id'], 'password': pw_hash})
    if not ok:
        flash("Failed to update password. Please try again.", "error")
        return redirect('/forgot_password')

    # 8. Consume token
    User.consumePasswordResetToken(token)

    flash("Password successfully updated. Please log in.", "success")
    return redirect('/')


# =============================================================================
# PROTECTED PAGES (Login required)
# =============================================================================

@app.route('/profile') 
def profile_page():
    """
    Display user profile and voting dashboard.

    Redirects:
        Login page if not authenticated
    """
    # Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    # Get session data
    user_data = get_user_session_data()
    user_id = session.get("user_id")
    
    # Add voting dashboard data
    user_data.update({
        'user_stats': get_user_voting_stats(user_id),
        'recent_votes': get_recent_votes(user_id),
        'upcoming_elections': get_upcoming_elections()
    })
    
    return render_template('profile.html', **user_data)


# =============================================================================
# PROFILE MANAGEMENT ROUTES
# =============================================================================

@app.route('/update_profile', methods=['POST']) 
def update_profile():
    """
    Handle profile information updates.
    
    Redirects:
        /profile with success or error flash message
    """
    # Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    # Get current user
    user = get_current_user()

    # Get form data
    data = {
        'user_id': user.user_id,
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
    
    return redirect("/profile")

@app.route('/change_password', methods=['POST']) 
def change_password():
    """
    Handle password change for logged-in users.
    
    Process:
        1. Verify user is logged in
        2. Get fresh user object from database
        3. Extract password fields from form
        4. Validate all fields provided
        5. Verify current password is correct
        6. Verify new passwords match
        7. Validate new password strength
        8. Ensure new password differs from current
        9. Hash and update password
    
    Redirects:
        /profile with success or error flash message
    """
    # 1. Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    # 2. Get current user object
    user = get_current_user()
    user = User.getUserByID({"user_id": user.user_id})
    
    # 3. Get password fields from form
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # 4. Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required", "error")
        return redirect("/profile")
    
    # 5. Verify current password
    if not bcrypt.check_password_hash(user.password, current_password):
        flash("Current password is incorrect", "error")
        return redirect("/profile")
    
    # 6. Check if new passwords match
    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect("/profile")
    
    # 7. Validate new password strength (detailed message)
    pw_error = validate_password(new_password)
    if pw_error:
        flash(pw_error, "error")
        return redirect("/profile")

    # 8. Disallow using the same password
    if bcrypt.check_password_hash(user.password, new_password):
        flash("New password cannot be the same as your current password.", "error")
        return redirect("/profile")
    
    # 9. Hash and Update password
    try:
        pw_hash = bcrypt.generate_password_hash(new_password)
        data = {
            'user_id': user.user_id,
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
    
    return redirect("/profile")
