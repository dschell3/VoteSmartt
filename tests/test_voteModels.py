"""
Simple component tests for voteModels.py
Tests the Vote class methods with mocked database connections and Events model.
Run with: pytest tests/test_voteModels.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# Mock the database connection before importing the Vote class
@pytest.fixture(autouse=True)
def mock_db_connection():
    """Automatically mock the database connection for all tests"""
    with patch('flask_app.models.voteModels.connectToMySQL') as mock_connect:
        yield mock_connect


# Test data fixtures
@pytest.fixture
def sample_vote_data():
    """Sample data for creating a Vote instance"""
    return {
        'vote_id': 1,
        'voted_at': datetime(2025, 1, 15, 10, 30, 0),
        'vote_user_id': 5,
        'vote_option_id': 10
    }


@pytest.fixture
def sample_vote_list():
    """Sample list of votes from database"""
    return [
        {'vote_id': 1, 'voted_at': datetime(2025, 1, 15), 'vote_user_id': 5, 'vote_option_id': 10},
        {'vote_id': 2, 'voted_at': datetime(2025, 1, 16), 'vote_user_id': 6, 'vote_option_id': 11},
    ]


@pytest.fixture
def sample_recent_votes_data():
    """Sample data returned by getRecentForUser with joined tables"""
    return [
        {
            'vote_id': 1,
            'voted_at': datetime(2025, 1, 15),
            'event_id': 100,
            'event_name': 'Election 2025',
            'start_time': datetime(2025, 1, 10),
            'end_time': datetime(2025, 1, 20),
            'option_text': 'Option A'
        },
        {
            'vote_id': 2,
            'voted_at': datetime(2025, 1, 12),
            'event_id': 101,
            'event_name': 'Survey',
            'start_time': datetime(2025, 1, 5),
            'end_time': datetime(2025, 1, 15),
            'option_text': 'Yes'
        }
    ]


@pytest.fixture
def sample_tally_data():
    """Sample vote tally data"""
    return [
        {'option_id': 1, 'option_text': 'Option A', 'votes': 10},
        {'option_id': 2, 'option_text': 'Option B', 'votes': 5}
    ]


@pytest.fixture
def mock_event():
    """Mock Event object for testing isEditable"""
    event = Mock()
    event.start_time = datetime(2025, 1, 10)
    event.end_time = datetime(2025, 1, 20)
    return event


# ============================================================================
# TEST: Vote.__init__() - Constructor
# ============================================================================

def test_vote_init_creates_instance_with_correct_attributes(sample_vote_data):
    """Test that Vote constructor properly initializes all attributes"""
    from flask_app.models.voteModels import Vote
    
    vote = Vote(sample_vote_data)
    
    assert vote.vote_id == 1
    assert vote.voted_at == datetime(2025, 1, 15, 10, 30, 0)
    assert vote.vote_user_id == 5
    assert vote.vote_option_id == 10


def test_vote_init_handles_different_data_types():
    """Test that Vote constructor handles string IDs (as they might come from DB)"""
    from flask_app.models.voteModels import Vote
    
    data = {
        'vote_id': '2',
        'voted_at': '2025-01-15',
        'vote_user_id': '7',
        'vote_option_id': '12'
    }
    
    vote = Vote(data)
    
    assert vote.vote_id == '2'
    assert vote.vote_user_id == '7'
    assert vote.vote_option_id == '12'


# ============================================================================
# TEST: Vote.getByID() - Retrieve vote by ID
# ============================================================================

def test_getByID_returns_vote_object(mock_db_connection, sample_vote_data):
    """Test that getByID returns a Vote object when vote exists"""
    from flask_app.models.voteModels import Vote
    
    # Setup mock to return sample data
    mock_query = Mock(return_value=[sample_vote_data])
    mock_db_connection.return_value.query_db = mock_query
    
    # Call the method
    result = Vote.getByID({'vote_id': 1})
    
    # Verify query was called correctly
    mock_db_connection.assert_called_once_with('mydb')
    mock_query.assert_called_once()
    call_args = mock_query.call_args[0]
    assert 'SELECT * FROM vote' in call_args[0]
    assert 'WHERE vote_id = %(vote_id)s' in call_args[0]
    
    # Verify result
    assert isinstance(result, Vote)
    assert result.vote_id == 1


def test_getByID_returns_none_when_not_found(mock_db_connection):
    """Test that getByID returns None when vote doesn't exist"""
    from flask_app.models.voteModels import Vote
    
    # Setup mock to return empty result
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    result = Vote.getByID({'vote_id': 999})
    
    assert result is None


