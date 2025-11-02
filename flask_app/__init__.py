import os
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_mail import Mail

load_dotenv()

app = Flask(__name__)
# Prefer an env-provided secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'THISISASECRETKEYBUTCHANGEITORDONT6769420HEHEHEHA')

# Mail configuration (read from environment)
app.config['MAIL_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')
# Default sender (fallback to the username)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

# Initialize Flask-Mail
mail = Mail(app)


@app.errorhandler(404)
def page_not_found(e):
	# import locally to avoid circular import at module import time
	from flask_app.controllers.userController import get_user_session_data
	# include user session data so template can show contextual CTAs
	ctx = get_user_session_data()
	return render_template('404.html', **ctx), 404

