import json
from http.server import BaseHTTPRequestHandler
from ariadne import graphql_sync
try:
    from .schema import schema
except ImportError:
    from schema import schema

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        # Handle CORS preflight requests from Apollo Sandbox
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
        data = json.loads(self.rfile.read(content_length))

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
