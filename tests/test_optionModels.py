"""
Simple component tests for optionModels.py
Tests the Option class methods with mocked database connections.
Run with: pytest tests/test_optionModels.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# Mock the database connection before importing the Option class
@pytest.fixture(autouse=True)
def mock_db_connection():
    """Automatically mock the database connection for all tests"""
    with patch('flask_app.models.optionModels.connectToMySQL') as mock_connect:
        yield mock_connect


# Test data fixtures
@pytest.fixture
def sample_option_data():
    """Sample data that would come from the database"""
    return {
        'option_id': 1,
        'option_text': 'Option A',
        'option_event_id': 10
    }


@pytest.fixture
def sample_option_list():
    """Sample list of options from database"""
    return [
        {'option_id': 1, 'option_text': 'Option A', 'option_event_id': 10},
        {'option_id': 2, 'option_text': 'Option B', 'option_event_id': 10},
        {'option_id': 3, 'option_text': 'Option C', 'option_event_id': 10}
    ]


# ============================================================================
# TEST: Option.__init__() - Constructor
# ============================================================================

def test_option_init_creates_instance_with_correct_attributes(sample_option_data):
    """Test that Option constructor properly initializes all attributes"""
    from flask_app.models.optionModels import Option
    
    option = Option(sample_option_data)
    
    assert option.option_id == 1
    assert option.option_text == 'Option A'
    assert option.option_event_id == 10


def test_option_init_handles_different_data_types():
    """Test that Option constructor handles string IDs (as they might come from DB)"""
    from flask_app.models.optionModels import Option
    
    data = {
        'option_id': '5',
        'option_text': 'Test Option',
        'option_event_id': '20'
    }
    
    option = Option(data)
    
    assert option.option_id == '5'
    assert option.option_text == 'Test Option'
    assert option.option_event_id == '20'


# ============================================================================
# TEST: Option.getByEventId() - Retrieve options by event ID
# ============================================================================

def test_getByEventId_returns_list_of_options(mock_db_connection, sample_option_list):
    """Test that getByEventId returns a list of Option objects"""
    from flask_app.models.optionModels import Option
    
    # Setup mock to return our sample data
    mock_query = Mock(return_value=sample_option_list)
    mock_db_connection.return_value.query_db = mock_query
    
    # Call the method
    data = {'event_id': 10}
    result = Option.getByEventId(data)
    
    # Verify the query was called with correct SQL and data
    mock_db_connection.assert_called_once_with('mydb')
    mock_query.assert_called_once()
    call_args = mock_query.call_args[0]
    assert 'SELECT * FROM `option`' in call_args[0]
    assert 'WHERE option_event_id = %(event_id)s' in call_args[0]
    assert call_args[1] == data
    
    # Verify results
    assert len(result) == 3
    assert all(isinstance(opt, Option) for opt in result)
    assert result[0].option_text == 'Option A'
    assert result[1].option_text == 'Option B'
    assert result[2].option_text == 'Option C'


def test_getByEventId_returns_empty_list_when_no_options(mock_db_connection):
    """Test that getByEventId returns empty list when no options found"""
    from flask_app.models.optionModels import Option
    
    # Setup mock to return empty list
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    # Call the method
    data = {'event_id': 999}
    result = Option.getByEventId(data)
    
    # Verify empty list is returned
    assert result == []
    assert isinstance(result, list)


# ============================================================================
# TEST: Option.create() - Create new option
# ============================================================================

def test_create_inserts_option_into_database(mock_db_connection):
    """Test that create method calls database with correct SQL and data"""
    from flask_app.models.optionModels import Option
    
    # Setup mock to return new option ID
    mock_query = Mock(return_value=5)  # Simulating new ID returned
    mock_db_connection.return_value.query_db = mock_query
    
    # Call the method
    data = {
        'option_text': 'New Option',
        'option_event_id': 15
    }
    result = Option.create(data)
    
    # Verify the query was called
    mock_db_connection.assert_called_once_with('mydb')
    mock_query.assert_called_once()
    call_args = mock_query.call_args[0]
    
    # Verify SQL contains INSERT statement
    assert 'INSERT INTO `option`' in call_args[0]
    assert 'option_text' in call_args[0]
    assert 'option_event_id' in call_args[0]
    assert call_args[1] == data
    
    # Verify return value
    assert result == 5


def test_create_returns_database_response(mock_db_connection):
    """Test that create returns whatever the database returns"""
    from flask_app.models.optionModels import Option
    
    # Setup mock to return True (successful insert)
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'option_text': 'Test', 'option_event_id': 1}
    result = Option.create(data)
    
    assert result == True


# ============================================================================
# TEST: Option.deleteByEventId() - Delete options by event ID
# ============================================================================

def test_deleteByEventId_calls_delete_query(mock_db_connection):
    """Test that deleteByEventId executes DELETE query with correct parameters"""
    from flask_app.models.optionModels import Option
    
    # Setup mock
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    # Call the method
    data = {'event_id': 10}
    result = Option.deleteByEventId(data)
    
    # Verify the query was called
    mock_db_connection.assert_called_once_with('mydb')
    mock_query.assert_called_once()
    call_args = mock_query.call_args[0]
    
    # Verify SQL contains DELETE statement
    assert 'DELETE FROM `option`' in call_args[0]
    assert 'WHERE option_event_id = %(event_id)s' in call_args[0]
    assert call_args[1] == data
    
    # Verify return value
    assert result == True


def test_deleteByEventId_handles_nonexistent_event(mock_db_connection):
    """Test that deleteByEventId handles case when event has no options"""
    from flask_app.models.optionModels import Option
    
    # Setup mock to simulate no rows affected
    mock_query = Mock(return_value=False)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 999}
    result = Option.deleteByEventId(data)
    
    # Should still execute without error
    mock_query.assert_called_once()
    assert result == False


# ============================================================================
# INTEGRATION-STYLE TEST (optional - tests multiple methods together)
# ============================================================================

def test_option_workflow_create_retrieve_delete(mock_db_connection, sample_option_list):
    """Test a typical workflow: create options, retrieve them, then delete them"""
    from flask_app.models.optionModels import Option
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Step 1: Create options
    mock_query.return_value = 1
    Option.create({'option_text': 'Option A', 'option_event_id': 10})
    
    mock_query.return_value = 2
    Option.create({'option_text': 'Option B', 'option_event_id': 10})
    
    # Step 2: Retrieve options
    mock_query.return_value = sample_option_list
    options = Option.getByEventId({'event_id': 10})
    assert len(options) == 3
    
    # Step 3: Delete options
    mock_query.return_value = True
    result = Option.deleteByEventId({'event_id': 10})
    assert result == True
    
    # Verify query_db was called 4 times (2 creates, 1 get, 1 delete)
    assert mock_query.call_count == 4