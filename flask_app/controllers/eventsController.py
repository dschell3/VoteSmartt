'''
==============================================================================
Events Controller - Handles HTTP routes for event/election management
==============================================================================

This module provides Flask route handlers for creating, viewing, editing, and
deleting voting events (polls, surveys, elections, competitions) within the
VoteSmartt system. It also handles candidate/option management for events.

Routes (organized by category):

    EVENT CREATION ROUTES:
        - GET  /admin2              : Display event creation form
        - POST /createEventRoute    : Process new event creation with candidates

    EVENT LISTING & VIEWING ROUTES:
        - GET  /eventList           : Display all events sorted by status/time
        - GET  /events              : Legacy alias, redirects to /eventList
        - GET  /event/<event_id>    : Display single event with voting/results

    EVENT EDIT ROUTES:
        - GET  /events/<id>/edit    : Display edit form (fields vary by status)
        - POST /events/<id>/edit    : Process event updates and candidate changes

    EVENT DELETE ROUTES:
        - POST /events/<id>/delete  : Delete event (creator/admin only)

Model Dependencies:
    - Events: Event CRUD operations, status computation, creator info
    - Option: Candidate/option management for events
    - Vote: Check existing user votes for pre-selection
    - Result: Calculate and display voting results after event closes

Business Rules Enforced:
    - All event routes require authentication (no anonymous access)
    - Only event creators (or admins) can edit/delete their events
    - Event editability varies by status:
        * Waiting: All fields editable (title, description, times, candidates)
        * Open: Only end_time and description editable (voting in progress)
        * Closed: Only description editable (historical record)
    - Events require at least 2 candidates/options for voting
    - Event creators cannot vote on their own events
    - Results only display after event status is 'Closed'

Timezone Handling:
    - Frontend sends local Pacific timezone via datetime-local inputs
    - Backend stores and compares times in Pacific timezone
    - Status computed server-side using get_now_pacific() for consistency
'''

from flask import flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events, compute_status, parse_datetime, get_now_pacific
from flask_app.models.optionModels import Option
from flask_app.models.voteModels import Vote
from flask_app.models.resultsModel import Result
from flask_app.utils.helpers import require_login, get_current_user, get_user_session_data
from flask_app.models.userModels import User
from flask_app.utils.validators import validate_event_title, validate_event_description, validate_candidate_name

# =============================================================================
# EVENT CREATION ROUTES - Create new voting events
# =============================================================================

@app.route('/admin2')
def adminPage():
    """
    Display the event creation form page.
    
    Redirects:
        - /login: If user is not authenticated
    """
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    user_data['edit_mode'] = False  # Indicate creation mode
    
    return render_template('eventForms.html', **user_data)

