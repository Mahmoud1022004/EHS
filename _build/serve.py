#!/usr/bin/env python3
"""Local preview server that behaves like the live edge.

The published pages link to clean URLs (/about, not /about.html) because that is
what Cloudflare serves. A plain `python3 -m http.server` cannot resolve those, so
use this instead:

    python3 _build/serve.py          # then open http://localhost:8000
    python3 _build/serve.py 8080     # or pick a port

It adds the two behaviours the edge provides and a plain file server does not:
extensionless URLs resolve to the matching .html file, and an unknown URL renders
404.html (or ar/404.html) with a real 404 status instead of a bare error string.
"""
import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        full = super().translate_path(path)
        if os.path.exists(full):
            return full
        # /about -> about.html, the way the edge resolves it.
        if not os.path.splitext(full)[1] and os.path.exists(full + ".html"):
            return full + ".html"
        return full

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = os.path.join(ROOT, "ar", "404.html") \
                if self.path.startswith("/ar/") else os.path.join(ROOT, "404.html")
            if os.path.exists(page):
                with open(page, "rb") as f:
                    body = f.read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().send_error(code, message, explain)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(ROOT)
    print(f"EHS preview on http://localhost:{port}   (Ctrl-C to stop)")
    http.server.ThreadingHTTPServer(
        ("", port), functools.partial(Handler, directory=ROOT)).serve_forever()
