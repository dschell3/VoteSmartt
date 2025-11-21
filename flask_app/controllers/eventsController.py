from flask import flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events
from flask_app.models.optionModels import Option
from flask_app.models.voteModels import Vote
from datetime import datetime, timezone
from flask_app.utils.helpers import require_login, get_current_user, get_user_session_data, is_logged_in
from flask_app.utils.validators import validate_event_title, validate_event_description, validate_candidate_name

# moved compute_status and _parse_datetime to Events model for reuse
# so other controllers can call it too

@app.route('/admin2')
def adminPage():
    # Require login to access the event creation page and pass session user data
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    user_data['edit_mode'] = False  # Indicate creation mode
    
    return render_template('eventForms.html', **user_data)

@app.route('/createEventRoute', methods=['POST'])
def createEventRoute():
    # 001 - Added comprehensive server-side validation for form submission
    # Ensure user is logged in
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user = get_current_user()

    # remove unused variable and print user ID for debugging
    print("THIS IS THE ID", user.user_id)
    first_name = user.first_name
    
    # Server-side validation - Now receiving LOCAL times directly
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    start_time_local = request.form.get('start_time', '').strip()  # LOCAL time from datetime-local
    end_time_local = request.form.get('end_time', '').strip()      # LOCAL time from datetime-local
    candidate = request.form.getlist('candidates[]')

    print(f"[DEBUG] Received LOCAL times: start={start_time_local}, end={end_time_local}")


    print(f"[DEBUG] Received times (local): start={start_time_local}, end={end_time_local}")

    candidate_descs = request.form.getlist('candidate_descs[]')
    # Build candidate list early so it's always available (avoid elif-chain scoping issues)
    valid_candidates = [c.strip() for c in candidate if (c or '').strip()]
    
    # Validation - check in priority order and show only the most important error
    error_message = None
    
    # Priority 1: Event name - Use centralized validator
    error_message = validate_event_title(title)

    # Priority 1.5: Event description validation
    if not error_message and description:
        error_message = validate_event_description(description)

    # Priority 2: Start date (if name is OK)
    elif not start_time_local:
        error_message = 'Please select a start date'
    
    # Priority 3: End date (if name and start date are OK)
    elif not end_time_local:
        error_message = 'Please select an end date'
    
    # Priority 4: Date validation (if all dates are provided)
    elif start_time_local and end_time_local:
        try:
            # Accept full datetime (preferred) and date-only as fallback
            def _parse_dt(val: str):
                v = (val or '').strip()
                # Replace 'T' with space for normalization
                v = v.replace('T', ' ')
                fmts = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
                for f in fmts:
                    try:
                        dt = datetime.strptime(v, f)
                        # DON'T make timezone-aware here - keep as naive local time
                        return dt
                    except Exception:
                        continue
                return None

            start_dt = _parse_dt(start_time_local)
            end_dt = _parse_dt(end_time_local)
            if not start_dt or not end_dt:
                raise ValueError('Invalid datetime format')

            # Convert local times to UTC for comparison with server time
            from datetime import timedelta
            pacific_offset = timedelta(hours=-8)
            
            # Treat as Pacific time and convert to UTC
            start_dt_aware = start_dt.replace(tzinfo=timezone(pacific_offset))
            start_dt_utc = start_dt_aware.astimezone(timezone.utc)
            
            now_utc = datetime.now(timezone.utc)

            # Check if start time is in the past
            if start_dt_utc < now_utc:
                error_message = 'Start time cannot be in the past'

            if not error_message:
                if end_dt <= start_dt:
                    error_message = 'End time cannot be before or equal to start time'

            # 10-year sanity window
            if not error_message:
                if start_dt.year > now_utc.year + 10 or end_dt.year > now_utc.year + 10:
                    error_message = 'Event dates cannot be more than 10 years in the future'

        except ValueError:
            error_message = 'Invalid date format'
        
    # Priority 5: Description length (optional field, only check if provided)
    if not error_message and description and len(description) > 1000:
        error_message = 'Event description is too long (maximum 1000 characters)'

    # Priority 6: Candidates (always validated once earlier checks pass)
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
    
    # === DEBUGGING: Print the exact validation error ===
    if error_message:
        print(f"[VALIDATION ERROR] {error_message}")
        print(f"[VALIDATION ERROR] start_time_local value: {start_time_local}")  # ✅ CORRECT
        print(f"[VALIDATION ERROR] end_time_local value: {end_time_local}")      # ✅ CORRECT
        # Also print what datetime was parsed
        try:
            def _parse_dt(val: str):
                v = (val or '').strip()
                v = v.replace('T', ' ')  # Add this line
                fmts = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
                for f in fmts:
                    try:
                        return datetime.strptime(v, f)
                    except Exception:
                        continue
                return None
            
            start_dt = _parse_dt(start_time_local)  # ✅ CORRECT - use start_time_local
            now = datetime.now(timezone.utc)
            print(f"[VALIDATION ERROR] Parsed start_dt: {start_dt}")
            print(f"[VALIDATION ERROR] Server now(): {now}")
            if start_dt:
                # Convert to UTC for comparison
                from datetime import timedelta
                pacific_offset = timedelta(hours=-8)
                start_dt_aware = start_dt.replace(tzinfo=timezone(pacific_offset))
                start_dt_utc = start_dt_aware.astimezone(timezone.utc)
                print(f"[VALIDATION ERROR] start_dt_utc < now? {start_dt_utc < now}")
                print(f"[VALIDATION ERROR] Difference: {(now - start_dt_utc).total_seconds()} seconds")
        except Exception as e:
            print(f"[VALIDATION ERROR] Could not parse for debugging: {e}")
        
        flash(error_message, 'error')
        return redirect('/admin2')
    

    # If there's a validation error, show only one message
    if error_message:
        flash(error_message, 'error')
        return redirect('/admin2')
    
    # Build normalized full datetime strings (YYYY-MM-DD HH:MM:SS)
    # Normalize datetime format (from datetime-local) - Keep in LOCAL timezone
    def normalize_datetime_local(val: str):
        """Normalize datetime-local format to 'YYYY-MM-DD HH:MM:SS' without timezone conversion"""
        if not val:
            return ''
        # datetime-local format: YYYY-MM-DDTHH:MM
        val = val.strip().replace('T', ' ')
        if len(val) == 16:  # YYYY-MM-DD HH:MM
            val = val + ':00'
        return val

    normalized_start = normalize_datetime_local(start_time_local)
    normalized_end = normalize_datetime_local(end_time_local)

    print(f"[DEBUG] Normalized LOCAL times: start={normalized_start}, end={normalized_end}")

    # All validation passed, create the event using normalized times
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
        data['status'] = Events.compute_status(data.get('start_time'), data.get('end_time'))
    except Exception:
        data['status'] = 'Unknown'

    # Create the event and capture its new ID so we can persist candidates
    new_event_id = None
    try:
        print(f"[DEBUG] About to create event with data: {data}")
        print(f"[DEBUG] Normalized start_time: {normalized_start}")
        print(f"[DEBUG] Normalized end_time: {normalized_end}")
        print(f"[DEBUG] Computed status: {data.get('status')}")
        
        new_event_id = Events.createEvent(data)
        
        print(f"[DEBUG] Event created successfully! new_event_id = {new_event_id}")
        flash('Event created successfully!', 'success')
    except Exception as e:
        # THIS IS THE CRITICAL PART - LOG THE ACTUAL ERROR
        print(f"[ERROR] Failed to create event!")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback:")
        traceback.print_exc()
        
        flash('Error creating event. Please try again.', 'error')
        return redirect('/admin2')

    print(f"[DEBUG] After event creation, new_event_id = {new_event_id}")
    
    # Persist candidate names (descriptions deferred per choice C)
    # NOTE: valid_candidates was built during validation; we ignore candidate_descs for now.
    if new_event_id:
        print(f"[DEBUG] Persisting {len(valid_candidates)} candidates...")
        # Deduplicate while preserving order
        seen = set()
        ordered_unique = []
        for c in valid_candidates:
            if c not in seen:
                seen.add(c)
                ordered_unique.append(c)
        try:
            for cand in ordered_unique:
                print(f"[DEBUG] Creating candidate: {cand}")
                Option.create({'option_text': cand, 'option_event_id': new_event_id})
            print(f"[DEBUG] All candidates created successfully!")
        except Exception as e:
            # Non‑fatal: event exists even if candidate insertion partially fails
            print(f"[ERROR] Candidate insertion error for event {new_event_id}")
            print(f"[ERROR] Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Event created but some candidates failed to save.', 'error')
    else:
        print("[ERROR] No new_event_id; skipping candidate persistence.")
        flash('Event was not created - please check the logs.', 'error')

    # Only redirect to event list if we successfully created the event
    if new_event_id:
        return redirect(url_for('eventList'))
    else:
        return redirect('/admin2')

    # Persist candidate names (descriptions deferred per choice C)
    # NOTE: valid_candidates was built during validation; we ignore candidate_descs for now.
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
                Option.create({'option_text': cand, 'option_event_id': new_event_id})
        except Exception as e:
            # Non‑fatal: event exists even if candidate insertion partially fails
            print(f"Candidate insertion error for event {new_event_id}: {e}")
            flash('Event created but some candidates failed to save.', 'error')
    else:
        print("[createEventRoute] No new_event_id; skipping candidate persistence.")
    
    return redirect(url_for('eventList'))

@app.route('/eventList')
def eventList():
    """Display list of all events, sorted by status and start time"""
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    
    user_data = get_user_session_data()
    allEvents = Events.getAllWithCreators()  # returns sorted events with status
    
    return render_template('eventList.html', allEvents=allEvents, **user_data)

@app.route('/events')
def legacyEventsAlias():
    """Backward-compatible alias for old /events links -> redirect to eventList."""
    return redirect(url_for('eventList'))


@app.route("/events/<int:event_id>/delete", methods=['POST'])
def deleteEvent(event_id):
    """Delete an event then redirect safely.

    Improvements:
    - Use named route redirect (eventList) for consistency.
    - Graceful handling if user object or permissions method not present.
    - Avoid redirecting to hard-coded /events (not defined) to prevent 404.
    - Minimize branching; single exit redirect.
    """
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # Permission check (tolerate missing method can_manage_events)
    can_manage = False
    if user:
        try:
            can_manage = getattr(user, 'can_manage_events', lambda: False)()
        except Exception:
            can_manage = False

    if not user or (event.created_byFK != getattr(user, 'user_id', None) and not can_manage):
        flash("You can only delete events that you created.", "error")
        return redirect(url_for('eventList'))

    try:
        result = Events.deleteEvent({"event_id": event_id})
        if result:
            flash(f"Event '{event.title}' deleted.", "success")
        else:
            flash("Failed to delete the event.", "error")
    except Exception as e:
        print(f"Delete event error: {e}")
        flash("An unexpected error occurred while deleting the event.", "error")

    return redirect(url_for('eventList'))


@app.route("/event/<int:event_id>")
def singleEvent(event_id):
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)
    user_data = get_user_session_data()
    event = Events.getOne({"event_id": event_id})
    if not event:
        return render_template('singleEvent.html', event=None, **user_data)
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
    # options for this event
    try:
        options = Option.getByEventId({'event_id': event_id}) or []
    except Exception:
        options = []

    # is event open for voting? (single status compute)
    try:
        status = Events.compute_status(event.start_time, event.end_time)
    except Exception:
        status = 'Unknown'
    is_open = (status == 'Open')

    # Get current user and check if they're the event creator
    cur_user = None
    is_event_creator = False
    try:
        cur_user = get_current_user()
        if cur_user:
            # Check if current user is the creator of this event
            is_event_creator = (event.created_byFK == cur_user.user_id)
    except Exception:
        pass

    # existing vote for this user (to preselect / allow update)
    # Event creators should not have votes, but we check anyway
    selected_option_id = None
    try:
        if cur_user and not is_event_creator:  # Only check votes for non-creators
            existing = Vote.getByUserAndEvent({'user_id': cur_user.user_id, 'event_id': event_id})
            if existing:
                selected_option_id = existing.vote_option_id
    except Exception:
        selected_option_id = None

    # tallies if not open (show results)
    tallies = []
    if not is_open:
        try:
            tallies = Vote.tallyVotesForEvent({'event_id': event_id}) or []
        except Exception:
            tallies = []

    return render_template('singleEvent.html', event=event, recommendations=recs, options=options, is_open=is_open, event_status=status, selected_option_id=selected_option_id, tallies=tallies, is_event_creator=is_event_creator, **user_data)