# ============================================================================
# TEST: Vote.getByUserAndEvent() - Get user's vote for an event
# ============================================================================

def test_getByUserAndEvent_returns_vote_object(mock_db_connection, sample_vote_data):
    """Test that getByUserAndEvent returns user's vote for a specific event"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=[sample_vote_data])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 5, 'event_id': 100}
    result = Vote.getByUserAndEvent(data)
    
    # Verify SQL includes JOIN with option table
    call_args = mock_query.call_args[0]
    assert 'JOIN `option` o' in call_args[0]
    assert 'WHERE v.vote_user_id = %(user_id)s' in call_args[0]
    assert 'AND o.option_event_id = %(event_id)s' in call_args[0]
    assert 'LIMIT 1' in call_args[0]
    
    # Verify result
    assert isinstance(result, Vote)
    assert result.vote_user_id == 5


def test_getByUserAndEvent_returns_none_when_user_hasnt_voted(mock_db_connection):
    """Test that getByUserAndEvent returns None when user hasn't voted in event"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=[])
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 5, 'event_id': 100}
    result = Vote.getByUserAndEvent(data)
    
    assert result is None


# ============================================================================
# TEST: Vote.getRecentForUser() - Get recent votes for a user
# ============================================================================

def test_getRecentForUser_returns_formatted_vote_list(mock_db_connection, sample_recent_votes_data):
    """Test that getRecentForUser returns properly formatted vote history"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=sample_recent_votes_data)
    mock_db_connection.return_value.query_db = mock_query
    
    # Mock Events.compute_status
    with patch('flask_app.models.voteModels.Events.compute_status', return_value='Open'):
        data = {'user_id': 5, 'limit': 3}
        result = Vote.getRecentForUser(data)
        
        # Verify SQL structure
        call_args = mock_query.call_args[0]
        assert 'JOIN `option` o' in call_args[0]
        assert 'JOIN event e' in call_args[0]
        assert 'ORDER BY v.voted_at DESC' in call_args[0]
        assert 'LIMIT %(limit)s' in call_args[0]
        
        # Verify result structure
        assert len(result) == 2
        assert result[0]['vote_id'] == 1
        assert result[0]['event_name'] == 'Election 2025'
        assert result[0]['status'] == 'open'
        assert result[0]['vote_type'] == 'Option A'
        assert result[0]['event_id'] == 100


def test_getRecentForUser_returns_empty_list_when_no_votes(mock_db_connection):
    """Test that getRecentForUser returns empty list when user has no votes"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=None)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 5, 'limit': 3}
    result = Vote.getRecentForUser(data)
    
    assert result == []


