from flask_app.config.mysqlconnection import connectToMySQL
import re, secrets, hashlib
from flask import flash
from flask_app import app
from datetime import datetime, timedelta

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

db = "mydb"

class User:
    db = db
    # columns in user table are: user_id, first_name, last_name, email,
    #                            password, isAdmin, created_at, phone
    
    def __init__(self, data):
        self.user_id = data['user_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.phone = data['phone']
        self.created_at = data['created_at']
        self.isAdmin = int(data.get('isAdmin', 0)) # always set an int 0/1
        
    @property
    def is_admin(self) -> bool:
        return self.isAdmin == 1

    # ===== ROLE-BASED CAPABILITIES =====
    # These methods define what actions each role can perform
    # Used for easy to read explicit permission checks, make code + UML consistent
    
    def can_cast_vote(self) -> bool:
        """Only non-admin users (voters) can cast votes
        Admins are prohibited from voting to maintain integrity"""
        return not self.is_admin
    
    def can_view_events(self) -> bool:
        """All users can view events"""
        return True

    def can_manage_events(self) -> bool:
        """Only admins can create/edit/delete voting events"""
        return self.is_admin
    
    def can_manage_users(self) -> bool:
        """Only admins can manage user accounts"""
        return self.is_admin


    @classmethod
    def register(cls, data):
        query = '''
        INSERT INTO
        user
        (first_name, last_name, email, password, phone, created_at) 
        VALUES 
        (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(phone)s, NOW());
        '''
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def isAdminByID(cls, data):
        query = "SELECT isAdmin FROM user WHERE user_id = %(user_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        return bool(result and result[0].get("isAdmin") == 1)

    @classmethod
    def getUserByEmail(cls, data):
        query = "SELECT * FROM user WHERE email = %(email)s;"
        
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        return cls(result[0])

    @classmethod
    def getUserByID(cls,data):
        query = "SELECT * FROM user WHERE user_id = %(user_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        # The DB layer returns False on error, [] when no rows, or a list of dicts on success.
        if not result or result is False:
            return None
        try:
            return cls(result[0])
        except Exception:
            return None
    
    @classmethod
    def getAllUsers(cls):
        # Get all users ordered by creation date descending, w/o password information
        query = """
        SELECT user_id, first_name, last_name, email, phone, created_at, isAdmin
        FROM user
        ORDER BY created_at DESC;
        """
        return connectToMySQL(db).query_db(query)

    @classmethod
    def updateProfile(cls, data):
        query = """
        UPDATE user
        SET 
            first_name = %(first_name)s, 
            last_name = %(last_name)s, 
            email = %(email)s, 
            phone = %(phone)s 
        WHERE user_id = %(user_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def updatePassword(cls, data):
        query = """
        UPDATE user 
        SET 
            password = %(password)s 
        WHERE user_id = %(user_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    # refactor later to simplify/combine with resetPasswordByEmail and use the send_email in userController
    @classmethod
    def sendPasswordResetEmail(cls, data):
        """Check if the email belongs to a registered user; if so, send a reset link."""
        user = cls.getUserByEmail({'email': data['email']})
        if not user:
            # Return generic OK to avoid revealing whether email exists
            return {"ok": True}

        # FIXME: Ask Jang how to create a link/token for password reset
        # FIXME: Implement actual send_email() function
        reset_link = f"http://localhost:5000/reset_password?email={data['email']}"
        from flask_app.controllers.userController import send_email
        send_email(
            to_address=data['email'],
            subject="Password Reset Request",
            body=f"Click the link below to reset your password:\n{reset_link}"
        )
        return {"ok": True}

    # TODO: Admin methods to promote users
    # TODO: Admin method to delete users...how would this impact their previous votes?
    
    # TODO: Admin should not be able to reset their own password via this method
    @classmethod
    def resetPasswordByEmail(cls, data):
        """Directly update the user's password if the email exists.
        Expects data['password'] to ALREADY be hashed."""
        user = cls.getUserByEmail({'email': data['email']})
        if not user:
            return False
        return cls.updatePassword({'user_id': user.user_id, 'password': data['password']})


    # ===== INPUT VALIDATION METHODS ===== 
    @staticmethod
    def validatePassword(password: str) -> bool:
        """Return True if the password meets minimum security requirements."""
        if not password or len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False
        return True

    # TODO - Static methods to validate email and phone number formats
    @staticmethod
    def validateEmail(email: str) -> bool:
        """Return True if the email format is valid."""
        ...

    @staticmethod
    def validatePhone(phone: str) -> bool:
        """Return True if the phone number format is valid."""
        ...