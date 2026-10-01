from __future__ import annotations

import argparse
import json
import math
import os
import runpy
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

STATIC = Path(__file__).with_name('static')
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-latest'
MAX_BODY = 8192
MAX_REPLY = 1_000_000
ROOMS = {
    'living': {'name': 'Living room', 'initial': {'lights': 2, 'music': False, 'blinds': 'open'}},
    'bedroom': {'name': 'Bedroom', 'initial': {'lights': 1, 'music': False, 'blinds': 'closed'}},
    'study': {'name': 'Study', 'initial': {'lights': 3, 'music': False, 'blinds': 'open'}},
}
EXAMPLES = [
    {'room': 'living', 'text': 'Dim the lights for a film.', 'action': 'lights', 'brightness': 1, 'applicable': .96},
    {'room': 'bedroom', 'text': 'Open the blinds.', 'action': 'blinds_open', 'brightness': 2, 'applicable': .98},
    {'room': 'study', 'text': 'Put some music on.', 'action': 'music_on', 'brightness': 2, 'applicable': .95},
    {'room': 'living', 'text': 'Maybe make the lights a bit brighter.', 'action': 'lights', 'brightness': 3, 'applicable': .58},
    {'room': 'living', 'text': 'What is the weather tomorrow?', 'action': 'no_change', 'brightness': 2, 'applicable': .04},
]
ACTIONS = {
    'lights': 'Set this room’s lights. Brightness comes from the separate Score answer.',
    'music_on': 'Turn this room’s music on.',
    'music_off': 'Turn this room’s music off.',
    'blinds_open': 'Open this room’s blinds.',
    'blinds_close': 'Close this room’s blinds.',
    'no_change': 'No single supported room action; includes questions, ambiguity, multiple actions, or unrelated requests.',
}
BRIGHTNESS = ['Off: explicitly turn the lights off.', 'Dim: low ambient lighting.', 'Reading: medium task lighting.', 'Bright: full lighting.']


def validate_request(payload):
    if not isinstance(payload, dict) or set(payload) != {'text', 'room', 'devices', 'mode'}:
        raise ValueError('Send text, room, devices, and mode.')
    if not isinstance(payload['room'], str) or payload['room'] not in ROOMS:
        raise ValueError('Choose a listed room.')
    if not isinstance(payload['text'], str) or not 1 <= len(payload['text'].strip()) <= 300:
        raise ValueError('Enter 1 to 300 characters of request text.')
    if payload['mode'] not in ('fixture', 'live'):
        raise ValueError('Choose fixture or live mode.')
    devices = payload['devices']
    if not isinstance(devices, dict) or set(devices) != {'lights', 'music', 'blinds'} or type(devices['lights']) is not int or devices['lights'] not in range(4) or type(devices['music']) is not bool or devices['blinds'] not in ('open', 'closed'):
        raise ValueError('Invalid room device snapshot.')
    return payload


def make_request(payload):
    return {'model': MODEL, 'state': {'request': payload['text'], 'selected_room': payload['room'], 'devices': payload['devices'], 'available_rooms': list(ROOMS)}, 'questions': {
        'action': {'type': 'choice', 'instructions': 'Which one supported change does `request` ask for in `selected_room`? Use no_change for multiple actions, ambiguity, questions, unrelated requests, or no actual change. Choose a single action without assuming permission for real devices.', 'criteria': ACTIONS},
        'brightness': {'type': 'score', 'instructions': 'If `request` asks to set lighting in `selected_room`, which brightness is requested? This is a speculative lighting question. Ignore it unless action is lights.', 'criteria': BRIGHTNESS},
        'applicable': {'type': 'noul', 'instructions': 'Does `request` express one applicable, actionable change to a supported device in `selected_room`, given the current `devices` state? A question, unclear request, multiple actions, unrelated request, or already-satisfied state means no.', 'criteria': {'true': 'One clear supported change to the selected room remains.', 'false': 'No clear single change to apply.'}},
    }}


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Invalid Jev probability.')
    return float(value)


