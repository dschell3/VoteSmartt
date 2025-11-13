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

bcrypt = Bcrypt(app)

# ================================
# HELPER FUNCTIONS
# ================================


def get_user_voting_stats(user_id):
    """Get voting statistics for dashboard (placeholder data)"""
    # TODO: Replace with actual database queries when voting system is implemented
    # Create a User model method to get these stats?
    return {
        'total_votes': 'N/A',  # Will be replaced with actual count
        'participation_rate': 'N/A',  # Will be calculated from events participated / total events
        'events_participated': 'N/A',  # Count of events user voted in
        'last_vote_date': 'N/A'  # Date of most recent vote
    }

# TODO - ASK JANG
# this just reimplements Vote.getRecentForUser w/ session data...should the session data remain
# in controllers like this? Basically yes, since models shouldn't depend on session state
# So have the controller extract session data and pass to model methods
def get_recent_votes(user_id, limit=3):
    """Get recent voting activity (placeholder data)"""
    return Vote.getRecentForUser({'user_id': user_id, 'limit': limit})

def get_upcoming_elections(limit=10):
    """Get upcoming elections for voting guides (placeholder data)"""
    return Events.getUpcoming(limit=limit)

def send_email(to_address, subject, body):
    """Send an email to `to_address` using the mail helper.

    This wraps the mail helper so controllers can call send_email(...) directly.
    """
    recipients = [to_address]
    send_contact_email(subject, body, recipients)

# ================================
# ERROR & UNAUTHORIZED PAGES
# ================================

@app.route('/unauthorized')
def unauthorized_page():
    user_data = get_user_session_data()
    return render_template('unauthorized.html', **user_data)

# ================================
# PUBLIC PAGES (No login required)
# ================================

@app.route('/') # Homepage route
def homepage():
    user_data = get_user_session_data()
    return render_template('homepage.html', **user_data)

# ================================
# ABOUT & CREDITS (Public, JSON-driven)
# ================================

_DATA_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'data')

def _load_json(filename, fallback):
    """Load a JSON file from static/data. On failure, return the fallback.
    This keeps page rendering robust and avoids 500s even when JSON is missing or invalid.
    """
    path = os.path.join(_DATA_BASE_PATH, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ABOUT/CREDITS] Failed loading {filename}: {e}")
        return fallback

@app.route('/about')
def about_page():
    user_data = get_user_session_data()
    data = _load_json('about.json', { 'title': 'About Us', 'intro': 'Content coming soon.', 'members': [] })
    return render_template('about.html', data=data, **user_data)

@app.route('/credits')
def credits_page():
    user_data = get_user_session_data()
    data = _load_json('credits.json', { 'title': 'CREDITS', 'people': [] })
    return render_template('credits.html', data=data, **user_data)

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


# Contact form submission handler
@app.route('/contactRoute', methods=['POST'])
def contact_route():
    """Handle contact form submissions and send an email to site admin."""
    # Collect form data
    name = request.form.get('first_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message', '').strip()

    # Basic validation
    if not name or not email or not message:
        flash('Please provide your name, email, and message.', 'error')
        return redirect('/contact')

    # Compose subject & body
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

    # Determine recipient (default to configured MAIL_USERNAME)
    recipient = current_app.config.get('MAIL_USERNAME')
    if not recipient:
        # If no recipient configured, fail gracefully
        flash('Mailing is not configured on this server. Please contact support another way.', 'error')
        return redirect('/contact')

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

@app.route("/registerRoute", methods=['POST']) # Registration handler
def register():
    """Handle user registration with validation"""
    # Get form data
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()
    
    # Validate using centralized validators
    errors = []
    
    # Validate first name
    error = validate_name(first_name, "First name")
    if error:
        errors.append(error)
    
    # Validate last name
    error = validate_name(last_name, "Last name")
    if error:
        errors.append(error)
    
    # Validate email
    error = validate_email(email)
    if error:
        errors.append(error)
    
    # Validate password
    error = validate_password(password)
    if error:
        errors.append(error)
    
    # Validate phone
    error = validate_phone(phone)
    if error:
        errors.append(error)
    
    # Check if email already exists (custom validation)
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
    
    # Create new user
    pw_hash = bcrypt.generate_password_hash(password)
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': pw_hash,
        'phone': formatted_phone,  # Use formatted phone
    }
    
    try:
        user_id = User.register(data)
        session['user_id'] = user_id
        session['first_name'] = first_name
        print(f"New user created with ID: {user_id}")
        return redirect(url_for('eventList'))
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
    session['first_name'] = user.first_name
    return redirect(url_for('eventList'))


@app.route("/logout", methods=['POST']) # Logout handler
def logout():
    session.clear()
    return redirect("/")


@app.route("/forgot_password", methods=['GET']) # Password reset request handler
def forgot_password_page():
    user_data = get_user_session_data()
    return render_template('forgot_password.html', **user_data)


