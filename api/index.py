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
        # 1. Redirect to GitHub Provider
        if 'auth/login' in self.path:
            client_id = os.environ.get("GITHUB_CLIENT_ID")
            callback = os.environ.get("CALLBACK_URL")
            url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={callback}"
            
            self.send_response(302)
            self.send_header('Location', url)
            self.end_headers()
            return
            
        # 2. Handle GitHub Callback & Exchange Token
        elif 'auth/callback' in self.path:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code = query.get('code', [None])[0]
            
            if not code:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'{"error": "Missing code parameter"}')
                return
            
            # Request Access Token from GitHub
            token_res = requests.post(
                'https://github.com/login/oauth/access_token',
                json={
                    'client_id': os.environ.get("GITHUB_CLIENT_ID"),
                    'client_secret': os.environ.get("GITHUB_CLIENT_SECRET"),
                    'code': code
                },
                headers={'Accept': 'application/json'}
            ).json()
            
            access_token = token_res.get('access_token')
            if not access_token:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(token_res).encode('utf-8'))
                return

            # Fetch GitHub User Profile
            user_res = requests.get(
                'https://api.github.com/user', 
                headers={'Authorization': f"Bearer {access_token}"}
            ).json()
            
            # Issue JWT
            token = jwt.encode({"username": user_res.get("login")}, JWT_SECRET, algorithm="HS256")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"token": token}).encode('utf-8'))
            return
            
        # Default Fallback
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