# ==========================
# Minimal EDIT routes (GET/POST) reusing existing template and validation
# ==========================

def _fmt_local_dt(raw_val):
    """Format a DB datetime or string to HTML datetime-local value (YYYY-MM-DDTHH:MM)."""
    try:
        dt = Events.parse_datetime(raw_val)
        return dt.strftime('%Y-%m-%dT%H:%M') if dt else ''
    except Exception:
        return ''


def _normalize_full(val_date_only: str, val_local: str):
    """Normalize posted datetime values to 'YYYY-MM-DD HH:MM:SS'. 
    
    Prefers val_date_only (UTC from hidden field) to ensure proper timezone handling.
    The hidden field contains UTC time converted by JavaScript, while val_local 
    contains the user's local timezone which we DON'T want to use directly.
    """
    # CRITICAL: Prefer UTC value (val_date_only) over local timezone (val_local)
    raw = (val_date_only or '').strip() or (val_local or '').strip()
    if not raw:
        return ''
    raw = raw.replace('T', ' ')
    if len(raw) == 16:  # YYYY-MM-DD HH:MM
        raw = raw + ':00'
    if len(raw) == 10:  # YYYY-MM-DD
        raw = raw + ' 00:00:00'
    return raw


def _can_edit_fields_by_status(status):
    """Return booleans controlling which fields are editable under a given status.
    Policy: Waiting -> can edit start/end/title/desc; Open -> can edit end/title/desc; Closed -> only desc.
    """
    status = (status or '').strip()
    can_title = True
    can_desc = True
    can_start = False
    can_end = False
    if status == 'Waiting':
        can_start = True
        can_end = True
    elif status == 'Open':
        can_start = False
        can_end = True
    elif status == 'Closed':
        can_title = False
        can_desc = True
        can_start = False
        can_end = False
    else:
        # Unknown -> safest: allow title/desc only
        can_title = True
        can_desc = True
        can_start = False
        can_end = False
    return can_title, can_desc, can_start, can_end


