"""Feedback Kitchen, a local TypeSafe demo with explicit baseline and live modes."""
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
MAX_BODY = 16_384
MAX_REPLY = 1_000_000

PRODUCTS = {
    'recipe': {
        'name': 'Pantry & Co.', 'description': 'A recipe app for the trip from kitchen to shop.',
        'suggestions': [
            {'id': 'offline', 'name': 'Offline shopping lists', 'claim': 'Lists disappear specifically when connectivity drops, so offline access would solve the reported failure.'},
            {'id': 'scale', 'name': 'Adjust serving sizes', 'claim': 'People need recipe quantities recalculated for different serving counts.'},
            {'id': 'substitute', 'name': 'Ingredient swaps', 'claim': 'People need practical substitutes for unavailable ingredients.'},
        ],
        'comments': [
            'This app is useless. I lost my shopping list in the supermarket.',
            'I opened my saved list at the market and it was empty.',
            'Cooking for two means dividing every six-person recipe by three.',
            'The tomato sauce was lovely. No notes!',
            'Could I swap dairy milk for oat milk in this sauce?',
            'I tapped save twice and the list came back after reopening.',
            'I keep losing my list while shopping. It happened again today.',
            'I wish the photographs were bigger on my tablet.',
        ],
        'baseline': [('offline', 2), ('offline', 3), ('scale', 2), ('no_match', 0), ('substitute', 1), ('unclear', 1), ('offline', 2), ('no_match', 0)],
        'support': {'offline': .34, 'scale': .79, 'substitute': .57},
    },
    'timer': {
        'name': 'Morrow Timer', 'description': 'A quiet study timer for focused sessions.',
        'suggestions': [
            {'id': 'resume', 'name': 'Restore interrupted sessions', 'claim': 'Unexpected app interruptions erase an active study session.'},
            {'id': 'quiet', 'name': 'Gentler alerts', 'claim': 'The timer alert disrupts shared quiet study spaces.'},
            {'id': 'history', 'name': 'Session history', 'claim': 'Students need a record of completed focus sessions.'},
        ],
        'comments': [
            'My 40-minute session reset when I answered a phone call.',
            'I hate everything about this timer today.',
            'The alarm startled everyone in the library.',
            'Can I see how many sessions I finished this week?',
            'It opened to zero after my phone restarted mid-session.',
            'The little bell is cute.',
            'I missed the end of my break because my phone was muted.',
            'Three study blocks done. Feels good.',
        ],
        'baseline': [('resume', 2), ('unclear', 0), ('quiet', 2), ('history', 1), ('resume', 3), ('no_match', 0), ('quiet', 1), ('no_match', 0)],
        'support': {'resume': .92, 'quiet': .72, 'history': .59},
    },
    'borrow': {
        'name': 'Neighborly', 'description': 'A small lending shelf for the people nearby.',
        'suggestions': [
            {'id': 'availability', 'name': 'Show item availability', 'claim': 'Borrowers cannot tell whether a listed item is currently available.'},
            {'id': 'returns', 'name': 'Return reminders', 'claim': 'Borrowers forget return dates and need reminders.'},
            {'id': 'distance', 'name': 'Filter by walking distance', 'claim': 'Borrowers need to find items close enough to collect on foot.'},
        ],
        'comments': [
            'I walked over for the drill but it was already lent out.',
            'The ladder listing still said available after I borrowed it.',
            'I forgot the book was due yesterday. Sorry, Maya!',
            'Is there a way to see only things within ten minutes of me?',
            'The whole idea is brilliant.',
            'It takes forever to get a reply from the owner.',
            'A reminder the evening before return would help.',
            'The search result says nearby, then sends me across town.',
        ],
        'baseline': [('availability', 2), ('availability', 2), ('returns', 1), ('distance', 1), ('no_match', 0), ('unclear', 1), ('returns', 1), ('distance', 2)],
        'support': {'availability': .94, 'returns': .83, 'distance': .8},
    },
}


def public_products():
    return {key: {k: v for k, v in product.items() if k not in ('baseline', 'support')} for key, product in PRODUCTS.items()}


