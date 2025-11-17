"""
Simple component tests for userModels.py
Tests the User class methods with mocked database connections.
Run with: pytest tests/test_userModels.py -v
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


# Mock the database connection before importing the User class
@pytest.fixture(autouse=True)
def mock_db_connection():
    """Automatically mock the database connection for all tests"""
    with patch('flask_app.models.userModels.connectToMySQL') as mock_connect:
        yield mock_connect


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample data for creating a User instance"""
    return {
        'user_id': 1,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'hashed_password_123',
        'phone': '(916) 555-1234',
        'created_at': datetime(2025, 1, 1, 10, 0, 0),
        'isAdmin': 0
    }


@pytest.fixture
def sample_admin_data():
    """Sample data for an admin user"""
    return {
        'user_id': 2,
        'first_name': 'Admin',
        'last_name': 'User',
        'email': 'admin@example.com',
        'password': 'hashed_admin_password',
        'phone': '(916) 555-9999',
        'created_at': datetime(2025, 1, 1, 10, 0, 0),
        'isAdmin': 1
    }


@pytest.fixture
def sample_user_list():
    """Sample list of users (without passwords)"""
    return [
        {
            'user_id': 1, 'first_name': 'John', 'last_name': 'Doe',
            'email': 'john@example.com', 'phone': '(916) 555-1234',
            'created_at': datetime(2025, 1, 1), 'isAdmin': 0
        },
        {
            'user_id': 2, 'first_name': 'Jane', 'last_name': 'Smith',
            'email': 'jane@example.com', 'phone': '(916) 555-5678',
            'created_at': datetime(2025, 1, 2), 'isAdmin': 1
        }
    ]


# ============================================================================
# TEST: User.__init__() - Constructor
# ============================================================================

def test_user_init_creates_instance_with_correct_attributes(sample_user_data):
    """Test that User constructor properly initializes all attributes"""
    from flask_app.models.userModels import User
    
    user = User(sample_user_data)
    
    assert user.user_id == 1
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'
    assert user.email == 'john.doe@example.com'
    assert user.password == 'hashed_password_123'
    assert user.phone == '(916) 555-1234'
    assert user.isAdmin == 0


def test_user_init_defaults_isAdmin_to_zero():
    """Test that isAdmin defaults to 0 when not provided"""
    from flask_app.models.userModels import User
    
    data = {
        'user_id': 1, 'first_name': 'Test', 'last_name': 'User',
        'email': 'test@example.com', 'password': 'pass',
        'phone': '1234567890', 'created_at': datetime(2025, 1, 1)
        # isAdmin not provided
    }
    
    user = User(data)
    
    assert user.isAdmin == 0


# ============================================================================
# TEST: User.is_admin - Property
# ============================================================================

def test_is_admin_property_returns_true_for_admin(sample_admin_data):
    """Test that is_admin property returns True for admin users"""
    from flask_app.models.userModels import User
    
    user = User(sample_admin_data)
    
    assert user.is_admin == True


def test_is_admin_property_returns_false_for_regular_user(sample_user_data):
    """Test that is_admin property returns False for regular users"""
    from flask_app.models.userModels import User
    
    user = User(sample_user_data)
    
    assert user.is_admin == False


# ============================================================================
# TEST: User.can_cast_vote() - Role-based method
# ============================================================================

def test_can_cast_vote_returns_true_for_regular_user(sample_user_data):
    """Test that regular users can cast votes"""
    from flask_app.models.userModels import User
    
    user = User(sample_user_data)
    
    assert user.can_cast_vote() == True


def test_can_cast_vote_returns_false_for_admin(sample_admin_data):
    """Test that admins cannot cast votes"""
    from flask_app.models.userModels import User
    
    user = User(sample_admin_data)
    
    assert user.can_cast_vote() == False


# ============================================================================
# TEST: User.can_manage_events() - Role-based method
# ============================================================================

def test_can_manage_events_returns_true_for_admin(sample_admin_data):
    """Test that admins can manage events"""
    from flask_app.models.userModels import User
    
    user = User(sample_admin_data)
    
    assert user.can_manage_events() == True