@app.route('/events/<int:event_id>/edit')
def editEventGet(event_id):
    """Render edit page reusing eventForms.html with edit_mode."""
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # Permission: creator or admin
    can_manage = False
    if user:
        try:
            is_admin = 1 if session.get('isAdminByID', 0) == 1 else 0
            can_manage = getattr(user, 'can_manage_events', lambda: False)() or (event.created_byFK == getattr(user, 'user_id', None)) or bool(is_admin)
        except Exception:
            can_manage = (event.created_byFK == getattr(user, 'user_id', None))
    if not user or not can_manage:
        flash("You can only edit events that you created.", "error")
        return redirect(url_for('eventList'))

    # Compute current status to drive editability
    try:
        # Ensure start_time and end_time are timezone-aware
        start_val = event.start_time
        end_val = event.end_time
        
        # If they're datetime objects without timezone, add UTC
        if isinstance(start_val, datetime) and start_val.tzinfo is None:
            start_val = start_val.replace(tzinfo=timezone.utc)
        if isinstance(end_val, datetime) and end_val.tzinfo is None:
            end_val = end_val.replace(tzinfo=timezone.utc)
        
        status = Events.compute_status(start_val, end_val)
        
        # DEBUG (remove after testing)
        print(f"[DEBUG] Event {event_id} status: {status}")
    
    except Exception as e:
        print(f"[ERROR] Status computation failed: {e}")
        status = 'Unknown'

    can_title, can_desc, can_start, can_end = _can_edit_fields_by_status(status)

    user_data = get_user_session_data()
    # Prefill strings for datetime-local inputs
    prefill_start_local = _fmt_local_dt(event.start_time)
    prefill_end_local = _fmt_local_dt(event.end_time)

    # Load existing options/candidates for this event
    existing_options = []
    try:
        existing_options = Option.getByEventId({'event_id': event_id})
    except Exception as e:
        print(f"[ERROR] Failed to load options for event {event_id}: {e}")
        existing_options = []

    return render_template(
        'eventForms.html',
        edit_mode=True,
        event=event,
        prefill_start_local=prefill_start_local,
        prefill_end_local=prefill_end_local,
        can_edit_title=can_title,
        can_edit_desc=can_desc,
        can_edit_start=can_start,
        can_edit_end=can_end,
        existing_options=existing_options,
        **user_data
    )