@app.route('/createEventRoute', methods=['POST'])
def createEventRoute():
    """
    Handle new event creation with comprehensive validation.
    
    Process:
        1. Verify user is logged in
        2. Extract and sanitize form data (title, description, times, candidates)
        3. Validate fields in priority order (show only first error):
           a. Event title (required, max 45 chars)
           b. Start time (required, must be future)
           c. End time (required, must be after start)
           d. Candidates (minimum 2 required, each validated)
        4. Normalize datetime strings to 'YYYY-MM-DD HH:MM:SS' format
        5. Compute initial event status from times
        6. Create event record in database
        7. Create associated candidate/option records
        8. Deduplicate candidates while preserving order
    
    Redirects:
        - /admin2: On validation errors (with flash messages)
        - /eventList: On successful creation
    """
    # 1. Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
        
    # 2. Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    start_time_local = request.form.get('start_time', '').strip()  # LOCAL time from datetime-local
    end_time_local = request.form.get('end_time', '').strip()      # LOCAL time from datetime-local
    candidate = request.form.getlist('candidates[]')

    # Build candidate list early so it's always available (avoid elif-chain scoping issues)
    valid_candidates = [c.strip() for c in candidate if (c or '').strip()]
    
    # 3. Validation - check in priority order and show only the most important error
    error_message = None
    
    # Priority 1: Event name - Use centralized validator
    error_message = validate_event_title(title)

    # Priority 2: Event description validation
    if not error_message and description:
        error_message = validate_event_description(description)

    # Priority 3: Start date (if name is OK)
    elif not start_time_local:
        error_message = 'Please select a start date'
    
    # Priority 4: End date (if name and start date are OK)
    elif not end_time_local:
        error_message = 'Please select an end date'
    
    # Priority 5: Date validation (if all dates are provided)
    elif start_time_local and end_time_local:
        try:
            # Use centralized parse_datetime from model
            start_dt = parse_datetime(start_time_local)
            end_dt = parse_datetime(end_time_local)
            if not start_dt or not end_dt:
                raise ValueError('Invalid datetime format')

            # Use centralized get_now_pacific - all times are naive Pacific
            now = get_now_pacific()

            # Check if start time is in the past
            if start_dt < now:
                error_message = 'Start time cannot be in the past'

            if not error_message:
                if end_dt <= start_dt:
                    error_message = 'End time cannot be before or equal to start time'

            # 10-year sanity window
            if not error_message:
                if start_dt.year > now.year + 10 or end_dt.year > now.year + 10:
                    error_message = 'Event dates cannot be more than 10 years in the future'

        except ValueError:
            error_message = 'Invalid date format'
        
    # Priority 6: Description length (optional field, only check if provided)
    if not error_message and description and len(description) > 1000:
        error_message = 'Event description is too long (maximum 1000 characters)'

    # Priority 7: Candidates (always validated once earlier checks pass)
    if not error_message:
        if len(valid_candidates) < 2:
            error_message = 'Please add at least 2 candidates'
        else:
            # Validate each candidate name using centralized validator
            for cand in valid_candidates:
                cand_error = validate_candidate_name(cand)
                if cand_error:
                    error_message = cand_error
                    break
            
            # Check for duplicate candidates (case-insensitive)
            if not error_message:
                seen = set()
                for cand in valid_candidates:
                    cand_lower = cand.lower()
                    if cand_lower in seen:
                        error_message = f'Duplicate candidate "{cand}" is not allowed. Each candidate must have a unique name.'
                        break
                    seen.add(cand_lower)

    # If there's a validation error, show only one message
    if error_message:
        # Debug logging for validation failures to aid development
        try:
            print(f"[CREATE EVENT] Validation error: {error_message}")
            print(f"[CREATE EVENT] Submitted title='{title}' start='{start_time_local}' end='{end_time_local}' candidates={valid_candidates}")
        except Exception:
            pass
        flash(error_message, 'error')
        return redirect('/admin2')
    
    # 4. Normalize datetime format (from datetime-local) - Keep in LOCAL timezone
    def normalize_datetime_local(val: str):
        if not val:
            return ''
        # datetime-local format: YYYY-MM-DDTHH:MM
        val = val.strip().replace('T', ' ')
        if len(val) == 16:  # YYYY-MM-DD HH:MM
            val = val + ':00'
        return val

    normalized_start = normalize_datetime_local(start_time_local)
    normalized_end = normalize_datetime_local(end_time_local)

    # 5. All validation passed, create the event data dictionary
    data = {
        'title': title,
        'description': description,
        'start_time': normalized_start,
        'end_time': normalized_end,
        'created_byFK': session['user_id'],
        # status will be computed below
    }
    
    # compute initial status from provided times
    try:
        data['status'] = compute_status(data.get('start_time'), data.get('end_time'))
    except Exception:
        data['status'] = 'Unknown'

    # 6. Create the event and capture its new ID so we can persist candidates
    new_event_id = None
    try:
        new_event_id = Events.createEvent(data)
        print(f"[CREATE EVENT] Events.createEvent returned: {new_event_id}")
        flash('Event created successfully!', 'success')
    except Exception as e:        
        print(f"[CREATE EVENT] Exception creating event: {e}")
        import traceback
        traceback.print_exc()
        flash('Error creating event. Please try again.', 'error')
        return redirect('/admin2')
    
    # 7. Persist candidate names 
    if new_event_id:
        # Deduplicate while preserving order
        seen = set()
        ordered_unique = []
        for c in valid_candidates:
            if c not in seen:
                seen.add(c)
                ordered_unique.append(c)
        try:
            for cand in ordered_unique:
                opt_id = Option.create({'option_text': cand, 'option_event_id': new_event_id})
                print(f"[CREATE EVENT] Created option id={opt_id} text='{cand}' for event {new_event_id}")
        except Exception as e:
            print(f"[CREATE EVENT] Exception creating options: {e}")
            import traceback
            traceback.print_exc()
            flash('Event created but some candidates failed to save.', 'error')
    else:
        flash('Event was not created - please check the logs.', 'error')

    # 8. Only redirect to event list if we successfully created the event
    if new_event_id:
        return redirect(url_for('eventList'))
    else:
        return redirect('/admin2')

