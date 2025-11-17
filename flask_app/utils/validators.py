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

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

def validate_name(name, field_name="Name"):
    """
    Validate first or last name.
    Returns error message or None if valid.
    """
    if not name or not isinstance(name, str):
        return f"{field_name} is required"
    
    name = name.strip()
    if len(name) < 2:
        return f"{field_name} must be at least 2 characters"
    
    if len(name) > 50:
        return f"{field_name} must be less than 50 characters"
    
    return None


def validate_email(email):
    """
    Validate email format.
    Returns error message or None if valid.
    """
    if not email or not isinstance(email, str):
        return "Email is required"
    
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        return "Please enter a valid email address"
    
    return None

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
    """
    if not phone or not isinstance(phone, str):
        return "Phone number is required"
    
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    if len(phone_digits) != 10:
        return "Phone number must be 10 digits"
    
    return None


def format_phone(phone):
    """
    Format phone number consistently: (123) 456-7890
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    if len(phone_digits) == 10:
        return f"({phone_digits[:3]}) {phone_digits[3:6]}-{phone_digits[6:]}"
    
    return phone


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
