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
    

    # Complete Password reset functionality
    # create password_tokens_db table to store password reset tokens
    # with fields: id, user_id, token_hash, expires_at, used_at, created_at
    # token_hash is a sha256 hash of a random token we generate 
    
    @classmethod
    def createPasswordReset( cls, email: str) -> dict:
        # look up user by email, returns none if not found
        user = cls.getUserByEmail( { 'email': email } )
        # generate a token either way
        raw_token = secrets.token_urlsafe(32)     # send to user
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()  # store in db
        expires_at = (datetime.now() + timedelta(minutes=RESET_TOKEN_MIN)).strftime("%Y-%m-%d %H:%M:%S")

        if user:
            # should we delete any existing tokens for this user first?
            connectToMySQL(db).query_db(
                """
                UPDATE password_tokens_db SET used_at = NOW() 
                WHERE user_id = %(uid)s AND used_at IS NULL;
                """, 
                { 'uid': user.user_id })
            # store the hashed token
            connectToMySQL(db).query_db(
                """
                INSERT INTO password_tokens_db (user_id, token_hash, expires_at) 
                VALUES (%(uid)s, %(th)s, %(exp)s);
                """, 
                { 'uid': user.user_id, 'th': token_hash, 'exp': expires_at })
            
        # return the plain token so the caller can email a link to the user
        return { "ok": True, "token": raw_token, "ttl_mins": RESET_TOKEN_MIN }
    
    @classmethod
    def resetPasswordWithToken( cls, token: str, new_password: str) -> bool:
        #check if token is valid, marks it used if so, and updates password
        # returns true on success, false otherwise
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        rows = connectToMySQL(db).query_db(
            """
            SELECT prt.id, prt.user_id, prt.expires_at, prt.used_at 
            FROM password_tokens_db prt
            WHERE pt.token_hash = %(th)s 
              AND pt.used_at IS NULL 
            LIMIT 1;
            """, 
            { 'th': token_hash })
        
        if not rows:
            return False
        
        rec = rows[0]
        expires_at = rec['expires_at']
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return False
            
        if datetime.utcnow() > rec["expires_at"]:
            return False
        
        # hash the new password and update the user record
        bcrypt = Bcrypt()
        pw_hash = bcrypt.generate_password_hash(new_password)
        ok = cls.updatePassword( { 'user_id': rec['user_id'], 'password': pw_hash } )
        if not ok:
            return False
        
        # mark the token used
        connectToMySQL(db).query_db(
            """
            UPDATE password_tokens_db 
            SET used_at = NOW() 
            WHERE id = %(id)s;
            """, 
            { 'id': rec['id'] })
        return True
    
