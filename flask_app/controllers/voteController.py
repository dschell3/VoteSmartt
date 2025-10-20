from flask import request, redirect, flash, session
from flask_app import app
from flask_app.models.userModels import User
from flask_app.models.voteModels import Vote
from flask_app.models.eventsModels import Events
from datetime import datetime

# Local helper, same style as other controllers
def require_login(redirect_to="/unauthorized"):
    if "user_id" not in session:
        flash("Should you really be here? Please sign in to continue.")
        return redirect_to
    return None

# block to ensure admins cannot vote
def require_not_admin():
    u = User.getUserByID({'user_id': session['user_id']})
    # User.getUserByID returns a User instance; it includes isAdmin in your model.
    if u and getattr(u, "isAdmin", 0) == 1:
        flash("Administrators cannot vote on events.", "error")
        return True
    return False

@app.route('/vote/cast', methods=['POST'])
def cast_vote():
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url) # Redirect if not logged in
    
    # Ensure user is not admin
    if require_not_admin():
        return redirect('/eventList')

    # Get form data
    event_id = request.form.get('event_id')
    option_id = request.form.get('option_id')

    if not event_id or not option_id:
        flash("Missing event or option.", "error")
        return redirect('/eventList') 

    event = Events.getOne({'event_id': event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect('/eventList')
    
    # Ensure event is open for voting
    if not Events.isOpen(event.start_time, event.end_time, datetime.now()):
        flash("Voting is closed for this event.", "error")
        return redirect(f"/event/{event_id}")

    # Check if user has already voted in this event, if they have update their vote
    existing = Vote.getByUserAndEvent({'user_id': session['user_id'], 'event_id': event_id})
    if existing:
        updated = Vote.changeVote({
            'user_id': session['user_id'],
            'event_id': event_id,
            'new_option_id': option_id
        })
        if updated:
            flash("Your previous vote was updated.", "success")
        else:
            flash("Could not update your vote. Please try again.", "error")
        return redirect(f"/event/{event_id}")

    # Had not voted yet, cast new vote
    Vote.castVote({'vote_user_id': session['user_id'], 'vote_option_id': option_id})
    flash("Your vote has been submitted.", "success")
    return redirect(f"/event/{event_id}")


@app.route('/vote/change', methods=['POST'])
def change_vote():
    # Is this needed? Ask Jang, 'vote/cast' already handles changing votes.
    # Just maintains two routes for clarity? I would remove this unless needed.
    return cast_vote()

@app.route('/vote/delete', methods=['POST'])
def delete_vote():
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # Ensure user is not admin
    if require_not_admin():
        return redirect('/eventList')
    
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
    if not Events.isOpen(event.start_time, event.end_time, datetime.now()):
        flash("This event has closed; votes cannot be retracted.", "error")
        return redirect(f"/event/{event_id}")

    # Delete the vote
    result = Vote.deleteVote({'user_id': session['user_id'], 'event_id': event_id})
    if result:
        flash("Your vote has been retracted.", "success")
    else:
        flash("Could not retract your vote.", "error")

    return redirect(f"/event/{event_id}")

# Additional vote-related routes can be added here