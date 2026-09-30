import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler
import requests
import jwt

# Force Python to locate modules inside the api directory
sys.path.append(os.path.dirname(__file__))

from ariadne import graphql_sync
from schema import schema

JWT_SECRET = os.environ.get("JWT_SECRET", "lab07-super-secret")

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        debug_info = {
            "received_path": self.path,
            "has_client_id": bool(os.environ.get("GITHUB_CLIENT_ID")),
            "has_secret": bool(os.environ.get("GITHUB_CLIENT_SECRET")),
            "callback_url": os.environ.get("CALLBACK_URL", "missing")
        }
        
        self.wfile.write(json.dumps(debug_info).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error": "Empty request body"}')
            return

        try:
            data = json.loads(self.rfile.read(content_length))
        except json.JSONDecodeError:
            self.send_response(400)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        # Decode JWT from Header
        auth_header = self.headers.get('Authorization', '')
        user = None
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
            try:
                user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            except jwt.InvalidTokenError:
                user = None

        # Inject User into Context
        success, result = graphql_sync(
            schema,
            data,
            context_value={"request": self, "user": user},
            debug=True
        )

        self.send_response(200 if success else 400)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        self.wfile.write(json.dumps(result).encode('utf-8'))
