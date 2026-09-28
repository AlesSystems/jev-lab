from __future__ import annotations

import argparse
import json
import math
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

STATIC = Path(__file__).with_name('static')
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-latest'
MAX_REQUEST = 4096
MAX_RESPONSE = 1_000_000
CHECKS = ('browser', 'load', 'rollback')


def card(id, title, text, kind, status, check=None, required=False):
    return dict(id=id, title=title, text=text, kind=kind, status=status, check=check, required=required)


RELEASES = {
    'friday': {
        'name': 'Friday Checkout', 'summary': 'A calmer checkout with a retry path for declined payments.',
        'claim': 'Checkout is ready for release.', 'hours': 18,
        'metrics': [
            dict(id='completion', label='Checkout completion', unit='%', values=[92, 94, 95, 96, 96, 97], note='Steady completion in staging; these numbers are synthetic.', related=['fr_browser', 'fr_comment']),
            dict(id='errors', label='Payment errors', unit='%', values=[2.8, 2.1, 1.7, 1.4, 1.2, 1.1], note='A falling aggregate can hide retries that still fail.', related=['fr_retry', 'fr_load']),
            dict(id='latency', label='P95 response', unit='ms', values=[420, 400, 380, 370, 355, 350], note='Illustrative staging traffic, not production telemetry.', related=['fr_load', 'fr_rollback']),
        ],
        'evidence': [
            card('fr_browser', 'Browser purchase flow', 'A full purchase passes on Chrome, Firefox, and Safari in staging.', 'test', 'pass', 'browser', True),
            card('fr_retry', 'Payment retry runs', 'Retries failed in two staging runs after a declined card.', 'test', 'fail', 'payment retry', True),
            card('fr_comment', 'Local confidence', 'Checkout seems fine locally. We should be good for Friday.', 'note', 'unverified'),
            card('fr_load', 'Load run', 'The load suite passed at expected launch traffic.', 'test', 'pass', 'load'),
            card('fr_rollback', 'Rollback drill', 'No rollback check has been run for the payment path.', 'test', 'missing', 'rollback', True),
            card('fr_flaky', 'Promo code rerun', 'Promo code test passed twice and failed once without a clear cause.', 'test', 'flaky', 'promo'),
        ],
    },
    'midnight': {
        'name': 'Midnight Migration', 'summary': 'Move account preferences to a new store overnight.',
        'claim': 'The migration is ready for release.', 'hours': 6,
        'metrics': [
            dict(id='lag', label='Queue lag', unit='s', values=[12, 19, 36, 55, 82, 104], note='The sharp climb came from a paused replay worker; it recovered after restart.', related=['mi_lag', 'mi_load']),
            dict(id='writes', label='Write success', unit='%', values=[99, 99, 98, 99, 99, 99], note='Synthetic write success in a staging replay.', related=['mi_browser', 'mi_dual']),
            dict(id='latency', label='P95 read', unit='ms', values=[98, 108, 112, 110, 106, 101], note='Synthetic read latency stayed near baseline.', related=['mi_load', 'mi_rollback']),
        ],
        'evidence': [
            card('mi_browser', 'Browser preference save', 'Saving and reloading preferences passes in the staging browser run.', 'test', 'pass', 'browser', True),
            card('mi_lag', 'Lag investigation', 'The replay worker was paused during the spike; queue lag fell after it resumed.', 'note', 'explained'),
            card('mi_rollback', 'Rollback drill', 'A staging rollback restored the old read path and preserved new writes.', 'test', 'pass', 'rollback', True),
            card('mi_load', 'Replay load run', 'The full replay completed at expected traffic with no dropped writes.', 'test', 'pass', 'load', True),
            card('mi_dual', 'Dual-write comparison', 'Older preference records match in the completed staging comparison.', 'test', 'pass', 'data comparison'),
            card('mi_chat', 'Team note', 'The lag graph looks scary. Maybe hold until we know why.', 'note', 'unverified'),
        ],
    },
    'profile': {
        'name': 'Profile Glow-Up', 'summary': 'Refresh profile editing and photo upload.',
        'claim': 'The new profile editor is ready for release.', 'hours': 42,
        'metrics': [
            dict(id='completion', label='Edit completion', unit='%', values=[77, 79, 82, 84, 85, 86], note='Synthetic task completion rose in the staged flow.', related=['pr_browser', 'pr_note']),
            dict(id='errors', label='Upload errors', unit='%', values=[4.0, 3.1, 2.4, 1.9, 1.4, 1.2], note='Aggregate upload errors improved, but a flaky mobile case remains.', related=['pr_mobile', 'pr_load']),
            dict(id='latency', label='Save latency', unit='ms', values=[710, 680, 650, 620, 600, 590], note='Synthetic p95 save time from staged traffic.', related=['pr_load', 'pr_rollback']),
        ],
        'evidence': [
            card('pr_browser', 'Desktop browser flow', 'Editing a profile and uploading a photo passes in two desktop browsers.', 'test', 'pass', 'browser', True),
            card('pr_mobile', 'Mobile photo upload', 'Mobile upload passed three runs and failed one; cause is unknown.', 'test', 'flaky', 'mobile upload', True),
            card('pr_rollback', 'Rollback drill', 'The old editor can be restored and edited profiles remain intact.', 'test', 'pass', 'rollback', True),
            card('pr_load', 'Image load run', 'Image service load run passed at expected launch traffic.', 'test', 'pass', 'load'),
            card('pr_note', 'Design review', 'The new profile flow feels much nicer. Ship it.', 'note', 'unverified'),
            card('pr_a11y', 'Keyboard pass', 'Keyboard editing and focus order passed in staging.', 'test', 'pass', 'accessibility'),
        ],
    },
}
FIXTURES = {
    'friday': dict(scores={'fr_comment': 0.9}, next_check='rollback', support=0.12),
    'midnight': dict(scores={'mi_lag': 1.0, 'mi_chat': 1.2}, next_check='browser', support=0.9),
    'profile': dict(scores={'pr_note': 0.6}, next_check='browser', support=0.68),
}


