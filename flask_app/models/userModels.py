'''
==============================================================================
User Model - Manages user accounts and role-based access control
==============================================================================

This module provides the User class for managing user registration,
authentication, profile management, and role-based permissions within
the VoteSmartt system. Could add implementation to include a super admin type user.

Database Table: user
Columns:
    - user_id (int): Primary key, auto-increment
    - first_name (varchar): User's first name
    - last_name (varchar): User's last name
    - email (varchar): Unique email address for login
    - password (varchar): Bcrypt-hashed password
    - phone (varchar): Contact phone number
    - created_at (datetime): Account creation timestamp
    - isAdmin (tinyint): Role flag (0=Voter, 1=Admin)

Class Relationships:
    - User 1--* Event: One user can create many events (via created_byFK)
    - User 1--* Vote: One user can cast many votes (across different events)

Security Considerations:
    - Passwords stored as bcrypt hashes (hashing done in controller)
    - Password reset tokens are SHA-256 hashed before storage
    - Reset tokens expire after configurable TTL (default 30 minutes)
    - Email existence not revealed during password reset (security by obscurity)
'''

from flask_app.config.mysqlconnection import connectToMySQL
from datetime import datetime, timedelta
import secrets
import hashlib

db = "mydb"

class User:
    """
    Represents a user account in the VoteSmartt system.
    """
    db = db         # DB identifier for mySQL connection
    
    def __init__(self, data):
        """
        Initialize a User instance from database row data.
        """
        self.user_id = data['user_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.phone = data['phone']
        self.created_at = data['created_at']
        # Handle isAdmin field safely - convert None to 0, then to int
        # This prevents errors when isAdmin is missing or NULL in DB result
        isAdmin_value = data.get('isAdmin', 0)
        self.isAdmin = int(isAdmin_value) if isAdmin_value is not None else 0
        
    # =========================================================================
    # PROPERTIES - Computed attributes
    # =========================================================================

    @property
    def is_admin(self) -> bool:
        """
        Check if user has administrator privileges. No super admin registration path in
        current implementation, but is checked for throughout controllers. Could be a
        future upgrade.
        
        Returns:
            bool: True if user is admin (isAdmin=1), False if voter (isAdmin=0)
        """
        return self.isAdmin == 1

    # =========================================================================
    # ROLE-BASED CAPABILITY METHODS - Permission checks, user level
    # =========================================================================
    
    def canCastVote(self) -> bool:       
        """
        Checks if user is allowed to cast votes. They are not admin.
        
        Returns:
            bool: True if user can vote (is a voter), False if admin
        """
        return not self.is_admin

    def canManageEvent(self, event) -> bool:
        """
        Check if user can manage a specific event (edit/delete).
        Event management is allowed for:
        1. Administrators (can manage any event)
        2. Event creators (can manage their own events)
        
        Args:
            event (Events): Event object to check permissions for
        
        Returns:
            bool: True if user can manage the event, False otherwise
        """
        return self.is_admin or (event.created_byFK == self.user_id)

    # =========================================================================
    # CREATE OPERATIONS - User registration
    # =========================================================================
    
    @classmethod
    def register(cls, data):
        """
        Create a new user account in the database.
        The created_at timestamp is automatically set to NOW(). 
        New users are created as voters (isAdmin=0) by default.
        
        Args:
            data (dict): Dictionary containing:
                         - 'first_name' (str): User's first name
                         - 'last_name' (str): User's last name
                         - 'email' (str): Unique email address
                         - 'password' (str): Pre-hashed password
                         - 'phone' (str): Contact phone number
        
        Returns:
            int: The user_id of the newly created user, or False on failure
        """
        query = '''
        INSERT INTO
        user
        (first_name, last_name, email, password, phone, created_at) 
        VALUES 
        (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(phone)s, NOW());
        '''
        return connectToMySQL(db).query_db(query, data)

    # =========================================================================
    # READ OPERATIONS - User retrieval
    # =========================================================================

    @classmethod
    def getUserByEmail(cls, data):
        """
        Retrieve a user by their email address.
        
        Args:
            data (dict): Dictionary containing:
                         - 'email' (str): Email address to search for
        
        Returns:
            User: User object if found, None if no user with that email
        """
        query = "SELECT * FROM user WHERE email = %(email)s;"
        
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        return cls(result[0])

    @classmethod
    def getUserByID(cls,data):
        """
        Retrieve a user by their primary key.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): User's primary key
        
        Returns:
            User: User object if found, None if user doesn't exist or on error
        """
        query = "SELECT * FROM user WHERE user_id = %(user_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        # Handle both empty results ([]) and database errors (False)
        if not result or result is False:
            return None
        try:
            return cls(result[0])
        except Exception:
            return None
    
    @classmethod
    def getAllUsers(cls):
        """
        Retrieve all users for admin dashboard display.
   
        Args:
            None
        
        Returns:
            list[dict]: List of user dictionaries (not User objects)
                        containing: user_id, first_name, last_name,
                        email, phone, created_at, isAdmin
                        Returns empty list or False on error.
        """
        # Explicitly select columns to exclude password from results
        query = """
        SELECT user_id, first_name, last_name, email, phone, created_at, isAdmin
        FROM user
        ORDER BY created_at DESC;
        """
        return connectToMySQL(db).query_db(query)

    # =========================================================================
    # UPDATE OPERATIONS - Profile and password management
    # =========================================================================

    @classmethod
    def updateProfile(cls, data):
        """
        Update user's profile information (excluding password).
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): User to update
                         - 'first_name' (str): New first name
                         - 'last_name' (str): New last name
                         - 'email' (str): New email address
                         - 'phone' (str): New phone number
        
        Returns:
            bool: True if update successful, False otherwise
        """
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
        """
        Update user's password.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): User to update
                         - 'password' (str): New pre-hashed password
        
        Returns:
            bool: True if update successful, False otherwise
        """
        query = """
        UPDATE user 
        SET 
            password = %(password)s 
        WHERE user_id = %(user_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    

    # =========================================================================
    # PASSWORD RESET TOKEN FLOW - Secure password recovery
    # =========================================================================
    # These methods implement a secure token-based password reset flow:
    # 1. User requests reset -> createPasswordResetToken() generates token
    # 2. User clicks email link -> verifyPasswordResetToken() validates
    # 3. User submits new password -> consumePasswordResetToken() marks used

    @classmethod
    def createPasswordResetToken(cls, email: str, ttl_minutes: int = 30):
        """
        Generate a one-time password reset token for a user.
        Creates a cryptographically secure token, hashes it with SHA-256,
        and stores the hash in the database. The raw (unhashed) token is
        returned for inclusion in the reset email link.
        
        Args:
            email (str): Email address of user requesting reset
            ttl_minutes (int): Token validity period (default 30 minutes)
        
        Returns:
            tuple: (success: bool, raw_token: str or None)
                   - (True, token_string) on success
                   - (True, None) if email not found (prevents enumeration)
                   - (True, None) on database error (fails silently)
        
        Security Notes:
            - Returns success even for non-existent emails to prevent
              attackers from discovering valid email addresses
            - Only the SHA-256 hash is stored; raw token is not persisted
            - Token expires after ttl_minutes (default 30)
        """
        # Look up user by email
        user = cls.getUserByEmail({'email': email})
        if not user:
            return True, None   # return success w/o email to avoid leaking email existence

        # Generate token
        raw_token = secrets.token_urlsafe(32)
        # Store the hash
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Determine experation time
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        # Insert token record
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
        return True, raw_token      # Return raw token for email link

    @classmethod
    def verifyPasswordResetToken(cls, raw_token: str):
        """
        Validate a password reset token and return associated user info.
        Hashes the provided token and looks up the matching record.
        Only returns valid tokens that are unused and not expired.
        
        Args:
            raw_token (str): The token string from the reset URL
        
        Returns:
            dict: Token and user information if valid:
                  - 'token_id' (int): Token's database ID
                  - 'user_id' (int): Associated user's ID
                  - 'expires_at' (datetime): Expiration timestamp
                  - 'used_at' (datetime or None): When token was consumed
                  - 'email' (str): User's email address
                  - 'password' (str): User's current hashed password
                  Returns None if token is invalid, expired, or already used.
        """
        if not raw_token:
            return None
        
        # Hash the token to match against the stored hash
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        # Look up the token, to ensure its unused + not expired
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
        """
        Mark a password reset token as used (consumed).
        Should be called after successfully updating the user's password
        to prevent token reuse. Sets used_at timestamp to current time.
        
        Args:
            raw_token (str): The token string that was used
        
        Returns:
            bool: True if token was marked as used, False otherwise
        """
        if not raw_token:
            return False
        # Hash token to match the stored value
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        # Mark token as used by setting used_at timestamp
        query = (
            """
            UPDATE password_reset_token
            SET used_at = NOW()
            WHERE token_hash = %(token_hash)s AND used_at IS NULL;
            """
        )
        return bool(connectToMySQL(db).query_db(query, {'token_hash': token_hash}))