# =============================================================================
# EVENT LIST & VIEWING ROUTES - Display events
# =============================================================================

@app.route('/eventList')
def eventList():
    """
    Display list of all events sorted by status and start time.
 
    Redirects:
        - /login: If user is not authenticated
    """
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_data = get_user_session_data()
    allEvents = Events.getAllWithCreators()  # returns sorted events with status
    
    return render_template('eventList.html', allEvents=allEvents, **user_data)

@app.route('/events')
def legacyEventsAlias():
    """
    Backward-compatible alias for old /events links.
    
    Redirects:
        - /eventList: to prevent 404 errors from old bookmarks or links.
    """
    return redirect(url_for('eventList'))

@app.route("/event/<int:event_id>")
def singleEvent(event_id):
    """
    Display a single event with voting interface or results.
    
    Process:
        1. Verify user is logged in
        2. Fetch event details with creator information
        3. Gather event recommendations (other open/upcoming events)
        4. Fetch all options/candidates for this event
        5. Compute event status (Open/Waiting/Closed)
        6. Check if current user is the event creator
        7. Check if user has existing vote (for pre-selection)
        8. If event is closed, calculate and display results with winner
    
    Args:
        event_id (int): ID of the event to display
    
    Redirects:
        - /login: If user is not authenticated
    """
    # 1. Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    # Get current user
    user_data = get_user_session_data()
    
    # 2. Get event object with creator details
    event = Events.getOne({"event_id": event_id})
    
    # Handle the case the event doesn't exists
    if not event:
        return render_template('singleEvent.html', event=None, **user_data)
    
    # 3. Gather recommendations (simple next 3 upcoming events excluding current)
    try:
        recs = Events.getRecommendations({ 'event_id': event_id })
    except Exception:
        recs = []

    # compute statuses for recommendations
    for r in recs:
        try:
            r.status = compute_status(r.start_time, r.end_time)
        except Exception:
            r.status = 'Unknown'
    
    # Only recommend events that are currently open or upcoming
    try:
        recs = [r for r in recs if getattr(r, 'status', None) in ('Open', 'Waiting')]
    except Exception:
        # If anything goes wrong during filtering, keep original list (safe fallback)
        pass

    # If there are no recommendations after filtering, fall back to latest 3 events
    if not recs:
        try:
            all_events = Events.getAllWithCreators() or []
            # Exclude current event and take up to 3
            fallback = [e for e in all_events if getattr(e, 'event_id', None) != event_id][:3]
            recs = fallback
        except Exception:
            recs = recs or []
    # 4. Get all the options for this event
    try:
        options = Option.getByEventId({'event_id': event_id}) or []
    except Exception:
        options = []

    # 5. Check if event is open for voting? (Waiting, Open, Closed)
    try:
        status = compute_status(event.start_time, event.end_time)
    except Exception:
        status = 'Unknown'
    is_open = (status == 'Open')

    # 6. Check if the current user is the event creator
    cur_user = None
    is_event_creator = False
    try:
        cur_user = get_current_user()
        if cur_user:
            is_event_creator = event.isCreatedBy(cur_user)
    except Exception:
        pass

    # 7. Check if user has already voted (UI)
    # Event creators should not have votes, but we check anyway
    selected_option_id = None
    try:
        if cur_user and not is_event_creator:  # Only check votes for non-creators
            existing = Vote.getByUserAndEvent({'user_id': cur_user.user_id, 'event_id': event_id})
            if existing:
                selected_option_id = existing.vote_option_id
    except Exception:
        selected_option_id = None

    # 8. if event is closed, compute + display winner results
    result = None
    if not is_open:
        try:
            result = Result({'event_id': event_id})
        except Exception:
            result = None

    return render_template(
        'singleEvent.html',
        event=event,
        recommendations=recs,
        options=options,
        is_open=is_open,
        event_status=status,
        selected_option_id=selected_option_id,
        tallies=result.rows if not is_open and result else [], 
        winner_option_ids=result.getWinnerOptionIds() if not is_open and result else [], 
        total_votes=result.getTotalVotes() if not is_open and result else 0, 
        is_event_creator=is_event_creator,
        **user_data
    ) 


