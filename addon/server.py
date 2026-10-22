"""Loopback-only authenticated Streamable HTTP transport."""

import hmac
import ipaddress
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_BODY = 32 * 1024 * 1024


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port, token, protocol):
        if len(token) < 32:
            raise ValueError("MCP token must contain at least 32 characters")
        self.token, self.protocol = token, protocol
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(("127.0.0.1", port), Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "AnkiMCP"

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *_args):
        pass

    def send_json(self, code, data=None):
        body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode() if data is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def allowed(self):
        if self.path != "/mcp":
            self.send_json(404)
            return False
        expected_host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") not in (expected_host, f"localhost:{self.server.server_port}"):
            self.send_json(403)
            return False
        origin = self.headers.get("Origin")
        if origin is not None:
            try:
                parsed = urlsplit(origin)
                local = (
                    parsed.scheme == "http"
                    and parsed.hostname in ("127.0.0.1", "localhost")
                    and parsed.port == self.server.server_port
                    and not parsed.username
                    and not parsed.path
                    and not parsed.query
                    and not parsed.fragment
                )
            except ValueError:
                local = False
            if not local:
                self.send_json(403)
                return False
        if not ipaddress.ip_address(self.client_address[0]).is_loopback:
            self.send_json(403)
            return False
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied.encode(), f"Bearer {self.server.token}".encode()):
            self.send_json(401)
            return False
        return True

    def do_POST(self):
        if not self.allowed():
            return
        if self.headers.get_content_type() != "application/json" or self.headers.get("Transfer-Encoding"):
            self.send_json(415)
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            self.send_json(413)
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                self.send_json(400)
                return
            request = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError):
            self.send_json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            return
        response = self.server.protocol.handle(request)
        self.send_json(202 if response is None else 200, response)

    def do_GET(self):
        if self.allowed():
            self.send_json(405)

    def do_DELETE(self):
        if self.allowed():
            self.send_json(405)

    def do_OPTIONS(self):
        self.send_json(405)
