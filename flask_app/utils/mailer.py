from flask import current_app
from flask_mail import Message
from flask_app import mail


def send_contact_email(subject: str, body: str, recipients: list):
    """Send a contact email using Flask-Mail.

    Args:
        subject: Subject line for the message.
        body: Plain text body of the message.
        recipients: List of recipient email addresses.
    Returns:
        None. Raises on failure.
    """
    msg = Message(subject=subject, recipients=recipients)
    msg.body = body
    # Use configured default sender (MAIL_DEFAULT_SENDER) if available
    try:
        mail.send(msg)
    except Exception as e:
        # Log the error to console and re-raise so callers can handle it.
        try:
            if current_app:
                current_app.logger.error(f"Error sending mail to {recipients}: {e}")
        except Exception:
            print(f"Error sending mail to {recipients}: {e}")
        raise
