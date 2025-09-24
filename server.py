from flask_app import app
from flask_app.controllers import userController
from flask import Flask
import socket

def get_free_port():
    """Find an available port on this machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))               # bind to a random free port
        return s.getsockname()[1]     # return the chosen port

if __name__ == '__main__':
    port = get_free_port()
    print(f"Starting server on port {port}")
    app.run(debug=True, port=port, use_reloader=False)
