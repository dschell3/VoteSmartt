from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events
from flask_app.models.userModels import User


@app.route('/admin2')
def adminPage():
    return render_template('eventForms.html')

@app.route('/createEventRoute', methods=['POST'])
def createEventRoute():
    user = User.getUserByID(session['user_id'])
    print("THIS IS THE ID",session['user_id'])
    first_name = user.first_name
    data = {
        'title': request.form['title'],
        'description': request.form['description'],
        'start_time': request.form['start_time'],
        'end_time': request.form['end_time'],
        'event_user_fk': session['user_id'],
        'created_by': first_name

    }

    Events.createEvent(data)
    return redirect(url_for('eventList'))

@app.route('/eventList')
def eventList():
    allEvents = Events.getAll()
    return render_template('eventList.html', allEvents = allEvents)

