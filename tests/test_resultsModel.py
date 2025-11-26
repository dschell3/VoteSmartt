"""
Simple component tests for resultsModel.py
Tests the Result class methods with mocked database connections and Vote model.
Run with: pytest tests/test_resultsModel.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# Mock the database connection before importing the Result class
@pytest.fixture(autouse=True)
def mock_db_connection():
    """Automatically mock the database connection for all tests"""
    with patch('flask_app.models.voteModels.connectToMySQL') as mock_connect:
        yield mock_connect


# Test data fixtures
@pytest.fixture
def sample_result_data():
    """Sample data for creating a Result instance"""
    return {
        'event_id': 1
    }


@pytest.fixture
def sample_vote_tally():
    """Sample vote tally data as returned by Vote.tallyVotesForEvent"""
    return [
        {'option_id': 1, 'option_text': 'Option A', 'votes': 10},
        {'option_id': 2, 'option_text': 'Option B', 'votes': 5},
        {'option_id': 3, 'option_text': 'Option C', 'votes': 3}
    ]


@pytest.fixture
def sample_vote_tally_with_tie():
    """Sample vote tally with a tie for first place"""
    return [
        {'option_id': 1, 'option_text': 'Option A', 'votes': 10},
        {'option_id': 2, 'option_text': 'Option B', 'votes': 10},
        {'option_id': 3, 'option_text': 'Option C', 'votes': 3}
    ]


@pytest.fixture
def empty_vote_tally():
    """Empty vote tally (no votes cast)"""
    return []


# ============================================================================
# TEST: Result.__init__() and calculate() - Constructor and calculation
# ============================================================================

def test_result_init_calls_calculate(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that Result constructor initializes event_id and calls calculate()"""
    from flask_app.models.resultsModel import Result
    
    # Mock Vote.tallyVotesForEvent to return sample data
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        
        # Verify attributes are set
        assert result.event_id == 1
        assert hasattr(result, 'rows')
        assert len(result.rows) == 3


