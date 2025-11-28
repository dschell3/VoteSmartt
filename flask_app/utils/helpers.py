"""
Shared helper functions for authentication and session management.
"""

from flask import session, redirect, flash
from flask_app.models.userModels import User

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def require_login(redirect_to="/unauthorized"):
    """
    Check if user is logged in. Returns redirect URL if not logged in.

    Returns:
        redirect URL string if not logged in, None if logged in
  
    """
    if "user_id" not in session:
        if redirect_to == "/login":
            flash("Please log in to access this page")
        else:
            flash("Should you really be here? Please sign in to continue.")
        return redirect_to
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    if not user:
        session.clear()
        flash("Session expired. Please log in again.")
        return redirect_to
    
    return None  # User is logged in


def get_current_user():
    """
    Get the currently logged-in user from session.
    
    Returns:
        User object if logged in, None otherwise
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    return User.getUserByID({'user_id': user_id})


def require_voter():
    """
    Check if current user is a voter (not admin). Returns True if should be BLOCKED.
    This enforces the business rule that administrators cannot vote.
    
    Returns:
        True if user is admin (should be blocked from voting)
        False if user is voter (allowed to vote)
    """
    user = get_current_user()
    if not user or not user.canCastVote():
        flash("Administrators cannot vote on events.", "error")
        return True
    return False


# ============================================================================
# SESSION DATA HELPERS
# ============================================================================

def get_user_session_data():
    """
    Get user session data formatted for templates.
    
    Returns:
        Dictionary with user info for templates:
        - logged_in: True/False
        - first_name, last_name, email, phone, user_id, created_at (if logged in)
    """
    user = get_current_user()
    
    if not user:
        return {'logged_in': False}
    
    return {
        'logged_in': True,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'user_id': user.user_id,
        'created_at': user.created_at
    }