@app.route('/users/list')
def usersList():
    """
    Return a JSON list of users. Requires login.
    Used by the single event page to show a modal with all users (creator-only button).
    """
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    try:
        rows = User.getAllUsers() or []
        # Return JSON-friendly structure (avoid exposing passwords)
        users = []
        for r in rows:
            users.append({
                'user_id': r.get('user_id'),
                'first_name': r.get('first_name'),
                'last_name': r.get('last_name'),
                'email': r.get('email'),
                'phone': r.get('phone'),
                'created_at': r.get('created_at'),
                'isAdmin': r.get('isAdmin')
            })
        from flask import jsonify
        return jsonify({'ok': True, 'users': users})
    except Exception as e:
        print(f"[USERS LIST] Error fetching users: {e}")
        from flask import jsonify
        return jsonify({'ok': False, 'error': 'Failed to load users'}), 500

# =============================================================================
# EVENT DELETE ROUTES - Remove events
# =============================================================================

@app.route("/events/<int:event_id>/delete", methods=['POST'])
def deleteEvent(event_id):
    """
    Delete an event and redirect safely.
    
    Process:
        1. Verify user is logged in
        2. Get current user object
        3. Verify event exists
        4. Check user has permission (creator or admin)
        5. Delete event from database (cascades to options/votes)
    
    Args:
        event_id (int): ID of the event to delete
    
    Redirects:
        - /eventList: Always (with success or error flash message)
        - /login: If user is not authenticated
    """
    # 1. Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # 2. Get current user object
    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    # 3. Verify event exists
    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # 4. Permission check
    if not user or not user.canManageEvent(event):
        flash("You can only delete events that you created.", "error")
        return redirect(url_for('eventList'))
    
    try:
        # 5a. Delete dependent options first to satisfy FK constraints
        try:
            Option.deleteByEventId({'event_id': event_id})
            print(f"[DELETE EVENT] Deleted options for event {event_id}")
        except Exception as opt_err:
            # Log but continue to attempt event deletion; DB may prevent deletion if options remain
            print(f"[DELETE EVENT] Failed to delete options for event {event_id}: {opt_err}")

        # 5b. Delete event from DB
        result = Events.deleteEvent({"event_id": event_id})
        if result:
            flash(f"Event '{event.title}' deleted.", "success")
        else:
            flash("Failed to delete the event.", "error")
    except Exception as e:
        print(f"Delete event error: {e}")
        flash("An unexpected error occurred while deleting the event.", "error")

    return redirect(url_for('eventList'))

# =============================================================================
# HELPER FUNCTIONS - Internal utilities for edit routes
# =============================================================================

def _fmt_local_dt(raw_val):
    """
    Format a DB datetime or string to HTML datetime-local value (YYYY-MM-DDTHH:MM).
    
    Args:
        raw_val: DateTime object or string from database
    Returns:
        str: Formatted string 'YYYY-MM-DDTHH:MM' or empty string on error
    """
    try:
        dt = parse_datetime(raw_val)
        return dt.strftime('%Y-%m-%dT%H:%M') if dt else ''
    except Exception:
        return ''


def _normalize_full(val_date_only: str, val_local: str):
    """
    Normalize posted datetime values to 'YYYY-MM-DD HH:MM:SS' format.
    Handles timezone conversion by preferring the UTC value over 
    local timezone values. This ensures consistent server-side
    time handling regardless of user's browser timezone.
    
    Args:
        val_date_only (str): UTC value from hidden form field (preferred)
        val_local (str): Local timezone value from datetime-local input
    Returns:
        str: Normalized datetime string 'YYYY-MM-DD HH:MM:SS' or empty string
    """
    # Prefer UTC value (val_date_only) over local timezone (val_local)
    raw = (val_date_only or '').strip() or (val_local or '').strip()
    if not raw:
        return ''
    raw = raw.replace('T', ' ')
    if len(raw) == 16:  # YYYY-MM-DD HH:MM
        raw = raw + ':00'
    if len(raw) == 10:  # YYYY-MM-DD
        raw = raw + ' 00:00:00'
    return raw