class AssessmentError(ValueError):
    pass


def validate_request(payload):
    if not isinstance(payload, dict) or set(payload) != {'release', 'selected', 'mode'}:
        raise AssessmentError('Choose a release, evidence cards, and assessment mode.')
    release_id, selected, mode = payload['release'], payload['selected'], payload['mode']
    if not isinstance(release_id, str) or release_id not in RELEASES:
        raise AssessmentError('Unknown release.')
    if mode not in ('fixture', 'live'):
        raise AssessmentError('Unknown assessment mode.')
    ids = {item['id'] for item in RELEASES[release_id]['evidence']}
    if not isinstance(selected, list) or len(selected) > 6 or any(not isinstance(item, str) for item in selected) or len(selected) != len(set(selected)) or not set(selected) <= ids:
        raise AssessmentError('Choose unique evidence cards from this release.')
    return release_id, selected, mode


def request_body(release_id, selected):
    release = RELEASES[release_id]
    included = [item for item in release['evidence'] if item['id'] in selected]
    findings = included
    state = {
        'release': release['name'], 'claim': release['claim'],
        'metrics': [dict(label=metric['label'], unit=metric['unit'], values=metric['values']) for metric in release['metrics']],
        'evidence': included,
        'required_checks': [dict(check=item['check'], status=item['status']) for item in release['evidence'] if item['required'] and item['status'] != 'pass'],
    }
    questions = {}
    for item in findings:
        questions['score_' + item['id']] = {
            'type': 'score',
            'instructions': f"How concerning is the finding in `evidence` with id {item['id']} for this release? Judge the concrete issue, not the writer's confidence or emotion.",
            'criteria': [
                'No concrete release risk is described.',
                'A possible issue is described without a reproduced failure.',
                'A credible issue needs a focused check before shipping.',
                'A reproduced serious failure threatens the release.',
            ],
        }
    questions['next_check'] = {
        'type': 'choice',
        'instructions': 'Which single next check most reduces uncertainty for `claim`, given `evidence` and `required_checks`?',
        'criteria': {
            'browser': 'Run a cross-browser user journey.',
            'load': 'Test behavior under expected traffic.',
            'rollback': 'Verify the release can be safely rolled back.',
            'targeted': 'Reproduce a specific failed or flaky case.',
        },
    }
    questions['support'] = {
        'type': 'noul',
        'instructions': 'Does the selected `evidence` support `claim`? Treat confident comments as assertions, not test results. A missing or failed required check weakens support.',
        'criteria': {'true': 'Specific passing tests cover the claim and no relevant contradiction remains.', 'false': 'Evidence is absent, contradictory, incomplete, or only reassuring wording.'},
    }
    return {'model': MODEL, 'state': state, 'questions': questions}


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssessmentError('Invalid Jev probability.')
    try:
        number = float(value)
    except OverflowError as error:
        raise AssessmentError('Invalid Jev probability.') from error
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise AssessmentError('Invalid Jev probability.')
    return number