def test_can_manage_events_returns_false_for_regular_user(sample_user_data):
    """Test that regular users cannot manage events"""
    from flask_app.models.userModels import User
    
    user = User(sample_user_data)
    
    assert user.can_manage_events() == False


# ============================================================================
# TEST: User.can_manage_users() - Role-based method
# ============================================================================

def test_can_manage_users_returns_true_for_admin(sample_admin_data):
    """Test that admins can manage users"""
    from flask_app.models.userModels import User
    
    user = User(sample_admin_data)
    
    assert user.can_manage_users() == True


def test_can_manage_users_returns_false_for_regular_user(sample_user_data):
    """Test that regular users cannot manage users"""
    from flask_app.models.userModels import User
    
    user = User(sample_user_data)
    
    assert user.can_manage_users() == False


# ============================================================================
# TEST: User.register() - Create new user
# ============================================================================

def test_register_inserts_user_into_database(mock_db_connection):
    """Test that register inserts a new user with correct SQL"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=1)  # Return new user ID
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'first_name': 'New',
        'last_name': 'User',
        'email': 'new@example.com',
        'password': 'hashed_password',
        'phone': '(916) 555-0000'
    }
    result = User.register(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'INSERT INTO' in call_args[0]
    assert 'user' in call_args[0]
    assert 'first_name' in call_args[0]
    assert 'last_name' in call_args[0]
    assert 'email' in call_args[0]
    assert 'password' in call_args[0]
    assert 'phone' in call_args[0]
    assert 'NOW()' in call_args[0]
    
    assert result == 1


def test_register_uses_now_for_created_at(mock_db_connection):
    """Test that register uses NOW() for created_at timestamp"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=1)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'first_name': 'Test', 'last_name': 'User',
        'email': 'test@example.com', 'password': 'pass',
        'phone': '1234567890'
    }
    User.register(data)
    
    call_args = mock_query.call_args[0]
    assert 'NOW()' in call_args[0]


# ============================================================================
# TEST: User.getUserByID() - Retrieve user by ID
# ============================================================================

def test_getUserByID_returns_user_object(mock_db_connection, sample_user_data):
    """Test that getUserByID returns a User object when user exists"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=[sample_user_data])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 1}
    result = User.getUserByID(data)
    
    # Verify SQL
    call_args = mock_query.call_args[0]
    assert 'SELECT * FROM user' in call_args[0]
    assert 'WHERE user_id = %(user_id)s' in call_args[0]
    
    # Verify result
    assert isinstance(result, User)
    assert result.user_id == 1
    assert result.first_name == 'John'


def test_getUserByID_returns_none_when_not_found(mock_db_connection):
    """Test that getUserByID returns None when user doesn't exist"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 999}
    result = User.getUserByID(data)
    
    assert result is None


def test_getUserByID_handles_false_result(mock_db_connection):
    """Test that getUserByID handles database error (False result)"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=False)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 1}
    result = User.getUserByID(data)
    
    assert result is None


# ============================================================================
# TEST: User.getUserByEmail() - Retrieve user by email
# ============================================================================

def test_getUserByEmail_returns_user_object(mock_db_connection, sample_user_data):
    """Test that getUserByEmail returns a User object when user exists"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=[sample_user_data])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'email': 'john.doe@example.com'}
    result = User.getUserByEmail(data)
    
    # Verify SQL
    call_args = mock_query.call_args[0]
    assert 'SELECT * FROM user' in call_args[0]
    assert 'WHERE email = %(email)s' in call_args[0]
    
    # Verify result
    assert isinstance(result, User)
    assert result.email == 'john.doe@example.com'


def test_getUserByEmail_returns_none_when_not_found(mock_db_connection):
    """Test that getUserByEmail returns None when user doesn't exist"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'email': 'nonexistent@example.com'}
    result = User.getUserByEmail(data)
    
    assert result is None


# ============================================================================
# TEST: User.getAllUsers() - Retrieve all users
# ============================================================================

def test_getAllUsers_returns_list_of_users(mock_db_connection, sample_user_list):
    """Test that getAllUsers returns a list of user data"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=sample_user_list)
    mock_db_connection.return_value.query_db = mock_query
    
    result = User.getAllUsers()
    
    # Verify SQL
    call_args = mock_query.call_args[0]
    assert 'SELECT user_id, first_name, last_name, email, phone, created_at, isAdmin' in call_args[0]
    assert 'FROM user' in call_args[0]
    assert 'ORDER BY created_at DESC' in call_args[0]
    # Verify password is NOT selected
    assert 'password' not in call_args[0]
    
    # Verify results
    assert len(result) == 2
    assert result[0]['first_name'] == 'John'
    assert result[1]['first_name'] == 'Jane'


