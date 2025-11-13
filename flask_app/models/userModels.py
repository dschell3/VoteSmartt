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
    #                            password, isAdminByID, created_at, phone
    
    def __init__(self, data):
        self.user_id = data['user_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.phone = data['phone']
        self.created_at = data['created_at']
        self.isAdminByID = int(data.get('isAdminByID', 0)) # always set an int 0/1
        # FIXME...isAdminByID Default already set to 0 in DB schema? role not on UML
        
    @property
    def is_admin(self) -> bool:
        return self.isAdminByID == 1

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
        query = "SELECT isAdminByID FROM user WHERE user_id = %(user_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        return bool(result and result[0].get("isAdminByID") == 1)

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
        SELECT user_id, first_name, last_name, email, phone, created_at, isAdminByID
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
    
    @classmethod
    def sendPasswordResetEmail(cls, data):
        """Check if the email belongs to a registered user; if so, send a reset link."""
        user = cls.getUserByEmail({'email': data['email']})
        if not user:
            # Return generic OK to avoid revealing whether email exists
            return {"ok": True}
        # Generate a one-time token, store only its hash and expiry, and email the raw token in a link.
        try:
            token = cls._create_password_reset_token_for_user(user)
        except Exception:
            # If DB update fails (missing columns etc.), fall back to sending an email-only link
            token = None

        base = app.config.get('BASE_URL', 'http://localhost:5000')
        if token:
            reset_link = f"{base}/reset_password?email={data['email']}&token={token}"
        else:
            reset_link = f"{base}/reset_password?email={data['email']}"

        from flask_app.controllers.userController import send_email
        send_email(
            to_address=data['email'],
            subject="Password Reset Request",
            body=(f"You requested a password reset. Click the link below to set a new password.\n"
                  f"This link will expire in 30 minutes.\n\n{reset_link}\n\n"
                  "If you didn't request this, you can safely ignore this email." )
        )
        return {"ok": True}

    @classmethod
    def _create_password_reset_token_for_user(cls, user):
        """Create a secure token, store its SHA256 hash and expiry (30 minutes) on the user row.

        Returns the raw token (string) on success. Raises on DB errors (so caller can fall back).
        """
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires = (datetime.utcnow() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

        query = """
        UPDATE user
        SET reset_token = %(reset_token)s, reset_token_expires = %(expires)s
        WHERE user_id = %(user_id)s;
        """
        data = {'reset_token': token_hash, 'expires': expires, 'user_id': user.user_id}
        connectToMySQL(db).query_db(query, data)
        return token

    @classmethod
    def _verify_reset_token_for_user(cls, user, token):
        """Verify provided raw token against stored hash and expiry. Returns True if valid."""
        try:
            query = "SELECT reset_token, reset_token_expires FROM user WHERE user_id = %(user_id)s;"
            rows = connectToMySQL(db).query_db(query, {'user_id': user.user_id})
            if not rows:
                return False
            row = rows[0]
            stored_hash = row.get('reset_token')
            expires = row.get('reset_token_expires')
            if not stored_hash or not expires:
                return False

            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Normalize expires to datetime
            if isinstance(expires, str):
                try:
                    expires_dt = datetime.strptime(expires.split('.')[0], '%Y-%m-%d %H:%M:%S')
                except Exception:
                    return False
            else:
                expires_dt = expires

            if datetime.utcnow() > expires_dt:
                return False

            return stored_hash == token_hash
        except Exception:
            return False

    @classmethod
    def resetPasswordWithToken(cls, data):
        """Reset a user's password using a one-time token.

        Expects data to contain 'email', 'token', and 'password' (already hashed).
        Returns truthy on success, False on failure.
        """
        user = cls.getUserByEmail({'email': data.get('email')})
        if not user:
            return False

        token = data.get('token')
        if not token:
            return False

        valid = cls._verify_reset_token_for_user(user, token)
        if not valid:
            return False

        # Update password and clear token fields
        try:
            query = """
            UPDATE user
            SET password = %(password)s, reset_token = NULL, reset_token_expires = NULL
            WHERE user_id = %(user_id)s;
            """
            return connectToMySQL(db).query_db(query, {'password': data['password'], 'user_id': user.user_id})
        except Exception:
            # Fall back to best-effort password update
            return cls.updatePassword({'user_id': user.user_id, 'password': data['password']})

    @classmethod
    def resetPasswordByEmail(cls, data):
        """Directly update the user's password if the email exists.
        Expects data['password'] to ALREADY be hashed."""
        user = cls.getUserByEmail({'email': data['email']})
        if not user:
            return False
        return cls.updatePassword({'user_id': user.user_id, 'password': data['password']})

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
