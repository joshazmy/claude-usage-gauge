"""
Preview server  --  v1
-----------------------------------------------------------------
Tiny local web server so you can SEE your desk-screen design in a
browser before the real hardware arrives. Uses only built-in Python
(nothing to install).

Run it:
    py server.py

Then open this in your browser:
    http://localhost:8780

Leave this window open while you look at the preview. Press Ctrl+C
in this window to stop it.
-----------------------------------------------------------------
"""

import http.server
import socketserver
import json
import os

import usage  # reuse the reader in usage.py

PORT = 8780
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.BaseHTTPRequestHandler):

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/usage"):
            # the live numbers, as JSON
            self._send(200, json.dumps(usage.collect()).encode("utf-8"),
                       "application/json")
        elif self.path in ("/", "/preview.html"):
            with open(os.path.join(HERE, "preview.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args):
        pass  # keep the window quiet


if __name__ == "__main__":
    print("Claude usage preview is running.")
    print("Open this in your browser:  http://localhost:%d" % PORT)
    print("(Keep this window open. Press Ctrl+C to stop.)")
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()