@app.route("/forgotPassword", methods=['POST']) # Forgot password handler
def forgot_password_request():
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash("Please enter your email address", "error")
        return redirect("/forgot_password")

    # Throttle: allow one request per 60 seconds per session
    now_ts = datetime.utcnow().timestamp()
    last_ts = session.get('forgot_last_ts')
    if last_ts and (now_ts - float(last_ts)) < 60:
        remaining = int(60 - (now_ts - float(last_ts))) or 1
        flash(f"Please wait {remaining} seconds before requesting another reset link.", "error")
        return redirect('/forgot_password')

    # Create token (return generic success even if email does not exist to avoid information leakage)
    ok, raw_token = User.createPasswordResetToken(email)

    # Compose reset link with token
    try:
        reset_url = url_for('reset_password_page', token=raw_token, _external=True) if raw_token else None
        # Always print in debug mode to aid local testing, regardless of mail status
        if reset_url and current_app and getattr(current_app, 'debug', False):
            print(f"[DEV][PASSWORD RESET] Reset link generated for {email}: {reset_url}")
        mail_user = current_app.config.get('MAIL_USERNAME')
        mail_pass = current_app.config.get('MAIL_PASSWORD') or current_app.config.get('MAIL_PASSWORD')
        # Only attempt to send if mail credentials appear configured
        if reset_url and mail_user and mail_pass:
            try:
                send_email(email, "Password Reset Request", f"Click the link below to reset your password:\n{reset_url}\n\nIf you did not request this, you can safely ignore this email.")
            except Exception as e:
                # Fallback: log link for developer visibility
                print(f"[DEV][PASSWORD RESET] Email send failed: {e}; reset link for {email}: {reset_url}")
        else:
            # Dev fallback when mail not configured
            if reset_url:
                print(f"[DEV][PASSWORD RESET] Mail config missing; reset link for {email}: {reset_url}")
    except Exception as e:
        # Broad catch in case url_for/external building fails unexpectedly
        print(f"[DEV][PASSWORD RESET] Unexpected failure preparing reset email: {e}")

    flash("If an account with that email exists, a reset link has been sent.", "success")
    # record throttle timestamp on success path as well (regardless of whether email exists)
    session['forgot_last_ts'] = now_ts
    return redirect("/login")

# Backward-compatible alias for older templates/modals
@app.route("/forgotRoute", methods=['POST'])
def forgot_password_request_alias():
    return forgot_password_request()


@app.route("/reset_password", methods=['GET']) # Password reset page (token-based)
def reset_password_page():
    token = request.args.get('token', '').strip()
    info = User.verifyPasswordResetToken(token)
    if not token or not info:
        flash("The reset link is invalid or has expired.", "error")
        return redirect("/forgot_password")

    return render_template("reset_password.html", token=token)
    

@app.route("/resetPassword", methods=['POST']) # Password reset handler (token-based)
def reset_password_submit():
    token = request.form.get('token', '').strip()
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not token or not new_password or not confirm_password:
        flash("All fields are required", "error")
        return redirect(request.referrer or '/login')

    if new_password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect(request.referrer or '/login')

    # Validate strength using centralized validator (detailed message)
    pw_error = validate_password(new_password)
    if pw_error:
        flash(pw_error, "error")
        return redirect(request.referrer or '/login')

    # Verify token again to prevent reuse and race conditions
    info = User.verifyPasswordResetToken(token)
    if not info:
        flash("The reset link is invalid or has expired.", "error")
        return redirect('/forgot_password')

    # Disallow reusing current password
    try:
        if bcrypt.check_password_hash(info['password'], new_password):
            flash("New password cannot be the same as your current password.", "error")
            return redirect(request.referrer or '/login')
    except Exception:
        pass

    # Update password by user_id
    pw_hash = bcrypt.generate_password_hash(new_password)
    ok = User.updatePassword({'user_id': info['user_id'], 'password': pw_hash})
    if not ok:
        flash("Failed to update password. Please try again.", "error")
        return redirect('/forgot_password')

    # Consume token
    User.consumePasswordResetToken(token)

    flash("Password successfully updated. Please log in.", "success")
    return redirect('/login')


# ================================
# PROTECTED PAGES (Login required)
# ================================

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
    
    user = get_current_user()
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
    
    return redirect("/settings")

@app.route('/change_password', methods=['POST']) # Change password handler
def change_password():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user = get_current_user()
    user = User.getUserByID({"user_id": user.user_id})
    
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
    
    # Validate new password strength (detailed message)
    pw_error = validate_password(new_password)
    if pw_error:
        flash(pw_error, "error")
        return redirect("/settings")

    # Disallow using the same password
    if bcrypt.check_password_hash(user.password, new_password):
        flash("New password cannot be the same as your current password.", "error")
        return redirect("/settings")
    
    # Update password
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
    
    return redirect("/settings")