def distribution(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise AssessmentError('Invalid Jev distribution.')
    weights = {key: probability(value[key]) for key in keys}
    if not 0.98 <= sum(weights.values()) <= 1.02:
        raise AssessmentError('Invalid Jev distribution.')
    return weights


def parse_answers(payload, questions):
    if not isinstance(payload, dict) or not isinstance(payload.get('model'), str) or not payload['model'] or not isinstance(payload.get('answers'), dict):
        raise AssessmentError('Invalid Jev response.')
    answers = payload['answers']
    if not set(questions) <= set(answers):
        raise AssessmentError('Jev omitted an answer.')
    for qid, question in questions.items():
        answer = answers[qid]
        if not isinstance(answer, dict) or answer.get('type') != question['type']:
            raise AssessmentError('Invalid Jev answer.')
        if question['type'] == 'score':
            weights = distribution(answer.get('probabilities'), ('0', '1', '2', '3'))
            score = answer.get('score')
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 3 or abs(float(score) - sum(int(k) * p for k, p in weights.items()) / sum(weights.values())) > 0.03:
                raise AssessmentError('Invalid Jev score.')
            probability(answer.get('confidence'))
        elif question['type'] == 'choice':
            weights = distribution(answer.get('probabilities'), tuple(question['criteria']))
            if not isinstance(answer.get('choice'), str) or answer['choice'] not in weights or weights[answer['choice']] + 0.000001 < max(weights.values()):
                raise AssessmentError('Invalid Jev choice.')
            probability(answer.get('confidence'))
        else:
            probability(answer.get('noul'))
    return {qid: answers[qid] for qid in questions}


def fixture_answers(release_id, selected, body):
    release = RELEASES[release_id]
    selected_set = set(selected)
    included = [item for item in release['evidence'] if item['id'] in selected_set]
    required_bad = any(item['required'] and item['status'] != 'pass' for item in release['evidence'])
    has_strong = any(item['kind'] == 'test' and item['status'] == 'pass' for item in included)
    contradictory = any(item['status'] in ('fail', 'flaky', 'missing') for item in included)
    base = FIXTURES[release_id]
    support = base['support'] if has_strong else min(base['support'], 0.18)
    if contradictory:
        support = min(support, 0.35)
    if required_bad:
        support = min(support, 0.45)
    answers = {}
    for qid, question in body['questions'].items():
        if question['type'] == 'score':
            finding = next(item for item in included if item['id'] == qid[6:])
            score = base['scores'].get(qid[6:], {'pass': 0.2, 'fail': 2.9, 'flaky': 2.2, 'missing': 2.0, 'explained': 0.5, 'unverified': 0.7}[finding['status']])
            lo = int(score)
            weights = {str(i): 0.0 for i in range(4)}
            weights[str(lo)] = 1 - (score - lo)
            if lo < 3:
                weights[str(lo + 1)] = score - lo
            answers[qid] = dict(type='score', score=score, confidence=0.82, probabilities=weights)
        elif question['type'] == 'choice':
            check = 'targeted' if any(item['required'] and item['status'] in ('fail', 'flaky') for item in release['evidence']) else 'rollback' if any(item['required'] and item['status'] == 'missing' for item in release['evidence']) else base['next_check']
            weights = {key: (0.85 if key == check else 0.05) for key in question['criteria']}
            answers[qid] = dict(type='choice', choice=check, confidence=0.8, probabilities=weights)
        else:
            answers[qid] = dict(type='noul', noul=support)
    return answers


def live_answers(body, api_key, transport=None):
    encoded = json.dumps(body).encode()
    if transport is None:
        request = urllib.request.Request(ENDPOINT, encoded, {'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                message = 'Live Jev rejected the API key. Check TYPESAFE_API_KEY.'
            elif error.code == 422:
                message = 'Live Jev rejected the assessment payload. Check the server integration.'
            elif error.code == 429:
                message = 'Live Jev rate limit reached. Retry later.'
            elif error.code in (502, 503, 529):
                message = 'Live Jev is overloaded. Retry later.'
            else:
                message = 'Live Jev is unavailable. Retry later.'
            raise AssessmentError(message) from error
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            raise AssessmentError('Live Jev is unavailable. Retry or select fixture mode.') from error
    else:
        try:
            raw = transport(encoded, api_key)
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            raise AssessmentError('Live Jev is unavailable. Retry or select fixture mode.') from error
    if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
        raise AssessmentError('Invalid Jev response size.')
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise AssessmentError('Invalid Jev response JSON.') from error
    return payload


def assess(payload, api_key=None, transport=None):
    release_id, selected, mode = validate_request(payload)
    release = RELEASES[release_id]
    body = request_body(release_id, selected)
    if mode == 'live':
        if not api_key:
            raise AssessmentError('Live Jev needs TYPESAFE_API_KEY on the server.')
        raw = live_answers(body, api_key, transport)
        answers = parse_answers(raw, body['questions'])
        model = raw['model']
    else:
        answers = fixture_answers(release_id, selected, body)
        answers = parse_answers({'model': 'hand-authored fixture', 'answers': answers}, body['questions'])
        model = 'hand-authored fixture'
    required = [item for item in release['evidence'] if item['required']]
    blocked = [item for item in required if item['status'] in ('fail', 'missing', 'flaky')]
    support = answers['support']['noul']
    status = 'blocked' if blocked else 'supported' if support >= 0.8 else 'needs review'
    return {
        'release': release_id, 'selected': selected, 'mode': mode, 'model': model,
        'status': status, 'support': support, 'next_check': answers['next_check']['choice'],
        'blocked_by': [item['id'] for item in blocked],
        'answers': answers, 'input': body,
    }


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/config':
            self.respond(200, {'releases': RELEASES, 'live_available': bool(os.getenv('TYPESAFE_API_KEY'))})
            return
        filename = 'index.html' if path == '/' else path.removeprefix('/')
        if filename not in ('index.html', 'app.css', 'app.js'):
            self.send_error(404)
            return
        data = (STATIC / filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', {'index.html': 'text/html', 'app.css': 'text/css', 'app.js': 'text/javascript'}[filename] + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlparse(self.path).path != '/api/assess':
            self.send_error(404)
            return
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        if host not in ('127.0.0.1:' + str(self.server.server_port), 'localhost:' + str(self.server.server_port)) or (origin and origin not in ('http://127.0.0.1:' + str(self.server.server_port), 'http://localhost:' + str(self.server.server_port))):
            self.respond(403, {'error': 'Only same-origin local requests are accepted.'})
            return
        if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            self.respond(415, {'error': 'Send JSON content.'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > MAX_REQUEST:
                raise AssessmentError('Assessment request is too large or empty.')
            payload = json.loads(self.rfile.read(size))
            release_id, selected, mode = validate_request(payload)
        except (ValueError, UnicodeError) as error:
            self.respond(400, {'error': str(error)})
            return
        try:
            result = assess(payload, os.getenv('TYPESAFE_API_KEY'))
        except AssessmentError as error:
            self.respond(503 if mode == 'live' else 500, {'error': str(error)})
            return
        self.respond(200, result)


def main():
    parser = argparse.ArgumentParser(description='Launch Lab synthetic release demo')
    parser.add_argument('command', nargs='?', choices=('serve',), help='Serve the local demo')
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    if args.command != 'serve':
        parser.print_help()
        return
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Launch Lab at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
