from flask import request, redirect, flash, session
from flask_app import app
from flask_app.models.userModels import User
from flask_app.models.voteModels import Vote
from flask_app.models.eventsModels import Events
from datetime import datetime
from flask_app.utils.helpers import require_login, require_voter, get_current_user

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
    6. Check if user already voted (if yes, update; if no, create new)
    """
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url) # Redirect if not logged in
    
    # Ensure user is not admin
    if require_voter():
        return redirect('/eventList')

    # Get/Instantiate current user
    user = get_current_user()

    # Get form data
    event_id = request.form.get('event_id')
    option_id = request.form.get('option_id')

    # Validate form data
    if not event_id or not option_id:
        flash("Missing event or option.", "error")
        return redirect('/eventList') 

    # Ensure event exists
    event = Events.getOne({'event_id': event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect('/eventList')
    
    # Ensure event is open for voting
    if Events.compute_status(event.start_time, event.end_time) != "Open":
        flash("Voting is closed for this event.", "error")
        return redirect(f"/event/{event_id}")

    # Check if user has already voted in this event, if they have update their vote
    existing = Vote.getByUserAndEvent({
        'user_id': user.user_id,
        'event_id': event_id
    })
    
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


@app.route('/vote/change', methods=['POST'])
def change_vote():
    #'vote/cast' already handles changing votes.
    # Just maintains two routes for clarity.
    return cast_vote()

@app.route('/vote/delete', methods=['POST'])
def delete_vote():
    """
    Delete (retract) a user's vote on an event.
    """
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # Ensure user is not admin
    if require_voter():
        return redirect('/eventList')
    
    # Get/Instantiate current user
    user = get_current_user()

    # Get form data
    event_id = request.form.get('event_id')
    if not event_id:
        flash("Missing event.", "error")
        return redirect('/eventList')

    # Ensure event exists
    event = Events.getOne({'event_id': event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect('/eventList')

    # Ensure event is still open for voting
    if Events.compute_status(event.start_time, event.end_time) != "Open":
        flash("This event has closed; votes cannot be retracted.", "error")
        return redirect(f"/event/{event_id}")

    # Delete the vote
    success = Vote.deleteVote({
        'user_id': user.user_id,
        'event_id': event_id
    })
    
    if success:
        flash("Your vote has been retracted.", "success")
    else:
        flash("Could not retract your vote.", "error")

# Additional vote-related routes can be added here