def test_getRecentForUser_calls_compute_status_for_each_vote(mock_db_connection, sample_recent_votes_data):
    """Test that getRecentForUser calls Events.compute_status for each vote"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=sample_recent_votes_data)
    mock_db_connection.return_value.query_db = mock_query
    
    with patch('flask_app.models.voteModels.Events.compute_status') as mock_compute:
        mock_compute.side_effect = ['Open', 'Closed']  # Different statuses for each vote
        
        data = {'user_id': 5, 'limit': 3}
        result = Vote.getRecentForUser(data)
        
        # Verify compute_status was called twice (once per vote)
        assert mock_compute.call_count == 2
        
        # Verify statuses are lowercase
        assert result[0]['status'] == 'open'
        assert result[1]['status'] == 'closed'


# ============================================================================
# TEST: Vote.castVote() - Cast a new vote
# ============================================================================

def test_castVote_inserts_vote_into_database(mock_db_connection):
    """Test that castVote inserts a new vote with correct SQL"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=1)  # Return new vote ID
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'vote_user_id': 5, 'vote_option_id': 10}
    result = Vote.castVote(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'INSERT INTO vote' in call_args[0]
    assert 'voted_at' in call_args[0]
    assert 'vote_user_id' in call_args[0]
    assert 'vote_option_id' in call_args[0]
    assert 'NOW()' in call_args[0]
    
    # Verify return value
    assert result == 1


def test_castVote_uses_now_for_timestamp(mock_db_connection):
    """Test that castVote uses NOW() for voted_at timestamp"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=1)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'vote_user_id': 5, 'vote_option_id': 10}
    Vote.castVote(data)
    
    # Verify NOW() is in the query
    call_args = mock_query.call_args[0]
    assert 'NOW()' in call_args[0]


# ============================================================================
# TEST: Vote.changeVote() - Update an existing vote
# ============================================================================

def test_changeVote_updates_vote_correctly(mock_db_connection):
    """Test that changeVote updates the option and timestamp"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'user_id': 5,
        'event_id': 100,
        'new_option_id': 15
    }
    result = Vote.changeVote(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'UPDATE vote v' in call_args[0]
    assert 'JOIN `option` o' in call_args[0]
    assert 'SET v.vote_option_id = %(new_option_id)s' in call_args[0]
    assert 'v.voted_at = NOW()' in call_args[0]
    assert 'WHERE v.vote_user_id = %(user_id)s' in call_args[0]
    assert 'AND o.option_event_id = %(event_id)s' in call_args[0]
    
    assert result == True


def test_changeVote_returns_false_when_no_vote_exists(mock_db_connection):
    """Test that changeVote returns False when no vote exists to update"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=False)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {
        'user_id': 5,
        'event_id': 100,
        'new_option_id': 15
    }
    result = Vote.changeVote(data)
    
    assert result == False


# ============================================================================
# TEST: Vote.deleteVote() - Delete a vote
# ============================================================================

def test_deleteVote_deletes_vote_correctly(mock_db_connection):
    """Test that deleteVote removes user's vote for an event"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=True)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 5, 'event_id': 100}
    result = Vote.deleteVote(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'DELETE v FROM vote v' in call_args[0]
    assert 'JOIN `option` o' in call_args[0]
    assert 'WHERE v.vote_user_id = %(user_id)s' in call_args[0]
    assert 'AND o.option_event_id = %(event_id)s' in call_args[0]
    
    assert result == True


def test_deleteVote_returns_false_when_no_vote_exists(mock_db_connection):
    """Test that deleteVote returns False when no vote exists to delete"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=False)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'user_id': 5, 'event_id': 100}
    result = Vote.deleteVote(data)
    
    assert result == False


# ============================================================================
# TEST: Vote.tallyVotesForEvent() - Get vote counts for an event
# ============================================================================

def test_tallyVotesForEvent_returns_vote_counts(mock_db_connection, sample_tally_data):
    """Test that tallyVotesForEvent returns option vote counts"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=sample_tally_data)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 100}
    result = Vote.tallyVotesForEvent(data)
    
    # Verify SQL structure
    call_args = mock_query.call_args[0]
    assert 'SELECT o.option_id, o.option_text, COUNT(v.vote_id) AS votes' in call_args[0]
    assert 'FROM `option` o' in call_args[0]
    assert 'LEFT JOIN vote v' in call_args[0]
    assert 'WHERE o.option_event_id = %(event_id)s' in call_args[0]
    assert 'GROUP BY o.option_id, o.option_text' in call_args[0]
    assert 'ORDER BY votes DESC, o.option_text ASC' in call_args[0]
    
    # Verify results
    assert len(result) == 2
    assert result[0]['option_text'] == 'Option A'
    assert result[0]['votes'] == 10


def test_tallyVotesForEvent_handles_events_with_no_votes(mock_db_connection):
    """Test that tallyVotesForEvent handles events where no one has voted"""
    from flask_app.models.voteModels import Vote
    
    # Options exist but have 0 votes
    no_votes_data = [
        {'option_id': 1, 'option_text': 'Option A', 'votes': 0},
        {'option_id': 2, 'option_text': 'Option B', 'votes': 0}
    ]
    
    mock_query = Mock(return_value=no_votes_data)
    mock_db_connection.return_value.query_db = mock_query
    
    data = {'event_id': 100}
    result = Vote.tallyVotesForEvent(data)
    
    assert len(result) == 2
    assert all(row['votes'] == 0 for row in result)


# ============================================================================
# TEST: Vote.isEditable() - Check if vote can be edited
# ============================================================================

def test_isEditable_returns_true_when_event_is_open(mock_event):
    """Test that isEditable returns True when event status is Open"""
    from flask_app.models.voteModels import Vote
    
    with patch('flask_app.models.voteModels.Events.compute_status', return_value='Open'):
        result = Vote.isEditable(mock_event)
        assert result == True


def test_isEditable_returns_false_when_event_is_closed(mock_event):
    """Test that isEditable returns False when event is Closed"""
    from flask_app.models.voteModels import Vote
    
    with patch('flask_app.models.voteModels.Events.compute_status', return_value='Closed'):
        result = Vote.isEditable(mock_event)
        assert result == False


def test_isEditable_returns_false_when_event_is_waiting(mock_event):
    """Test that isEditable returns False when event is Waiting"""
    from flask_app.models.voteModels import Vote
    
    with patch('flask_app.models.voteModels.Events.compute_status', return_value='Waiting'):
        result = Vote.isEditable(mock_event)
        assert result == False


def test_isEditable_calls_compute_status_with_event_times(mock_event):
    """Test that isEditable passes event times to compute_status"""
    from flask_app.models.voteModels import Vote
    
    with patch('flask_app.models.voteModels.Events.compute_status') as mock_compute:
        mock_compute.return_value = 'Open'
        
        Vote.isEditable(mock_event)
        
        # Verify compute_status was called with the event's times
        mock_compute.assert_called_once_with(mock_event.start_time, mock_event.end_time)


# ============================================================================
# INTEGRATION TESTS - Test complete voting workflows
# ============================================================================

def test_voting_workflow_cast_check_change(mock_db_connection, sample_vote_data):
    """Test complete workflow: cast vote, check it exists, then change it"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Step 1: Cast vote
    mock_query.return_value = 1
    vote_id = Vote.castVote({'vote_user_id': 5, 'vote_option_id': 10})
    assert vote_id == 1
    
    # Step 2: Check vote exists
    mock_query.return_value = [sample_vote_data]
    existing_vote = Vote.getByUserAndEvent({'user_id': 5, 'event_id': 100})
    assert existing_vote is not None
    assert existing_vote.vote_option_id == 10
    
    # Step 3: Change vote
    mock_query.return_value = True
    changed = Vote.changeVote({'user_id': 5, 'event_id': 100, 'new_option_id': 15})
    assert changed == True
    
    # Verify query_db was called 3 times
    assert mock_query.call_count == 3


def test_voting_workflow_cast_and_delete(mock_db_connection):
    """Test workflow: cast vote then delete it"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Cast vote
    mock_query.return_value = 1
    Vote.castVote({'vote_user_id': 5, 'vote_option_id': 10})
    
    # Delete vote
    mock_query.return_value = True
    deleted = Vote.deleteVote({'user_id': 5, 'event_id': 100})
    assert deleted == True
    
    assert mock_query.call_count == 2


def test_get_recent_votes_integration(mock_db_connection, sample_recent_votes_data):
    """Test that recent votes correctly formats data with event status"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock(return_value=sample_recent_votes_data)
    mock_db_connection.return_value.query_db = mock_query
    
    with patch('flask_app.models.voteModels.Events.compute_status') as mock_compute:
        # First vote: Open, Second vote: Closed
        mock_compute.side_effect = ['Open', 'Closed']
        
        result = Vote.getRecentForUser({'user_id': 5, 'limit': 10})
        
        # Verify both votes are formatted correctly
        assert len(result) == 2
        assert result[0]['status'] == 'open'
        assert result[1]['status'] == 'closed'
        assert all(key in result[0] for key in ['vote_id', 'event_name', 'date', 'status', 'vote_type', 'event_id'])


def test_getStatsForUser_returns_complete_statistics(mock_db_connection):
    """Test that getStatsForUser returns all required statistics"""
    from flask_app.models.voteModels import Vote
    from datetime import datetime
    
    # Mock the three database queries
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # Setup return values for the three queries
    mock_query.side_effect = [
        # Query 1: total votes and last vote date
        [{'total_votes': 5, 'last_vote_date': datetime(2025, 11, 15, 10, 30, 0)}],
        # Query 2: events participated
        [{'events_participated': 3}],
        # Query 3: total available events
        [{'total_available': 10}]
    ]
    
    result = Vote.getStatsForUser({'user_id': 5})
    
    # Verify structure
    assert 'total_votes' in result
    assert 'participation_rate' in result
    assert 'events_participated' in result
    assert 'last_vote_date' in result
    
    # Verify values
    assert result['total_votes'] == 5
    assert result['events_participated'] == 3
    assert result['participation_rate'] == 30.0  # 3/10 * 100
    assert 'Nov' in result['last_vote_date']
    
    # Verify query_db was called 3 times
    assert mock_query.call_count == 3


def test_getStatsForUser_handles_no_votes(mock_db_connection):
    """Test that getStatsForUser handles users with no votes"""
    from flask_app.models.voteModels import Vote
    
    mock_query = Mock()
    mock_db_connection.return_value.query_db = mock_query
    
    # User has never voted
    mock_query.return_value = [{'total_votes': 0, 'last_vote_date': None}]
    
    result = Vote.getStatsForUser({'user_id': 5})
    
    assert result['total_votes'] == 0
    assert result['last_vote_date'] == 'Never'
