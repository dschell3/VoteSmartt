"""
Validation utilities for user inputs across the Flask app.
Provides consistent validation across files and centralizes rules.

All validation logic should go through this module to ensure:
1. Consistent error messages
2. Single source of truth for validation rules
3. Easy testing of validation logic
4. No duplicate validation code
"""

import re

#TODO: - ALEX - Complete the remaining validation functions below

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

def validate_name(name, field_name="Name"):
    """
    Validate first or last name.
    Returns error message or None if valid.
    2-50 characters.
    """
    ...


def validate_email(email):
    """
    Validate email format.
    Returns error message or None if valid.
    can use EMAIL_REGEX
    """
    ...

def validate_password(password):
    """
    Validate password meets security requirements.
    Returns error message or None if valid.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    - Contains special character
    """
    if not password:
        return "Password is required"
    
    if len(password) < 8:
        return "Password must be at least 8 characters"
    
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    
    return None


def validate_phone(phone):
    """
    Validate phone number (US format).
    Returns error message or None if valid.
    Removes non-digit characters and checks for 10 digits.
    10 digits required.
    """
    ...


def format_phone(phone):
    """
    Format phone number consistently: (123) 456-7890
    Returns formatted phone or original if invalid.
    10 digits required. In the format (123) 456-7890
    """
    ...


def validate_all_registration_fields(first_name, last_name, email, password, phone):
    """
    Validate all registration fields at once.
    Returns list of error messages (empty if all valid).
    """
    errors = []
    
    # Validate each field
    error = validate_name(first_name, "First name")
    if error:
        errors.append(error)
    
    error = validate_name(last_name, "Last name")
    if error:
        errors.append(error)
    
    error = validate_email(email)
    if error:
        errors.append(error)
    
    error = validate_password(password)
    if error:
        errors.append(error)
    
    error = validate_phone(phone)
    if error:
        errors.append(error)
    
    return errors
