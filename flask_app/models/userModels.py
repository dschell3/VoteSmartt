from flask_app.config.mysqlconnection import connectToMySQL
import re
from flask import flash
from flask_app import app
from datetime import datetime, timedelta

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

db = "votingSystem"

class User:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.created_at = data['created_at']
        self.phone = data['phone']
        
        
    
    @classmethod
    def register(cls, data):
        query = '''
        INSERT INTO users
        (first_name, last_name, email, password, phone, created_at) 
        VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(phone)s, NOW());
        '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def getUserByEmail(cls, data):
        query = "SELECT * FROM users WHERE email = %(email)s;"
        
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        return cls(result[0])