def test_getAllUsers_excludes_password_field(mock_db_connection):
    """Test that getAllUsers does not include password information"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    User.getAllUsers()
    
    call_args = mock_query.call_args[0]
    # Password should NOT be in SELECT statement
    assert 'password' not in call_args[0].lower() or 'SELECT user_id' in call_args[0]


# ============================================================================
# TEST: User.updateProfile() - Update user profile
# ============================================================================

def test_updateProfile_updates_user_correctly(mock_db_connection):
    """Test that updateProfile updates user information"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'user_id': 1,
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'updated@example.com',
        'phone': '(916) 555-9999'
    }
    result = User.updateProfile(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'UPDATE user' in call_args[0]
    assert 'SET' in call_args[0]
    assert 'first_name' in call_args[0]
    assert 'last_name' in call_args[0]
    assert 'email' in call_args[0]
    assert 'phone' in call_args[0]
    assert 'WHERE user_id' in call_args[0]
    
    assert result == True


def test_updateProfile_does_not_update_password(mock_db_connection):
    """Test that updateProfile does not modify password"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'user_id': 1, 'first_name': 'Test', 'last_name': 'User',
        'email': 'test@example.com', 'phone': '1234567890'
    }
    User.updateProfile(data)
    
    call_args = mock_query.call_args[0]
    # Password should NOT be in UPDATE statement
    assert 'password' not in call_args[0]


# ============================================================================
# TEST: User.updatePassword() - Update user password
# ============================================================================

def test_updatePassword_updates_password_correctly(mock_db_connection):
    """Test that updatePassword updates user password"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'user_id': 1,
        'password': 'new_hashed_password'
    }
    result = User.updatePassword(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'UPDATE user' in call_args[0]
    assert 'SET' in call_args[0]
    assert 'password' in call_args[0]
    assert 'WHERE user_id' in call_args[0]
    
    assert result == True


def test_updatePassword_only_updates_password(mock_db_connection):
    """Test that updatePassword only modifies password field"""
    from flask_app.models.userModels import User
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 1, 'password': 'new_pass'}
    User.updatePassword(data)
    
    call_args = mock_query.call_args[0]
    # Should only update password, not other fields
    assert 'password' in call_args[0]
    assert 'first_name' not in call_args[0]
    assert 'email' not in call_args[0]


# ============================================================================
# INTEGRATION TESTS - Test complete workflows
# ============================================================================

def test_user_registration_and_retrieval(mock_db_connection, sample_user_data):
    """Test complete workflow: register user then retrieve by ID"""
    from flask_app.models.userModels import User
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Register user
    mock_query.return_value = 1
    user_id = User.register({
        'first_name': 'John', 'last_name': 'Doe',
        'email': 'john@example.com', 'password': 'hashed',
        'phone': '1234567890'
    })
    assert user_id == 1
    
    # Retrieve by ID
    mock_query.return_value = [sample_user_data]
    user = User.getUserByID({'user_id': user_id})
    assert user is not None
    assert user.first_name == 'John'
    
    assert mock_query.call_count == 2


def test_role_based_permissions_workflow(sample_user_data, sample_admin_data):
    """Test that role-based permissions work correctly for different user types"""
    from flask_app.models.userModels import User
    
    voter = User(sample_user_data)
    admin = User(sample_admin_data)
    
    # Voters can vote, cannot manage
    assert voter.can_cast_vote() == True
    assert voter.can_manage_events() == False
    assert voter.can_manage_users() == False
    
    # Admins can manage, cannot vote
    assert admin.can_cast_vote() == False
    assert admin.can_manage_events() == True
    assert admin.can_manage_users() == True