def validate_request(payload):
    if not isinstance(payload, dict) or set(payload) != {'product', 'comments', 'mode'}:
        raise ValueError('Choose a product, mode, and comments.')
    product = payload['product']
    if not isinstance(product, str) or product not in PRODUCTS:
        raise ValueError('Choose a listed product.')
    if not isinstance(payload['mode'], str) or payload['mode'] not in ('baseline', 'live'):
        raise ValueError('Choose baseline or live assessment.')
    comments = payload['comments']
    if not isinstance(comments, list) or not 1 <= len(comments) <= 12:
        raise ValueError('Include 1 to 12 comments.')
    seen = set()
    for item in comments:
        if not isinstance(item, dict) or set(item) != {'id', 'text'}:
            raise ValueError('Each comment needs an id and text.')
        if not isinstance(item['id'], str) or not item['id'].isalnum() or len(item['id']) > 32 or item['id'] in seen:
            raise ValueError('Comment ids must be unique letters and numbers.')
        seen.add(item['id'])
        if not isinstance(item['text'], str) or not 3 <= len(item['text'].strip()) <= 500:
            raise ValueError('Comments need 3 to 500 characters.')
    if payload['mode'] == 'baseline' and (len(comments) != 8 or any(item != {'id': f'c{i+1}', 'text': text} for i, (item, text) in enumerate(zip(comments, PRODUCTS[product]['comments'])))):
        raise ValueError('Prepared baseline only covers the original comments. Use Live Jev to assess edits.')
    return product, comments, payload['mode']


def make_request(product, comments):
    suggestions = PRODUCTS[product]['suggestions']
    options = {s['id']: s['name'] + ': ' + s['claim'] for s in suggestions}
    options.update({'unclear': 'A problem is described but the improvement is not clear.', 'no_match': 'No problem or request matches this catalog.'})
    state = {'product': PRODUCTS[product]['name'], 'comments': comments}
    questions = {}
    for item in comments:
        cid = item['id']
        questions['choice_' + cid] = {'type': 'choice', 'instructions': {'comment': item['text'], 'question': 'Which one catalog improvement does `comment` most directly suggest? Do not infer a cause from emotional wording alone.'}, 'criteria': options}
        questions['impact_' + cid] = {'type': 'score', 'instructions': {'comment': item['text'], 'question': 'How much practical disruption does `comment` describe? Ignore emotional intensity and score observed inconvenience or task failure.'}, 'criteria': ['No practical disruption described.', 'A minor inconvenience or unconfirmed difficulty.', 'A meaningful task interruption or repeated workaround.', 'The core task is blocked or repeated work is lost.']}
    for suggestion in suggestions:
        questions['support_' + suggestion['id']] = {'type': 'noul', 'instructions': {'claim': suggestion['claim'], 'question': 'Taken together, do `comments` supply concrete evidence for `claim`? A symptom without its proposed cause does not establish a causal fix. Positive tone alone is not evidence.'}, 'criteria': {'true': 'Comments directly support the specific improvement and causal claim.', 'false': 'Evidence is missing, ambiguous, or only describes a symptom.'}}
    return {'model': MODEL, 'state': state, 'questions': questions}


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1 or not math.isfinite(value):
        raise ValueError('Invalid Jev probability.')
    return float(value)


