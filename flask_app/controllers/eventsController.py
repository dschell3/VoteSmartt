from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app
from flask_app.models.eventsModels import Events


@app.route('/admin2')
def adminPage():
    return render_template('eventForms.html')

@app.route('/createEventRoute', methods=['POST'])
def createEvent():
    data = {
        'title': request.form['title'],
        'description': request.form['description'],
        'start_time': request.form['start_time'],
        'end_time': request.form['end_time'],
        'created_by': request.form['created_by'],

    }
    Events.createEvent(data)
    return redirect(url_for('eventList'))

@app.route('/eventList')
def eventList():
    return render_template('eventList.html')