@app.route('/events/<int:event_id>/edit')
def editEventGet(event_id):
    """
    Display the event edit form with pre-populated values.
    
    Process:
        1. Verify user is logged in
        2. Get current user object
        3. Verify event exists
        4. Check user has permission (creator or admin)
        5. Determine which fields are editable based on event status
        6. Pre-populate form with current values
        7. Load existing candidates for display
    
    Args:
        event_id (int): ID of the event to edit
    
    Redirects:
        - /eventList: If event not found or no permission
        - /login: If user is not authenticated
    """
    # 1. Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # 2. Get current user object
    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    # 3. Verify event exists
    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # 4. Permission: creator or admin
    if not user or not user.canManageEvent(event):
        flash("You can only edit events that you created.", "error")
        return redirect(url_for('eventList'))

    # 5. Get editable fields based on event status
    editable = event.getEditableFields()
    user_data = get_user_session_data()
    
    # 6. Prefill strings for datetime-local inputs
    prefill_start_local = _fmt_local_dt(event.start_time)
    prefill_end_local = _fmt_local_dt(event.end_time)

    # 7. Load existing options/candidates for this event
    existing_options = []
    try:
        existing_options = Option.getByEventId({'event_id': event_id})
    except Exception as e:
        existing_options = []

    return render_template(
        'eventForms.html',
        edit_mode=True,
        event=event,
        prefill_start_local=prefill_start_local,
        prefill_end_local=prefill_end_local,
        can_edit_title=editable['title'],
        can_edit_desc=editable['description'],
        can_edit_start=editable['start_time'],
        can_edit_end=editable['end_time'],
        existing_options=existing_options,
        **user_data
    )