@app.route('/events/<int:event_id>/edit', methods=['POST'])
def editEventPost(event_id):
    """Handle edit submission with minimal validation and field restrictions by status."""
    redirect_url = require_login()
    if redirect_url:
        return redirect(redirect_url)

    user = None
    try:
        user = get_current_user()
    except Exception:
        user = None

    event = Events.getOne({"event_id": event_id})
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('eventList'))

    # Permission check
    can_manage = False
    if user:
        try:
            is_admin = 1 if session.get('isAdminByID', 0) == 1 else 0
            can_manage = getattr(user, 'can_manage_events', lambda: False)() or (event.created_byFK == getattr(user, 'user_id', None)) or bool(is_admin)
        except Exception:
            can_manage = (event.created_byFK == getattr(user, 'user_id', None))
    if not user or not can_manage:
        flash("You can only edit events that you created.", "error")
        return redirect(url_for('eventList'))

    # Current status
    try:
        status = Events.compute_status(event.start_time, event.end_time)
    except Exception:
        status = 'Unknown'
    can_title, can_desc, can_start, can_end = _can_edit_fields_by_status(status)

    # Read fields
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    start_time_local = request.form.get('start_time_local', '').strip()
    end_time_local = request.form.get('end_time_local', '').strip()

    # Basic validation similar to create, but skip candidates and adjust by status
    error_message = None

    # Title/desc validation using centralized validators
    if can_title:
        error_message = validate_event_title(title)
    else:
        title = event.title

    if not error_message and can_desc and description:
        error_message = validate_event_description(description)
    elif not can_desc:
        description = event.description

    # Normalize datetimes; if not editable, keep original DB values
    normalized_start = _normalize_full(start_time, start_time_local) if can_start else (event.start_time or '')
    normalized_end = _normalize_full(end_time, end_time_local) if can_end else (event.end_time or '')

    # Parse for logical checks
    start_dt = Events.parse_datetime(normalized_start)
    end_dt = Events.parse_datetime(normalized_end)
    now = datetime.now(timezone.utc)

    # CRITICAL FIX: Make parsed datetimes timezone-aware for comparison
    if start_dt and start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt and end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    # Enforce temporal rules based on status
    if not error_message:
        if can_start and not start_dt:
            error_message = 'Please select a start date'
        if not error_message and can_end and not end_dt:
            error_message = 'Please select an end date'

    if not error_message and start_dt and end_dt:
        if end_dt <= start_dt:
            error_message = 'End time cannot be before or equal to start time'

    # Additional rules by status
    if not error_message:
        if status == 'Waiting' and start_dt and start_dt < now:
            error_message = 'Start time cannot be in the past'
        if status == 'Open':
            # Only end time is editable; ensure it's in the future and after original start
            orig_start = Events.parse_datetime(event.start_time)
            # Make orig_start timezone-aware too
            if orig_start and orig_start.tzinfo is None:
                orig_start = orig_start.replace(tzinfo=timezone.utc)
            
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

    if error_message:
        flash(error_message, 'error')
        return redirect(url_for('editEventGet', event_id=event_id))

    # Persist update
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

    # ===== CANDIDATE/OPTION MANAGEMENT (only for "Waiting" status) =====
    # Only allow candidate editing if event is still in "Waiting" status
    if status == 'Waiting':
        try:
            # Get submitted candidates from form
            submitted_candidates = request.form.getlist('candidates[]')
            submitted_candidate_ids = request.form.getlist('candidate_ids[]')
            
            # Clean up candidate data (strip whitespace, remove empty entries)
            # CRITICAL FIX: Zip candidates with IDs to maintain proper pairing
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
                print(f"[VALIDATION ERROR] Event {event_id}: Insufficient candidates ({len(valid_candidates)}/2 required)")
                return redirect(url_for('editEventGet', event_id=event_id))
            

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
                        print(f"[DEBUG] Updated option {cand_id}: '{cand_text}'")
                else:
                    # CREATE new option (no ID or ID not in existing set)
                    new_id = Option.create({
                        'option_text': cand_text,
                        'option_event_id': event_id
                    })
                    print(f"[DEBUG] Created new option: '{cand_text}' with ID {new_id}")
            
            # DELETE options that were removed (exist in DB but not in submission)
            for opt in existing_options:
                if str(opt.option_id) not in submitted_option_ids:
                    Option.deleteById({'option_id': opt.option_id})
                    print(f"[DEBUG] Deleted option {opt.option_id}: '{opt.option_text}'")
            
            print(f"[DEBUG] Candidate update complete for event {event_id}")
            
        except Exception as e:
            print(f"[ERROR] Candidate update failed for event {event_id}: {e}")
            flash('Event updated but there was an error updating candidates.', 'warning')
            return redirect(url_for('editEventGet', event_id=event_id))

    return redirect(url_for('eventList'))
