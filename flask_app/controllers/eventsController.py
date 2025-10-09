from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events
from flask_app.models.userModels import User
from datetime import datetime


def _parse_datetime(value):
    """Try to parse a DB value into a naive datetime. Return None if impossible."""
    if not value:
        return None
    # If it's already a datetime object
    if isinstance(value, datetime):
        return value
    # Try common string formats
    fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
    for f in fmts:
        try:
            return datetime.strptime(value, f)
        except Exception:
            continue
    # Fallback: try fromisoformat
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _compute_status(start_raw, end_raw):
    now = datetime.now()
    start = _parse_datetime(start_raw)
    end = _parse_datetime(end_raw)

    if not start and not end:
        return 'Unknown'
    if start and end:
        if now < start:
            return 'Waiting'
        if now > end:
            return 'Closed'
        return 'Open'
    if start and not end:
        return 'Waiting' if now < start else 'Open'
    if end and not start:
        return 'Closed' if now > end else 'Open'
    return 'Unknown'

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
    return render_template('eventForms.html')

@app.route('/createEventRoute', methods=['POST'])
def createEventRoute():
    user = User.getUserByID({'user_id': session['user_id']})
    print("THIS IS THE ID",session['user_id'])
    first_name = user.first_name
    data = {
        'title': request.form['title'],
        'description': request.form['description'],
        'start_time': request.form['start_time'],
        'end_time': request.form['end_time'],
        'created_byFK': session['user_id'],
        # status will be computed below
    }
    # compute initial status from provided times
    try:
        data['status'] = _compute_status(data.get('start_time'), data.get('end_time'))
    except Exception:
        data['status'] = 'Unknown'

    Events.createEvent(data)
    return redirect(url_for('eventList'))

def is_logged_in():
    return 'user_id' in session

@app.route('/eventList')
def eventList():
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    allEvents = Events.getAll()
    # Compute server-side status for each event so templates have a reliable value
    for ev in allEvents:
        try:
            ev.status = _compute_status(ev.start_time, ev.end_time)
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
        dt = _parse_datetime(ev.start_time)
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
            r.status = _compute_status(r.start_time, r.end_time)
        except Exception:
            r.status = 'Unknown'

    return render_template('singleEvent.html', event=event, recommendations=recs, **user_data)