def distribution(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('Invalid Jev distribution.')
    result = {key: probability(value[key]) for key in keys}
    if not .98 <= sum(result.values()) <= 1.02:
        raise ValueError('Invalid Jev distribution.')
    return result


def parse_response(body, request):
    if not isinstance(body, dict) or not isinstance(body.get('model'), str) or not body['model'].strip() or not isinstance(body.get('answers'), dict) or set(body['answers']) != set(request['questions']):
        raise ValueError('Invalid Jev response.')
    answers = body['answers']
    action = answers['action']
    brightness = answers['brightness']
    applicable = answers['applicable']
    if any(not isinstance(answer, dict) or answer.get('type') != kind for answer, kind in ((action, 'choice'), (brightness, 'score'), (applicable, 'noul'))):
        raise ValueError('Invalid Jev answer type.')
    action_probs = distribution(action.get('probabilities'), ACTIONS)
    chosen = action.get('choice')
    if not isinstance(chosen, str) or chosen not in ACTIONS or action_probs[chosen] + 1e-6 < max(action_probs.values()):
        raise ValueError('Invalid Jev choice.')
    score_probs = distribution(brightness.get('probabilities'), [str(i) for i in range(4)])
    score = brightness.get('score')
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 3 or abs(score - sum(i * score_probs[str(i)] for i in range(4)) / sum(score_probs.values())) > .03:
        raise ValueError('Invalid Jev brightness score.')
    if brightness.get('legend') != {str(i): label for i, label in enumerate(BRIGHTNESS)}:
        raise ValueError('Invalid Jev brightness legend.')
    normalized = {'action': {'choice': chosen, 'confidence': probability(action.get('confidence')), 'probabilities': action_probs}, 'brightness': {'score': float(score), 'confidence': probability(brightness.get('confidence')), 'probabilities': score_probs}, 'applicable': {'noul': probability(applicable.get('noul'))}}
    usage = body.get('usage')
    if usage is not None and (not isinstance(usage, dict) or any(type(usage.get(key)) is not int or usage[key] < 0 for key in ('input_tokens', 'output_tokens'))):
        raise ValueError('Invalid Jev usage.')
    return {'source': 'Live Jev', 'model': body['model'], 'action': chosen, 'target': round(score) if chosen == 'lights' else None, 'answers': normalized, 'usage': usage, 'inspection': {'request': request, 'response': body, 'note': 'Jev returns typed judgments. Any returned reasoning fields are preserved below; when absent, no separate written rationale was supplied. Displayed policy explanations are application rules, not Jev thinking.'}}


def fixture(payload):
    match = next((example for example in EXAMPLES if example['room'] == payload['room'] and example['text'] == payload['text'] and payload['devices'] == ROOMS[example['room']]['initial']), None)
    if match is None:
        raise ValueError('This exact fixture only covers its original room and device state. Use Live Jev for edits or changed rooms.')
    options = {key: float(key == match['action']) for key in ACTIONS}
    levels = {str(i): float(i == match['brightness']) for i in range(4)}
    answers = {'action': {'choice': match['action'], 'confidence': 1, 'probabilities': options}, 'brightness': {'score': match['brightness'], 'confidence': 1, 'probabilities': levels}, 'applicable': {'noul': match['applicable']}}
    request = make_request(payload)
    return {'source': 'Illustrative fixture', 'model': None, 'action': match['action'], 'target': match['brightness'] if match['action'] == 'lights' else None, 'answers': answers, 'usage': None, 'inspection': {'request': request, 'response': {'note': 'Prepared illustrative answers. No Jev API call occurred.', 'answers': answers}}}


def evaluate(payload, api_key='', transport=None):
    validate_request(payload)
    if payload['mode'] == 'fixture':
        return fixture(payload)
    if not api_key:
        raise RuntimeError('Set TYPESAFE_API_KEY on the server to use Live Jev.')
    request = make_request(payload)
    body = json.dumps(request).encode()
    try:
        if transport is None:
            req = urllib.request.Request(ENDPOINT, body, {'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=35) as response:
                raw = response.read(MAX_REPLY + 1)
        else:
            raw = transport(body, api_key)
        if not isinstance(raw, bytes) or len(raw) > MAX_REPLY:
            raise ValueError('Jev response exceeded limit.')
        return parse_response(json.loads(raw), request)
    except urllib.error.HTTPError as error:
        error.close()
        message = {401: 'Jev rejected the API key. Check TYPESAFE_API_KEY.', 422: 'Jev rejected the question schema.', 429: 'Jev is rate limited. Wait and retry.', 529: 'Jev is busy. Wait and retry.'}.get(error.code, 'Jev returned an HTTP error. Retry.')
        raise RuntimeError(message) from error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError) as error:
        raise RuntimeError('Live Jev failed. Check the connection and retry.') from error


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json; charset=utf-8'):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/config':
            return self.reply(200, {'rooms': ROOMS, 'examples': EXAMPLES, 'liveAvailable': bool(os.getenv('TYPESAFE_API_KEY'))})
        names = {'/': 'index.html', '/app.css': 'app.css', '/app.js': 'app.js'}
        if path not in names:
            return self.reply(404, {'error': 'Page not found.'})
        name = names[path]
        mime = {'index.html': 'text/html', 'app.css': 'text/css', 'app.js': 'text/javascript'}[name]
        self.reply(200, (STATIC / name).read_bytes(), mime + '; charset=utf-8')

    def do_POST(self):
        if urlparse(self.path).path != '/api/evaluate':
            return self.reply(404, {'error': 'Page not found.'})
        try:
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            if host not in allowed or (origin is not None and origin not in {f'http://{name}' for name in allowed}):
                raise ValueError('Cross-origin requests are not allowed.')
            if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
                raise ValueError('Send JSON to evaluate.')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                raise ValueError('Evaluation request is too large or empty.')
            self.reply(200, evaluate(json.loads(self.rfile.read(size)), os.getenv('TYPESAFE_API_KEY', '')))
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.reply(400, {'error': str(error)})
        except RuntimeError as error:
            self.reply(503, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description='Run Jev Habitat locally.')
    parser.add_argument('command', choices=['serve'])
    parser.add_argument('--port', type=int, default=8777)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Jev Habitat: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'env.py'), run_name='__main__')
    main()
