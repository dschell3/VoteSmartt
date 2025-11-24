from flask_app import app
from flask_app.controllers import userController, eventsController, voteController  # noqa: F401
# Ensure all route modules are imported so their @app.route decorators execute.
# Previously voteController was not imported, causing POST /vote/cast to 404.

import os
import socket
import logging
from typing import Optional

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False


def get_port_from_env(default: int = 5000) -> int:
    port_env = os.environ.get('PORT') or os.environ.get('FLASK_RUN_PORT')
    if port_env:
        try:
            return int(port_env)
        except ValueError:
            logging.warning("Invalid port in environment (%s), falling back to default %s", port_env, default)
            return default

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _public_host_for_url(host: str) -> str:
    if not host or host in ('0.0.0.0', '::'):
        return 'localhost'
    return host


def _get_bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() not in ('0', 'false', 'no')


if __name__ == '__main__':
    if _HAS_DOTENV:
        load_dotenv()
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    host = os.environ.get('HOST', '127.0.0.1')
    port = get_port_from_env(5000)
    if not app.config.get('BASE_URL'):
        scheme = os.environ.get('BASE_URL_SCHEME', 'http')
        public_host = _public_host_for_url(host)
        app.config['BASE_URL'] = f"{scheme}://{public_host}:{port}"
    debug = _get_bool_env('FLASK_DEBUG', True)
    use_reloader = _get_bool_env('USE_RELOADER', True)

    logging.info("Starting server — host=%s port=%s debug=%s reloader=%s", host, port, debug, use_reloader)

    try:
        app.run(debug=debug, host=host, port=port, use_reloader=use_reloader)
    except KeyboardInterrupt:
        logging.info("Server interrupted, shutting down")
