import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Force Python to locate modules inside the api directory
sys.path.append(os.path.dirname(__file__))

from ariadne import graphql_sync
from schema import schema

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
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"GraphQL API is running. Point Apollo Sandbox to this URL.")

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

        success, result = graphql_sync(
            schema,
            data,
            context_value={"request": self},
            debug=True
        )

        self.send_response(200 if success else 400)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        self.wfile.write(json.dumps(result).encode('utf-8'))
