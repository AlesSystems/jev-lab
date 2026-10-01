"""Release Room composes the existing release and feedback assessments."""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from demos.feedback_kitchen import feedback_kitchen as feedback
from demos.launch_lab import launch_lab as release

STATIC = Path(__file__).with_name('static')
ENGINES = {'/api/release': release, '/api/feedback': feedback}
MAX_BODY = feedback.MAX_BODY


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload, mime='application/json; charset=utf-8'):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/config':
            return self.reply(200, {'products': feedback.public_products(), 'releases': release.RELEASES, 'live_available': bool(os.getenv('TYPESAFE_API_KEY'))})
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/app.css': ('app.css', 'text/css'), '/newsreader.ttf': ('newsreader.ttf', 'font/ttf')}
        if path not in files:
            return self.reply(404, {'error': 'Page not found.'})
        name, mime = files[path]
        self.reply(200, (STATIC / name).read_bytes(), mime)

    def do_POST(self):
        engine = ENGINES.get(urlparse(self.path).path)
        if engine is None:
            return self.reply(404, {'error': 'Assessment not found.'})
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        if self.headers.get('Host') not in allowed or (origin is not None and origin not in {f'http://{host}' for host in allowed}):
            return self.reply(403, {'error': 'Only same-origin local requests are accepted.'})
        if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            return self.reply(415, {'error': 'Send JSON content.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                raise ValueError('Assessment request is too large or empty.')
            payload = json.loads(self.rfile.read(size))
            engine.validate_request(payload)
        except (ValueError, TypeError, UnicodeError) as error:
            return self.reply(400, {'error': str(error)})
        try:
            result = engine.assess(payload, os.getenv('TYPESAFE_API_KEY', ''))
        except (ValueError, RuntimeError) as error:
            return self.reply(503, {'error': str(error)})
        self.reply(200, result)


def main():
    parser = argparse.ArgumentParser(description='Release Room feedback and release command center')
    parser.add_argument('command', choices=['serve'])
    parser.add_argument('--port', type=int, default=8770)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Release Room at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
