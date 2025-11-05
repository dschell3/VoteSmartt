from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events
from flask_app.models.userModels import User
from datetime import datetime

# moved compute_status and _parse_datetime to Events model for reuse
# so other controllers can call it too

def get_user_session_data():
    """Helper function to get user session data for templates"""
    logged_in = "user_id" in session
    user_data = {'logged_in': logged_in}
    
    if logged_in:
        user_id = session["user_id"]
        user = User.getUserByID({"user_id": user_id})
        if user:
            user_data.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'user_id': user.user_id,
                'created_at': user.created_at
            })
    
    return user_data

def is_logged_in():
    return 'user_id' in session

def require_login(redirect_to="/unauthorized"):
    """Helper function to check if user is logged in"""
    if "user_id" not in session:
        if redirect_to == "/login":
            flash("Please log in to access this page")
        else:
            flash("Should you really be here? Please sign in to continue.")
        return redirect_to
    
    user_id = session["user_id"]
    user = User.getUserByID({"user_id": user_id})
    if not user:
        session.clear()
        flash("Session expired. Please log in again.")
        return redirect_to
    
    return None  # No redirect needed


@app.route('/admin2')
def adminPage():
    # Require login to access the event creation page and pass session user data
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    return render_template('eventForms.html', **user_data)

@app.route('/createEventRoute', methods=['POST'])
def createEventRoute():
    # 001 - Added comprehensive server-side validation for form submission
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user = User.getUserByID({'user_id': session['user_id']})
    print("THIS IS THE ID",session['user_id'])
    first_name = user.first_name
    
    # Server-side validation
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    candidate_descs = request.form.getlist('candidate_descs[]')
    
    # Validation - check in priority order and show only the most important error
    error_message = None
    
    # Priority 1: Event name (most important)
    if not title:
        error_message = 'Please enter an event name'
    elif len(title) > 255:
        error_message = 'Event name is too long (maximum 255 characters)'
    
    # Priority 2: Start date (if name is OK)
    elif not start_time:
        error_message = 'Please select a start date'
    
    # Priority 3: End date (if name and start date are OK)
    elif not end_time:
        error_message = 'Please select an end date'
    
    # Priority 4: Date validation (if all dates are provided)
    elif start_time and end_time:
        try:
            start_date = datetime.strptime(start_time, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_time, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if start_date < today:
                error_message = 'Start date cannot be in the past'
            elif end_date < start_date:
                error_message = 'End date cannot be before start date'
            elif start_date.year > datetime.now().year + 10 or end_date.year > datetime.now().year + 10:
                error_message = 'Event dates cannot be more than 10 years in the future'
                
        except ValueError:
            error_message = 'Invalid date format'
    
    # Priority 5: Description length (optional field, only check if provided)
    elif description and len(description) > 1000:
        error_message = 'Event description is too long (maximum 1000 characters)'
    
    # Priority 5: Candidates (lower priority)
    else:
        valid_candidates = [c.strip() for c in candidate if c.strip()]
        if len(valid_candidates) < 2:
            error_message = 'Please add at least 2 candidates'
        else:
            # Check candidate length
            for candidate in valid_candidates:
                if len(candidate) > 100:
                    error_message = f'Candidate name "{candidate}" is too long (maximum 100 characters)'
                    break
    
    # If there's a validation error, show only one message
    if error_message:
        flash(error_message, 'error')
        return redirect('/admin2')
    
    # All validation passed, create the event
    data = {
        'title': title,
        'description': description,
        'start_time': start_time,
        'end_time': end_time,
        'created_byFK': session['user_id'],
        # status will be computed below
    }
    
    # compute initial status from provided times
    try:
        data['status'] = Events.compute_status(data.get('start_time'), data.get('end_time'))
    except Exception:
        data['status'] = 'Unknown'

    # Create the event
    try:
        Events.createEvent(data)
        flash('Event created successfully!', 'success')
    except Exception as e:
        flash('Error creating event. Please try again.', 'error')
        return redirect('/admin2')
    
    return redirect(url_for('eventList'))

@app.route('/eventList')
def eventList():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    allEvents = Events.getAllWithCreators()
    # Compute server-side status for each event so templates have a reliable value
    for ev in allEvents:
        try:
            ev.status = Events.compute_status(ev.start_time, ev.end_time)
        except Exception:
            ev.status = 'Unknown'
    # Sort events so that Open events appear first, then Waiting, then Closed.
    # Within each status, sort by start_time ascending (earliest first).
    status_priority = {
        'Open': 0,
        'Waiting': 1,
        'Closed': 2,
        'Unknown': 3
    }

    def _safe_parse_start(ev):
        """Return a datetime for sorting; None becomes far-future to push it to the end."""
        dt = Events.parse_datetime(ev.start_time)
        if dt is None:
            # Use a far-future date so events without start_time appear after dated ones
            return datetime.max
        return dt

    # sort by (status priority, start_time)
    try:
        allEvents.sort(key=lambda e: (status_priority.get(getattr(e, 'status', 'Unknown'), 3), _safe_parse_start(e)))
    except Exception:
        # If something goes wrong with sorting, fallback to the original order
        pass

    return render_template('eventList.html', allEvents=allEvents, **user_data)


@app.route("/events/<int:event_id>/delete", methods=['POST'])
def deleteEvent(event_id):
    """Delete an event - only creators or admins can delete events"""
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    # Get current user data
    user_id = session.get('user_id')
    user = User.getUserByID({'user_id': user_id})
    
    # Get the event to check ownership
    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect("/events")
    
    # Check if user is the creator or an admin
    if event.created_byFK != user_id and not (user and user.can_manage_events()):
        flash("You can only delete events that you created.", "error")
        return redirect("/events")
    
    # Attempt to delete the event
    try:
        result = Events.deleteEvent({"event_id": event_id})
        if result:
            flash(f"Event '{event.title}' has been successfully deleted.", "success")
        else:
            flash("Failed to delete the event. Please try again.", "error")
    except Exception as e:
        flash("An error occurred while deleting the event.", "error")
        print(f"Delete event error: {e}")  # For debugging
    
    return redirect("/events")


@app.route("/event/<int:event_id>")
def singleEvent(event_id):
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    event = Events.getOne({"event_id": event_id})
    # gather recommendations (simple next 3 upcoming events excluding current)
    try:
        recs = Events.getRecommendations({ 'event_id': event_id })
    except Exception:
        recs = []

    # compute statuses for recommendations
    for r in recs:
        try:
            r.status = Events.compute_status(r.start_time, r.end_time)
        except Exception:
            r.status = 'Unknown'

    return render_template('singleEvent.html', event=event, recommendations=recs, **user_data)