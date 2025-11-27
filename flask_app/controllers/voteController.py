'''
==============================================================================
Vote Controller - Handles HTTP routes for voting operations
==============================================================================

This module provides Flask route handlers for casting, changing, and retracting
votes within the VoteSmartt system. 

Routes:
    - POST /vote/cast    : Cast a new vote or update an existing vote
    - POST /vote/change  : Alias for /vote/cast (semantic clarity)
    - POST /vote/delete  : Retract (delete) an existing vote

Model Dependencies:
    - Vote: Core voting operations (castVote, changeVote, deleteVote, getByUserAndEvent)
    - Events: Event retrieval and ownership checking (getOne, isCreatedBy)
    - Option: Validates option belongs to event (getByEventId)
    - compute_status: Determines if event is Open/Waiting/Closed

Business Rules Enforced:
    - User must be logged in to vote
    - Admins (isAdmin=1) cannot cast votes
    - Event creators cannot vote on their own events
    - Votes can only be cast/changed/deleted when event status is 'Open'
    - Each user can only have ONE vote per event (update if exists)
    - Selected option must belong to the target event
'''

from flask import request, redirect, flash
from flask_app import app
from flask_app.models.optionModels import Option
from flask_app.models.voteModels import Vote
from flask_app.models.eventsModels import Events, compute_status
from flask_app.utils.helpers import require_login, require_voter, get_current_user

# =============================================================================
# CAST/UPDATE OPERATIONS - Submit or update a vote
# =============================================================================

@app.route('/vote/cast', methods=['POST'])
def cast_vote():
    """
    Cast or update a vote on an event.
    
    Process:
        1. Verify user is logged in (require_login)
        2. Verify user is a voter, not admin (require_voter)
        3. Get user object once (get_current_user)
        4. Validate form data (event_id, option_id)
        5. Verify event exists and is open
        6. Verify user is not the event creator
        7. Validate selected option belongs to event
        8. Check if user already voted (if yes, update; if no, create new)
        9. Cast/Update vote

    Redirects:
        - /eventList: On auth failure or missing data
        - /event/<event_id>: On success or event-specific errors
    """
    # 1. Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url) # Redirect if not logged in
    
    # 2. Ensure user is not admin
    if require_voter():
        return redirect('/eventList')

    # 3. Get/Instantiate current user
    user = get_current_user()

    # Get form data
    event_id = request.form.get('event_id')
    option_id = request.form.get('option_id')

    # 4. Validate form data
    if not event_id or not option_id:
        flash("Missing event or option.", "error")
        return redirect('/eventList') 

    # Normalize to ints and validate
    try:
        event_id = int(event_id)
        option_id = int(option_id)
    except Exception:
        flash("Invalid vote data.", "error")
        return redirect('/eventList')

    # 5a. Ensure event exists
    event = Events.getOne({'event_id': event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect('/eventList')
    
    # 5b. Ensure event is open for voting
    if compute_status(event.start_time, event.end_time) != "Open":
        flash("Voting is closed for this event.", "error")
        return redirect(f"/event/{event_id}")

    # 6. Event creators are treated as admins for their events and cannot vote
    if event.isCreatedBy(user):
        flash("Event creators cannot vote on their own events.", "error")
        return redirect(f"/event/{event_id}")

    # 7. Extra safety: ensure the option belongs to this event
    try:
        valid_options = Option.getByEventId({'event_id': event_id})
        valid_ids = {o.option_id for o in valid_options}
        if option_id not in valid_ids:
            flash("Selected option is not valid for this event.", "error")
            return redirect(f"/event/{event_id}")
    except Exception:
        # If validation fails unexpectedly, continue without blocking
        pass

    # 8. Check if user has already voted in this event, if they have update their vote
    existing = Vote.getByUserAndEvent({
        'user_id': user.user_id,
        'event_id': event_id
    })
    
    # 9. Cast/Update Vote
    if existing:
        # Update vote
        Vote.changeVote({
            'user_id': user.user_id,
            'event_id': event_id,
            'new_option_id': option_id
        })
        flash("Your vote was updated.", "success")
    else:
        # Cast new vote
        Vote.castVote({
            'vote_user_id': user.user_id, 
            'vote_option_id': option_id
        })
        flash("Your vote has been submitted.", "success")
    return redirect(f"/event/{event_id}")

# =============================================================================
# CHANGE OPERATIONS - Alias route for clarity
# =============================================================================

@app.route('/vote/change', methods=['POST'])
def change_vote():
    """
    Alias route for changing a vote.
    
    Process:
        Delegates entirely to cast_vote()
    """
    return cast_vote()

# =============================================================================
# DELETE/RETRACT OPERATIONS - Remove a user's vote
# =============================================================================

@app.route('/vote/delete', methods=['POST'])
def delete_vote():
    """
    Delete (retract) a user's vote on an event.
    
    Process:
        1. Verify user is logged in (require_login)
        2. Verify user is a voter, not admin (require_voter)
        3. Get user object (get_current_user)
        4. Validate form data (event_id)
        5. Verify event exists
        6. Verify user is not the event creator (defensive)
        7. Verify event is still open (votes can only be retracted while open)
        8. Delete the vote and provide feedback
    
    Redirects:
        - /eventList: On auth failure or missing data
        - /event/<event_id>: On success or event-specific errors
    """
    # 1. Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # 2. Ensure user is not admin
    if require_voter():
        return redirect('/eventList')
    
    # 3. Get/Instantiate current user
    user = get_current_user()

    # 4. Get + Validate form data
    event_id = request.form.get('event_id')
    if not event_id:
        flash("Missing event.", "error")
        return redirect('/eventList')

    # 5. Ensure event exists
    event = Events.getOne({'event_id': event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect('/eventList')
    
    # 6. This check is mostly defensive since creators shouldn't have votes to delete
    if event.isCreatedBy(user):
        flash("Event creators cannot vote on their own events.", "error")
        return redirect(f"/event/{event_id}")

    # 7. Ensure event is still open for voting
    if compute_status(event.start_time, event.end_time) != "Open":
        flash("This event has closed; votes cannot be retracted.", "error")
        return redirect(f"/event/{event_id}")

    # 8. Delete the vote
    success = Vote.deleteVote({
        'user_id': user.user_id,
        'event_id': event_id
    })
    # Provide feedback
    if success:
        flash("Your vote has been retracted.", "success")
    else:
        flash("Could not retract your vote.", "error")

    # Always redirect back to the event page to refresh state
    return redirect(f"/event/{event_id}")

