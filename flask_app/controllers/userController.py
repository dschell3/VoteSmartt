from flask import Flask, jsonify, request, flash, url_for, redirect, session, render_template, request
from flask_app import app

@app.route('/') # Homepage route
def homepage():
    return render_template('homepage.html')