def distribution(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('Invalid Jev distribution.')
    probs = {key: probability(value[key]) for key in keys}
    if not .98 <= sum(probs.values()) <= 1.02:
        raise ValueError('Invalid Jev distribution.')
    return probs


def parse_response(body, request):
    if not isinstance(body, dict) or not isinstance(body.get('model'), str) or not body['model'].strip() or not isinstance(body.get('answers'), dict):
        raise ValueError('Invalid Jev response.')
    answers = body['answers']
    if set(answers) != set(request['questions']):
        raise ValueError('Jev omitted or added answers.')
    choices = {}
    impacts = {}
    supports = {}
    for qid, question in request['questions'].items():
        answer = answers[qid]
        if not isinstance(answer, dict) or answer.get('type') != question['type']:
            raise ValueError('Invalid Jev answer type.')
        if qid.startswith('choice_'):
            probs = distribution(answer.get('probabilities'), question['criteria'])
            chosen = answer.get('choice')
            if not isinstance(chosen, str) or chosen not in probs or probs[chosen] + 1e-6 < max(probs.values()):
                raise ValueError('Invalid Jev choice.')
            choices[qid[7:]] = {'suggestion': chosen, 'confidence': probability(answer.get('confidence')), 'probabilities': probs}
        elif qid.startswith('impact_'):
            probs = distribution(answer.get('probabilities'), [str(i) for i in range(4)])
            score = answer.get('score')
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 3 or not math.isfinite(score) or abs(score - sum(int(k)*v for k,v in probs.items()) / sum(probs.values())) > .03:
                raise ValueError('Invalid Jev impact score.')
            impacts[qid[7:]] = {'score': score, 'confidence': probability(answer.get('confidence')), 'probabilities': probs}
        else:
            supports[qid[8:]] = probability(answer.get('noul'))
    return {'source': 'Live Jev', 'model': body['model'], 'choices': choices, 'impacts': impacts, 'supports': supports, 'inspection': {'request': request, 'response': body, 'note': 'Jev returns typed judgments. Any returned reasoning fields are preserved below; when absent, no separate written rationale was supplied. Displayed policy explanations are application rules, not Jev thinking.'}}


def baseline(product, comments):
    data = PRODUCTS[product]
    choices = {}
    impacts = {}
    for item, (suggestion, impact) in zip(comments, data['baseline']):
        choices[item['id']] = {'suggestion': suggestion, 'confidence': None}
        impacts[item['id']] = {'score': impact, 'confidence': None}
    return {'source': 'Prepared baseline, illustrative fixture', 'model': None, 'choices': choices, 'impacts': impacts, 'supports': data['support'], 'inspection': {'note': 'Curated baseline for the eight unedited example comments. No Jev API call was made.', 'comments': comments, 'suggestions': data['suggestions']}}


def assess(payload, api_key='', transport=None):
    product, comments, mode = validate_request(payload)
    if mode == 'baseline':
        return baseline(product, comments)
    if not api_key:
        raise RuntimeError('Set TYPESAFE_API_KEY on the server to assess edited feedback with Jev.')
    request = make_request(product, comments)
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
        if error.code == 401:
            message = 'Jev rejected the API key. Check TYPESAFE_API_KEY and retry.'
        elif error.code in (429, 529):
            message = 'Jev is busy or rate limited. Wait briefly and retry.'
        elif error.code == 422:
            message = 'Jev rejected this assessment request. Check the question schema.'
        else:
            message = 'Jev returned an HTTP error. Retry the assessment.'
        raise RuntimeError(message) from error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError) as error:
        raise RuntimeError('Live Jev assessment failed. Check the connection and retry.') from error


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json; charset=utf-8'):
        raw = json.dumps(data).encode() if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/config':
            return self.reply(200, {'products': public_products(), 'liveAvailable': bool(os.getenv('TYPESAFE_API_KEY'))})
        names = {'/': 'index.html', '/app.css': 'app.css', '/app.js': 'app.js'}
        if path not in names:
            return self.reply(404, {'error': 'Page not found.'})
        name = names[path]
        mime = {'index.html': 'text/html', 'app.css': 'text/css', 'app.js': 'text/javascript'}[name]
        self.reply(200, (STATIC / name).read_bytes(), mime + '; charset=utf-8')

    def do_POST(self):
        if urlparse(self.path).path != '/api/assess':
            return self.reply(404, {'error': 'Page not found.'})
        try:
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            if host not in allowed or (origin is not None and origin not in {f'http://{name}' for name in allowed}):
                raise ValueError('Cross-origin requests are not allowed.')
            if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
                raise ValueError('Send JSON to assess feedback.')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                raise ValueError('Assessment request is too large or empty.')
            payload = json.loads(self.rfile.read(size))
            result = assess(payload, os.getenv('TYPESAFE_API_KEY', ''))
            self.reply(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.reply(400, {'error': str(error)})
        except RuntimeError as error:
            self.reply(503, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description='Feedback Kitchen demo')
    parser.add_argument('command', choices=['serve'])
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Feedback Kitchen at http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'env.py'), run_name='__main__')
    main()