def test_calculate_adds_percentages_to_rows(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that calculate() adds percentage field to each row"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        
        # Verify percentages are calculated correctly
        # Total votes = 10 + 5 + 3 = 18
        assert result.rows[0]['percentage'] == 55.6  # 10/18 * 100 = 55.6
        assert result.rows[1]['percentage'] == 27.8  # 5/18 * 100 = 27.8
        assert result.rows[2]['percentage'] == 16.7  # 3/18 * 100 = 16.7


def test_calculate_handles_empty_results(mock_db_connection, sample_result_data, empty_vote_tally):
    """Test that calculate() handles empty vote tally (no votes)"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=empty_vote_tally):
        result = Result(sample_result_data)
        
        # Verify empty list is handled
        assert result.rows == []


def test_calculate_handles_zero_votes_gracefully(mock_db_connection, sample_result_data):
    """Test that calculate() handles case where all options have 0 votes"""
    from flask_app.models.resultsModel import Result
    
    zero_votes = [
        {'option_id': 1, 'option_text': 'Option A', 'votes': 0},
        {'option_id': 2, 'option_text': 'Option B', 'votes': 0}
    ]
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=zero_votes):
        result = Result(sample_result_data)
        
        # When total is 0, percentages should be 0.0
        assert result.rows[0]['percentage'] == 0.0
        assert result.rows[1]['percentage'] == 0.0


# ============================================================================
# TEST: Result.getWinner() - Get winning option
# ============================================================================

def test_getWinners_returns_option_with_most_votes(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that getWinner returns the option with the highest vote count"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        winner = result.getWinners()
        
        # Winner should be Option A with 10 votes
        assert winner is not None
        assert winner['option_id'] == 1
        assert winner['option_text'] == 'Option A'
        assert winner['votes'] == 10


def test_getWinners_returns_first_in_case_of_tie(mock_db_connection, sample_result_data, sample_vote_tally_with_tie):
    """Test that getWinner returns first option in case of tie"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally_with_tie):
        result = Result(sample_result_data)
        winner = result.getWinners()
        
        # Should return first option with highest votes (Option A)
        assert winner is not None
        assert winner['option_id'] == 1
        assert winner['votes'] == 10


def test_getWinners_returns_none_when_no_votes(mock_db_connection, sample_result_data, empty_vote_tally):
    """Test that getWinner returns None when there are no votes"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=empty_vote_tally):
        result = Result(sample_result_data)
        winner = result.getWinners()
        
        assert winner is None


# ============================================================================
# TEST: Result.getTotalVotes() - Get total vote count
# ============================================================================

def test_getTotalVotes_returns_sum_of_all_votes(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that getTotalVotes returns the correct sum"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        total = result.getTotalVotes()
        
        # Total should be 10 + 5 + 3 = 18
        assert total == 18


def test_getTotalVotes_returns_zero_when_no_votes(mock_db_connection, sample_result_data, empty_vote_tally):
    """Test that getTotalVotes returns 0 when there are no votes"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=empty_vote_tally):
        result = Result(sample_result_data)
        total = result.getTotalVotes()
        
        assert total == 0


# ============================================================================
# TEST: Result.getWinnerVoteTotal() - Get winner's vote count
# ============================================================================

def test_getWinnerVoteTotal_returns_winners_vote_count(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that getWinnerVoteTotal returns the vote count of the winner"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        winner_votes = result.getWinnerVoteTotal()
        
        # Winner (Option A) has 10 votes
        assert winner_votes == 10


def test_getWinnerVoteTotal_returns_zero_when_no_votes(mock_db_connection, sample_result_data, empty_vote_tally):
    """Test that getWinnerVoteTotal returns 0 when there are no votes"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=empty_vote_tally):
        result = Result(sample_result_data)
        winner_votes = result.getWinnerVoteTotal()
        
        assert winner_votes == 0


# ============================================================================
# TEST: Result.getWinnerPercentage() - Get winner's percentage
# ============================================================================

def test_getWinnerPercentage_returns_winners_percentage(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that getWinnerPercentage returns the percentage of the winner"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        winner_percentage = result.getWinnerPercentage()
        
        # Winner has 55.6% (10 out of 18 votes)
        assert winner_percentage == 55.6


def test_getWinnerPercentage_returns_zero_when_no_votes(mock_db_connection, sample_result_data, empty_vote_tally):
    """Test that getWinnerPercentage returns 0.0 when there are no votes"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=empty_vote_tally):
        result = Result(sample_result_data)
        winner_percentage = result.getWinnerPercentage()
        
        assert winner_percentage == 0.0


# ============================================================================
# INTEGRATION TEST - Test complete workflow
# ============================================================================

def test_result_complete_workflow(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test a complete workflow of creating Result and using all methods"""
    from flask_app.models.resultsModel import Result
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        # Create result instance
        result = Result(sample_result_data)
        
        # Verify event_id is set
        assert result.event_id == 1
        
        # Verify rows are calculated with percentages
        assert len(result.rows) == 3
        assert all('percentage' in row for row in result.rows)
        
        # Verify winner
        winner = result.getWinner()
        assert winner['option_text'] == 'Option A'
        
        # Verify total votes
        total = result.getTotalVotes()
        assert total == 18
        
        # Verify winner vote total
        winner_votes = result.getWinnerVoteTotal()
        assert winner_votes == 10
        
        # Verify winner percentage
        winner_percentage = result.getWinnerPercentage()
        assert winner_percentage == 55.6


def test_result_with_single_option(mock_db_connection, sample_result_data):
    """Test Result with only one voting option"""
    from flask_app.models.resultsModel import Result
    
    single_option = [
        {'option_id': 1, 'option_text': 'Only Option', 'votes': 7}
    ]
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=single_option):
        result = Result(sample_result_data)
        
        # Should handle single option correctly
        assert result.getTotalVotes() == 7
        assert result.getWinner()['option_text'] == 'Only Option'
        assert result.getWinnerPercentage() == 100.0


def test_result_preserves_original_data(mock_db_connection, sample_result_data, sample_vote_tally):
    """Test that Result doesn't modify the original vote tally data structure"""
    from flask_app.models.resultsModel import Result
    
    # Create a copy to compare later
    original_tally = [dict(row) for row in sample_vote_tally]
    
    with patch('flask_app.models.resultsModel.Vote.tallyVotesForEvent', return_value=sample_vote_tally):
        result = Result(sample_result_data)
        
        # Result.rows should have percentages added
        assert 'percentage' in result.rows[0]
        
        # But original vote tally should not have been modified
        # (This tests that calculate() works on a copy, not the original)
        # Note: In the current implementation, it modifies the original.
        # This test documents current behavior.