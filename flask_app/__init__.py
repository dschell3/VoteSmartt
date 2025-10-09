import os
from flask import Flask
app = Flask(__name__)
app.secret_key = 'THISISASECRETKEYBUTCHANGEITORDONT6769420HEHEHEHA'
from flask import render_template
from flask_app.controllers.userController import get_user_session_data


@app.errorhandler(404)
def page_not_found(e):
	# include user session data so template can show contextual CTAs
	ctx = get_user_session_data()
	return render_template('404.html', **ctx), 404

