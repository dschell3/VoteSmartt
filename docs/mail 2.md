# Mail / SMTP Configuration

This project uses Flask-Mail to send email (contact form, password resets, etc.). Follow these steps to configure it locally and in production.

Local setup

1. Copy `.env.example` to `.env` and fill in your values. Example values:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
EMAIL_USER=your.full@gmail.com
EMAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=your.full@gmail.com
```

2. Never commit `.env` to git. Add `.env` to `.gitignore` if not already present.

3. The app will load environment variables automatically (the project uses `python-dotenv`).

Production (Heroku / other)

- Set the same variables in your hosting provider's secret store (Heroku config vars, AWS Secrets Manager, etc.).
- Do NOT store passwords in repo files.

Important security note

If you ever expose the App Password in a public repo or chat, immediately revoke it in your Google account and create a new App Password.

Testing mail sending

1. Start the app with your environment variables set.
2. Open the contact page and submit a test message.
3. If mail sending fails, check logs for errors; common issues are incorrect credentials or network/port blocking.

Troubleshooting

- If using Gmail, ensure you created an App Password for the account (this is required when 2FA is enabled). Regular account passwords usually won't work.
- Use port 465 with SSL or 587 with TLS/STARTTLS. The config uses TLS by default (587).
