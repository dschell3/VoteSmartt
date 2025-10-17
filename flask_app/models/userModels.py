from flask_app.config.mysqlconnection import connectToMySQL
import re, secrets, hashlib
from flask import flash
from flask_app import app
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

RESET_TOKEN_MIN = 30 
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

db = "mydb"

class User:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.phone = data['phone']
        self.created_at = data['created_at']
        
        
    
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
    
    @classmethod
    def sendPasswordResetEmail(cls, email: str):
        """Check if the email belongs to a registered user; if so, send a reset link."""
        user = cls.getUserByEmail({'email': email})
        if not user:
            # Return generic OK to avoid revealing whether email exists
            return {"ok": True}

        reset_link = f"http://localhost:5000/reset_password?email={email}"
        # Replace this placeholder with your actual email sending logic
        from flask_app.controllers.userController import send_email
        send_email(
            to_address=email,
            subject="Password Reset Request",
            body=f"Click the link below to reset your password:\n{reset_link}"
        )
        return {"ok": True}
    
    @classmethod
    def resetPasswordByEmail(cls, email: str, new_password: str) -> bool:
        """Directly update the user's password if the email exists."""
        user = cls.getUserByEmail({'email': email})
        if not user:
            return False

        pw_hash = bcrypt.generate_password_hash(new_password)
        return cls.updatePassword({'user_id': user.user_id, 'password': pw_hash})
    