@app.route('/events/<int:event_id>/edit', methods=['POST'])
def editEventPost(event_id):
    """
    Handle event edit submission with status-aware validation.
    
    Process:
        1. Verify user is logged in
        2. Get current user and verify permissions
        3. Determine which fields are editable based on status
        4. Validate only editable fields
        5. Apply status-specific temporal rules:
           - Waiting: Start can't be in past
           - Open: End must be in future and after start
           - Closed: Keep all times unchanged
        6. Update event record
        7. If status is 'Waiting', process candidate changes:
           - Update existing candidates (by ID)
           - Add new candidates (no ID)
           - Delete removed candidates (in DB but not in form)
    
    Args:
        event_id (int): ID of the event to update

    Redirects:
        - /events/<id>/edit: On validation errors
        - /eventList: On successful update
        - /login: If user is not authenticated
    """
    # 1. Verify user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    # 2. Get current user object
    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    # Validate event exists
    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # Permission check
    if not user or not user.canManageEvent(event):
        flash("You can only edit events that you created.", "error")
        return redirect(url_for('eventList'))

    # 3. Get + Check which fields are editable based on status
    editable = event.getEditableFields()
    status = editable['status']
    can_title = editable['title']
    can_desc = editable['description']
    can_start = editable['start_time']
    can_end = editable['end_time']

    # Read fields
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    start_time_local = request.form.get('start_time_local', '').strip()
    end_time_local = request.form.get('end_time_local', '').strip()

    # 4. Validate only editable fields
    error_message = None

    # Title validation using centralized validators
    if can_title:
        error_message = validate_event_title(title)
    else:
        title = event.title

    # Description validation - optional
    if not error_message and can_desc and description:
        error_message = validate_event_description(description)
    elif not can_desc:
        description = event.description

    # Normalize datetimes; if not editable, keep original DB values
    normalized_start = _normalize_full(start_time, start_time_local) if can_start else (event.start_time or '')
    normalized_end = _normalize_full(end_time, end_time_local) if can_end else (event.end_time or '')

    # Parse for logical checks
    start_dt = parse_datetime(normalized_start)
    end_dt = parse_datetime(normalized_end)
    now = get_now_pacific()

    # Enforce temporal rules based on status
    if not error_message:
        if can_start and not start_dt:
            error_message = 'Please select a start date'
        if not error_message and can_end and not end_dt:
            error_message = 'Please select an end date'
    
    # Time range validation
    if not error_message and start_dt and end_dt:
        if end_dt <= start_dt:
            error_message = 'End time cannot be before or equal to start time'

    # 5. Status-specific rules
    if not error_message:
        if status == 'Waiting' and start_dt and start_dt < now:
            error_message = 'Start time cannot be in the past'
        if status == 'Open':
            # Only end time is editable; ensure it's in the future and after original start
            orig_start = parse_datetime(event.start_time)
            if can_end and end_dt:
                if orig_start and end_dt <= orig_start:
                    error_message = 'End time must be after start time'
                elif end_dt <= now:
                    error_message = 'End time must be in the future for an open event'
        if status == 'Closed':
            # Only description allowed; ensure we keep all others unchanged
            title = event.title
            normalized_start = event.start_time
            normalized_end = event.end_time
    
    # If validation failed, redirect back to edit form
    if error_message:
        flash(error_message, 'error')
        return redirect(url_for('editEventGet', event_id=event_id))

    # 6. Update event record
    data = {
        'event_id': event_id,
        'title': title,
        'description': description if can_desc else event.description,
        'start_time': normalized_start,
        'end_time': normalized_end,
    }
    try:
        Events.editEvent(data)
        flash('Event updated successfully!', 'success')
    except Exception as e:
        print(f"Edit event error: {e}")
        flash('Error updating event. Please try again.', 'error')
        return redirect(url_for('editEventGet', event_id=event_id))

    # 7. ===== CANDIDATE/OPTION MANAGEMENT (only for "Waiting" status) =====
    # Only allow candidate editing if event is still in "Waiting" status
    if status == 'Waiting':
        try:
            # Get submitted candidates from form
            submitted_candidates = request.form.getlist('candidates[]')
            submitted_candidate_ids = request.form.getlist('candidate_ids[]')
            
            # Clean up candidate data (strip whitespace, remove empty entries)
            valid_candidates = []
            valid_ids = []

            # Ensure both lists have the same length by padding with empty strings if needed
            max_len = max(len(submitted_candidates), len(submitted_candidate_ids))
            padded_candidates = submitted_candidates + [''] * (max_len - len(submitted_candidates))
            padded_ids = submitted_candidate_ids + [''] * (max_len - len(submitted_candidate_ids))

            # Process paired data
            for cand_text, cand_id in zip(padded_candidates, padded_ids):
                cleaned_text = cand_text.strip()
                cleaned_id = cand_id.strip()
                
                # Only include if candidate text is not empty
                if cleaned_text:
                    valid_candidates.append(cleaned_text)
                    valid_ids.append(cleaned_id if cleaned_id else None)
            
            # Validate each candidate name before processing updates
            validation_errors = []
            for cand_name in valid_candidates:
                cand_error = validate_candidate_name(cand_name)
                if cand_error:
                    validation_errors.append(cand_error)
            
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                return redirect(url_for('editEventGet', event_id=event_id))

            # Validate minimum candidate count (must have at least 2 candidates for voting)
            if len(valid_candidates) < 2:
                flash('Events must have at least 2 candidates. Please add more candidates before saving.', 'error')
                return redirect(url_for('editEventGet', event_id=event_id))
            
            # Check for duplicate candidates (case-insensitive)
            seen_names = set()
            for cand_name in valid_candidates:
                cand_lower = cand_name.lower()
                if cand_lower in seen_names:
                    flash(f'Duplicate candidate "{cand_name}" is not allowed. Each candidate must have a unique name.', 'error')
                    return redirect(url_for('editEventGet', event_id=event_id))
                seen_names.add(cand_lower)
            

            # Get existing options from database
            existing_options = Option.getByEventId({'event_id': event_id})
            existing_option_ids = {str(opt.option_id) for opt in existing_options}
            
            # Track which options to keep, update, add, or delete
            submitted_option_ids = set()
            
            # Process each submitted candidate
            for idx, cand_text in enumerate(valid_candidates):
                cand_id = valid_ids[idx]
                
                if cand_id and cand_id in existing_option_ids:
                    # UPDATE existing option
                    submitted_option_ids.add(cand_id)
                    # Find the existing option to check if text changed
                    existing_opt = next((opt for opt in existing_options if str(opt.option_id) == cand_id), None)
                    if existing_opt and existing_opt.option_text != cand_text:
                        # Only update if text actually changed
                        Option.update({
                            'option_id': int(cand_id),
                            'option_text': cand_text
                        })
                else:
                    # CREATE new option (no ID or ID not in existing set)
                    new_id = Option.create({
                        'option_text': cand_text,
                        'option_event_id': event_id
                    })
            
            # DELETE options that were removed (exist in DB but not in submission)
            for opt in existing_options:
                if str(opt.option_id) not in submitted_option_ids:
                    Option.deleteById({'option_id': opt.option_id})
            
            
        except Exception as e:
            flash('Event updated but there was an error updating candidates.', 'warning')
            return redirect(url_for('editEventGet', event_id=event_id))

    return redirect(url_for('eventList'))
