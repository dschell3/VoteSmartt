from flask_app.config.mysqlconnection import connectToMySQL
from flask_app.utils.validators import (
    validate_all_registration_fields, validate_email,
    validate_name, validate_password, validate_phone )

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
        # self.isAdmin = int(data.get('isAdmin', 0)) // Backup in case of errors
        # Handle isAdmin field safely - convert None to 0, then to int
        isAdmin_value = data.get('isAdmin', 0)
        self.isAdmin = int(isAdmin_value) if isAdmin_value is not None else 0
        
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

    def can_manage_events(self) -> bool:
        """Only admins can create/edit/delete voting events"""
        return self.is_admin
    
    def can_manage_users(self) -> bool:
        """Only admins can manage user accounts"""
        return self.is_admin


    # ===== CLASS METHODS FOR DB INTERACTIONS =====
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
    
    # TODO - Registration method for admin users
    @classmethod
    def register_admin(cls, data):
        ...
    
    # TODO: Admin methods to promote users
    # TODO: Admin method to delete users...how would this impact their previous votes?
    # TODO: Admin should not be able to reset their own password via this method

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

        # TODO: Ask Jang how to implement email sending using existing app infrastructure
        # TODO: use send_email function from userController
        reset_link = f"http://localhost:5000/reset_password?email={data['email']}"
        try:
            from flask_app.controllers.userController import send_email
            send_email(
                to_address=data['email'],
                subject="Password Reset Request",
                body=f"Click the link below to reset your password:\n{reset_link}"
            )
            return {"ok": True}
        except Exception as e:
            # Fail gracefully to avoid leaking user existence and to prevent 500s in AJAX flow
            print(f"Password reset email send failed: {e}")
            return {"ok": True}

    @classmethod
    def resetPasswordByEmail(cls, data):
        """Directly update the user's password if the email exists.
        Expects data['password'] to ALREADY be hashed."""
        user = cls.getUserByEmail({'email': data['email']})
        if not user:
            return False
        return cls.updatePassword({'user_id': user.user_id, 'password': data['password']})

    # ===== PASSWORD RESET TOKEN FLOW =====
    @classmethod
    def createPasswordResetToken(cls, email: str, ttl_minutes: int = 30):
        """Create a one-time password reset token for the given email.

        Returns a tuple (ok: bool, raw_token: str or None).
        If email doesn't exist, returns (True, None) to avoid leaking info.
        """
        user = cls.getUserByEmail({'email': email})
        if not user:
            return True, None

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        query = (
            """
            INSERT INTO password_reset_token
                (user_id, token_hash, expires_at, created_at)
            VALUES
                (%(user_id)s, %(token_hash)s, %(expires_at)s, NOW());
            """
        )
        data = {
            'user_id': user.user_id,
            'token_hash': token_hash,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        ok = connectToMySQL(db).query_db(query, data)
        if not ok:
            # Fail silently (do not reveal user existence)
            return True, None
        return True, raw_token

    @classmethod
    def verifyPasswordResetToken(cls, raw_token: str):
        """Verify token validity. Returns dict with token row + user, or None.

        Output example: { 'token_id': 1, 'user_id': 2, 'email': 'x', ... }
        """
        if not raw_token:
            return None
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        query = (
            """
            SELECT t.id as token_id, t.user_id, t.expires_at, t.used_at,
                   u.email, u.password
            FROM password_reset_token t
            JOIN user u ON u.user_id = t.user_id
            WHERE t.token_hash = %(token_hash)s
              AND (t.used_at IS NULL)
              AND (t.expires_at > NOW());
            """
        )
        rows = connectToMySQL(db).query_db(query, {'token_hash': token_hash})
        if not rows:
            return None
        return rows[0]

    @classmethod
    def consumePasswordResetToken(cls, raw_token: str):
        """Mark a token as used. Returns True/False."""
        if not raw_token:
            return False
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        query = (
            """
            UPDATE password_reset_token
            SET used_at = NOW()
            WHERE token_hash = %(token_hash)s AND used_at IS NULL;
            """
        )
        return bool(connectToMySQL(db).query_db(query, {'token_hash': token_hash}))


    # ===== INPUT VALIDATION METHODS ===== 
    @staticmethod
    def validatePassword(password: str) -> bool:
        """Return True if the password meets minimum security requirements."""
        error = validate_password(password)
        return error is None

    @staticmethod
    def validateEmail(email: str) -> bool:
        """return True if the email format is valid."""
        error = validate_email(email)
        return error is None

    @staticmethod
    def validatePhone(phone: str) -> bool:
        """return True if the phone number format is valid."""
        error = validate_phone(phone)
        return error is None
    
    # TODO - Static method to validate names (first/last) ?
    # e.g., non-empty, reasonable length, no invalid characters

    # TODO - Static method to normalize phone number format for storage/display?