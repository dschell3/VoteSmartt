from flask_app import app
from flask_app.controllers import userController, eventsController, voteController  # noqa: F401
# Ensure all route modules are imported so their @app.route decorators execute.
# Previously voteController was not imported, causing POST /vote/cast to 404.

import os
from flask import Flask
import socket


def get_port_from_env(default: int = 5000) -> int:
    """Return port from environment variables or default.

    Looks for PORT, FLASK_RUN_PORT, or falls back to `default`.
    """
    port_env = os.environ.get('PORT') or os.environ.get('FLASK_RUN_PORT')
    try:
        return int(port_env) if port_env else default
    except ValueError:
        return default


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = get_port_from_env(5000)

    # Ensure BASE_URL is set consistently so emails include the correct host/port
    if not app.config.get('BASE_URL'):
        # Use host:port for local development. If running behind a proxy set BASE_URL env.
        scheme = os.environ.get('BASE_URL_SCHEME', 'http')
        app.config['BASE_URL'] = f"{scheme}://{host}:{port}"

    print(f"Starting server on {host}:{port}")
    app.run(debug=True, host=host, port=port, use_reloader=True)
