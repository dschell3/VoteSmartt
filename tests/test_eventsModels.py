"""
Simple component tests for eventsModels.py
Tests the Events class methods with mocked database connections.
Run with: pytest tests/test_eventsModels.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# Mock the database connection before importing the Events class
@pytest.fixture(autouse=True)
def mock_db_connection():
    """Automatically mock the database connection for all tests"""
    with patch('flask_app.models.eventsModels.connectToMySQL') as mock_connect:
        yield mock_connect


# Test data fixtures
@pytest.fixture
def sample_event_data():
    """Sample data for creating an Events instance"""
    return {
        'event_id': 1,
        'title': 'Presidential Election 2025',
        'description': 'Vote for the next president',
        'start_time': datetime(2025, 1, 10, 8, 0, 0),
        'end_time': datetime(2025, 1, 20, 20, 0, 0),
        'created_byFK': 5,
        'created_at': datetime(2025, 1, 1, 10, 0, 0),
        'status': 'Open'
    }


@pytest.fixture
def sample_event_list():
    """Sample list of events from database"""
    return [
        {
            'event_id': 1, 'title': 'Event 1', 'description': 'Desc 1',
            'start_time': datetime(2025, 1, 10), 'end_time': datetime(2025, 1, 20),
            'created_byFK': 5, 'created_at': datetime(2025, 1, 1), 'status': 'Open'
        },
        {
            'event_id': 2, 'title': 'Event 2', 'description': 'Desc 2',
            'start_time': datetime(2025, 2, 10), 'end_time': datetime(2025, 2, 20),
            'created_byFK': 5, 'created_at': datetime(2025, 1, 2), 'status': 'Waiting'
        }
    ]


@pytest.fixture
def sample_events_with_creators():
    """Sample events with creator information"""
    return [
        {
            'event_id': 1, 'title': 'Event 1', 'description': 'Desc 1',
            'start_time': datetime(2025, 1, 10), 'end_time': datetime(2025, 1, 20),
            'created_byFK': 5, 'created_at': datetime(2025, 1, 1), 'status': 'Open',
            'first_name': 'John', 'last_name': 'Doe'
        },
        {
            'event_id': 2, 'title': 'Event 2', 'description': 'Desc 2',
            'start_time': datetime(2025, 2, 10), 'end_time': datetime(2025, 2, 20),
            'created_byFK': 6, 'created_at': datetime(2025, 1, 2), 'status': 'Waiting',
            'first_name': 'Jane', 'last_name': 'Smith'
        }
    ]


# ============================================================================
# TEST: Events.__init__() - Constructor
# ============================================================================

def test_events_init_creates_instance_with_correct_attributes(sample_event_data):
    """Test that Events constructor properly initializes all attributes"""
    from flask_app.models.eventsModels import Events
    
    event = Events(sample_event_data)
    
    assert event.event_id == 1
    assert event.title == 'Presidential Election 2025'
    assert event.description == 'Vote for the next president'
    assert event.start_time == datetime(2025, 1, 10, 8, 0, 0)
    assert event.end_time == datetime(2025, 1, 20, 20, 0, 0)
    assert event.created_byFK == 5
    assert event.created_at == datetime(2025, 1, 1, 10, 0, 0)
    assert event.status == 'Open'


def test_events_init_handles_different_data_types():
    """Test that Events constructor handles string IDs (as they might come from DB)"""
    from flask_app.models.eventsModels import Events
    
    data = {
        'event_id': '10',
        'title': 'Test Event',
        'description': 'Test Description',
        'start_time': '2025-01-10',
        'end_time': '2025-01-20',
        'created_byFK': '7',
        'created_at': '2025-01-01',
        'status': 'Waiting'
    }
    
    event = Events(data)
    
    assert event.event_id == '10'
    assert event.title == 'Test Event'
    assert event.created_byFK == '7'


# ============================================================================
# TEST: Events.createEvent() - Create new event
# ============================================================================

def test_createEvent_inserts_event_into_database(mock_db_connection):
    """Test that createEvent inserts a new event with correct SQL"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=1)  # Return new event ID
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'title': 'New Election',
        'description': 'Description',
        'start_time': datetime(2025, 3, 1),
        'end_time': datetime(2025, 3, 10),
        'created_byFK': 5,
        'status': 'Waiting'
    }
    result = Events.createEvent(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'INSERT INTO event' in call_args[0]
    assert 'title' in call_args[0]
    assert 'description' in call_args[0]
    assert 'start_time' in call_args[0]
    assert 'end_time' in call_args[0]
    assert 'created_byFK' in call_args[0]
    assert 'NOW()' in call_args[0]
    assert 'status' in call_args[0]
    
    assert result == 1


def test_createEvent_uses_now_for_created_at(mock_db_connection):
    """Test that createEvent uses NOW() for created_at timestamp"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=1)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'title': 'Event', 'description': 'Desc',
        'start_time': datetime(2025, 3, 1), 'end_time': datetime(2025, 3, 10),
        'created_byFK': 5, 'status': 'Waiting'
    }
    Events.createEvent(data)
    
    call_args = mock_query.call_args[0]
    assert 'NOW()' in call_args[0]


# ============================================================================
# TEST: Events.editEvent() - Update existing event
# ============================================================================

def test_editEvent_updates_event_correctly(mock_db_connection):
    """Test that editEvent updates event with correct SQL"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'event_id': 1,
        'title': 'Updated Title',
        'description': 'Updated Description',
        'start_time': datetime(2025, 3, 5),
        'end_time': datetime(2025, 3, 15)
    }
    result = Events.editEvent(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'UPDATE event' in call_args[0]
    assert 'SET title' in call_args[0]
    assert 'description' in call_args[0]
    assert 'start_time' in call_args[0]
    assert 'end_time' in call_args[0]
    assert 'WHERE event_id' in call_args[0]
    
    assert result == True


def test_editEvent_does_not_update_created_fields(mock_db_connection):
    """Test that editEvent doesn't modify created_byFK or created_at"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'event_id': 1, 'title': 'Updated', 'description': 'Updated',
        'start_time': datetime(2025, 3, 5), 'end_time': datetime(2025, 3, 15)
    }
    Events.editEvent(data)
    
    call_args = mock_query.call_args[0]
    # Verify created_byFK and created_at are NOT in UPDATE
    assert 'created_byFK' not in call_args[0]
    assert 'created_at' not in call_args[0]


# ============================================================================
# TEST: Events.deleteEvent() - Delete event
# ============================================================================

def test_deleteEvent_deletes_event_correctly(mock_db_connection):
    """Test that deleteEvent removes event with correct SQL"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 1}
    result = Events.deleteEvent(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'DELETE FROM event' in call_args[0]
    assert 'WHERE event_id = %(event_id)s' in call_args[0]
    
    assert result == True


def test_deleteEvent_returns_false_when_event_doesnt_exist(mock_db_connection):
    """Test that deleteEvent returns False when event doesn't exist"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=False)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 999}
    result = Events.deleteEvent(data)
    
    assert result == False


# ============================================================================
# TEST: Events.getOne() - Retrieve single event by ID
# ============================================================================

def test_getOne_returns_event_object(mock_db_connection, sample_event_data):
    """Test that getOne returns an Events object when event exists"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=[sample_event_data])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 1}
    result = Events.getOne(data)
    
    # Verify SQL
    call_args = mock_query.call_args[0]
    assert 'SELECT * FROM event' in call_args[0]
    assert 'WHERE event_id = %(event_id)s' in call_args[0]
    
    # Verify result
    assert isinstance(result, Events)
    assert result.event_id == 1
    assert result.title == 'Presidential Election 2025'


def test_getOne_returns_none_when_not_found(mock_db_connection):
    """Test that getOne returns None when event doesn't exist"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 999}
    result = Events.getOne(data)
    
    assert result is None


# ============================================================================
# TEST: Events.getAllWithCreators() - Get events with creator info
# ============================================================================

def test_getAllWithCreators_adds_creator_info(mock_db_connection, sample_events_with_creators):
    """Test that getAllWithCreators adds creator information to events"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_events_with_creators)
    mock_db_connection.return_value.query_db = mock_query
    
    # Mock compute_status to avoid datetime issues
    with patch.object(Events, 'compute_status', return_value='Open'):
        with patch.object(Events, 'parse_datetime', return_value=datetime(2025, 1, 10)):
            result = Events.getAllWithCreators()
            
            # Verify SQL includes JOIN
            call_args = mock_query.call_args[0]
            assert 'LEFT JOIN user u' in call_args[0]
            assert 'ON e.created_byFK = u.user_id' in call_args[0]
            
            # Verify creator info is added
            assert len(result) == 2
            assert result[0].creator_first_name == 'John'
            assert result[0].creator_last_name == 'Doe'
            assert result[0].creator_full_name == 'John Doe'
            assert result[1].creator_full_name == 'Jane Smith'


def test_getAllWithCreators_calls_compute_status(mock_db_connection, sample_events_with_creators):
    """Test that getAllWithCreators computes status for each event"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_events_with_creators)
    mock_db_connection.return_value.query_db = mock_query
    
    with patch.object(Events, 'compute_status', return_value='Open') as mock_compute:
        with patch.object(Events, 'parse_datetime', return_value=datetime(2025, 1, 10)):
            result = Events.getAllWithCreators()
            
            # Verify compute_status was called for each event
            assert mock_compute.call_count == 2


# ============================================================================
# TEST: Events.getRecommendations() - Get upcoming events
# ============================================================================

def test_getRecommendations_excludes_current_event(mock_db_connection, sample_event_list):
    """Test that getRecommendations excludes the provided event_id"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_event_list)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 1}
    result = Events.getRecommendations(data)
    
    # Verify SQL excludes the event
    call_args = mock_query.call_args[0]
    assert 'WHERE event_id != %(event_id)s' in call_args[0]
    assert 'ORDER BY start_time ASC' in call_args[0]
    assert 'LIMIT 3' in call_args[0]


def test_getRecommendations_returns_up_to_3_events(mock_db_connection, sample_event_list):
    """Test that getRecommendations returns maximum 3 events"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_event_list)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 1}
    result = Events.getRecommendations(data)
    
    assert len(result) <= 3


# ============================================================================
# TEST: Events.getUpcoming() - Get future events
# ============================================================================

def test_getUpcoming_returns_future_events(mock_db_connection, sample_event_list):
    """Test that getUpcoming returns events that haven't started yet"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_event_list)
    mock_db_connection.return_value.query_db = mock_query
    
    result = Events.getUpcoming()
    
    # Verify SQL
    call_args = mock_query.call_args[0]
    assert 'WHERE e.start_time > NOW()' in call_args[0]
    assert 'ORDER BY e.start_time ASC' in call_args[0]


def test_getUpcoming_respects_limit_parameter(mock_db_connection, sample_event_list):
    """Test that getUpcoming applies LIMIT when provided"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock(return_value=sample_event_list)
    mock_db_connection.return_value.query_db = mock_query
    
    result = Events.getUpcoming(limit=5)
    
    # Verify LIMIT is in query
    call_args = mock_query.call_args[0]
    assert 'LIMIT 5' in call_args[0]


# ============================================================================
# TEST: Events.compute_status() - Static method for status calculation
# ============================================================================

def test_compute_status_returns_open_when_event_is_active():
    """Test that compute_status returns 'Open' when current time is between start and end"""
    from flask_app.models.eventsModels import Events
    from datetime import datetime as real_datetime
    
    # Patch only datetime.now, not the whole datetime module
    with patch('flask_app.models.eventsModels.datetime') as mock_dt:
        # Make the mock inherit from the real datetime
        mock_dt.now = Mock(return_value=real_datetime(2025, 1, 15))
        # Pass through isinstance checks by making mock look like datetime module
        mock_dt.__class__ = type(real_datetime)
        
        # Pass actual datetime objects
        start = real_datetime(2025, 1, 10)
        end = real_datetime(2025, 1, 20)
        
        # Mock parse_datetime to return the datetime objects as-is
        with patch.object(Events, 'parse_datetime', side_effect=lambda x: x):
            status = Events.compute_status(start, end)
            assert status == 'Open'


def test_compute_status_returns_waiting_when_not_started():
    """Test that compute_status returns 'Waiting' when event hasn't started"""
    from flask_app.models.eventsModels import Events
    from datetime import datetime as real_datetime
    
    with patch('flask_app.models.eventsModels.datetime') as mock_dt:
        mock_dt.now = Mock(return_value=real_datetime(2025, 1, 5))
        
        start = real_datetime(2025, 1, 10)
        end = real_datetime(2025, 1, 20)
        
        with patch.object(Events, 'parse_datetime', side_effect=lambda x: x):
            status = Events.compute_status(start, end)
            assert status == 'Waiting'


def test_compute_status_returns_closed_when_ended():
    """Test that compute_status returns 'Closed' when event has ended"""
    from flask_app.models.eventsModels import Events
    from datetime import datetime as real_datetime
    
    with patch('flask_app.models.eventsModels.datetime') as mock_dt:
        mock_dt.now = Mock(return_value=real_datetime(2025, 1, 25))
        
        start = real_datetime(2025, 1, 10)
        end = real_datetime(2025, 1, 20)
        
        with patch.object(Events, 'parse_datetime', side_effect=lambda x: x):
            status = Events.compute_status(start, end)
            assert status == 'Closed'


def test_compute_status_returns_unknown_when_no_times():
    """Test that compute_status returns 'Unknown' when both times are None"""
    from flask_app.models.eventsModels import Events
    
    status = Events.compute_status(None, None)
    
    assert status == 'Unknown'


# ============================================================================
# TEST: Events.parse_datetime() - Static method for datetime parsing
# ============================================================================

def test_parse_datetime_handles_datetime_objects():
    """Test that parse_datetime returns datetime objects as-is"""
    from flask_app.models.eventsModels import Events
    
    dt = datetime(2025, 1, 15, 10, 30, 0)
    result = Events.parse_datetime(dt)
    
    assert result == dt


def test_parse_datetime_handles_none():
    """Test that parse_datetime returns None for None input"""
    from flask_app.models.eventsModels import Events
    
    result = Events.parse_datetime(None)
    
    assert result is None


# ============================================================================
# INTEGRATION TESTS - Test complete workflows
# ============================================================================

def test_event_lifecycle_create_edit_delete(mock_db_connection):
    """Test complete event lifecycle: create, edit, delete"""
    from flask_app.models.eventsModels import Events
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Create event
    mock_query.return_value = 1
    event_id = Events.createEvent({
        'title': 'Test Event',
        'description': 'Description',
        'start_time': datetime(2025, 3, 1),
        'end_time': datetime(2025, 3, 10),
        'created_byFK': 5,
        'status': 'Waiting'
    })
    assert event_id == 1
    
    # Edit event
    mock_query.return_value = True
    edited = Events.editEvent({
        'event_id': 1,
        'title': 'Updated Event',
        'description': 'Updated',
        'start_time': datetime(2025, 3, 2),
        'end_time': datetime(2025, 3, 11)
    })
    assert edited == True
    
    # Delete event
    mock_query.return_value = True
    deleted = Events.deleteEvent({'event_id': 1})
    assert deleted == True
    
    # Verify 3 operations
    assert mock_query.call_count == 3


def test_status_computation_workflow():
    """Test status computation across different time scenarios"""
    from flask_app.models.eventsModels import Events
    from datetime import datetime as real_datetime
    
    start = real_datetime(2025, 1, 10)
    end = real_datetime(2025, 1, 20)
    
    # Mock parse_datetime to pass through datetime objects
    with patch.object(Events, 'parse_datetime', side_effect=lambda x: x):
        # Before event starts
        with patch('flask_app.models.eventsModels.datetime') as mock_dt:
            mock_dt.now = Mock(return_value=real_datetime(2025, 1, 5))
            assert Events.compute_status(start, end) == 'Waiting'
        
        # During event
        with patch('flask_app.models.eventsModels.datetime') as mock_dt:
            mock_dt.now = Mock(return_value=real_datetime(2025, 1, 15))
            assert Events.compute_status(start, end) == 'Open'
        
        # After event ends
        with patch('flask_app.models.eventsModels.datetime') as mock_dt:
            mock_dt.now = Mock(return_value=real_datetime(2025, 1, 25))
            assert Events.compute_status(start, end) == 'Closed'