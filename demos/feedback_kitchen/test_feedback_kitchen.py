import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from demos.feedback_kitchen import feedback_kitchen as fk


class FeedbackKitchenTest(unittest.TestCase):
    def setUp(self):
        self.comments = [{'id': f'c{i+1}', 'text': text} for i, text in enumerate(fk.PRODUCTS['recipe']['comments'])]

    def test_baseline_is_only_for_unchanged_examples(self):
        payload = {'product': 'recipe', 'comments': self.comments, 'mode': 'baseline'}
        result = fk.assess(payload)
        self.assertIn('baseline', result['source'])
        self.assertLess(result['supports']['offline'], .4)
        self.comments[0]['text'] = 'My saved list disappears whenever I lose mobile signal.'
        with self.assertRaisesRegex(ValueError, 'Prepared baseline'):
            fk.assess(payload)
        with self.assertRaisesRegex(RuntimeError, 'TYPESAFE_API_KEY'):
            fk.assess({**payload, 'mode': 'live'})

    def test_question_shapes_and_valid_live_parse(self):
        request = fk.make_request('recipe', self.comments)
        self.assertEqual(len(request['questions']), 19)
        answers = {}
        options = list(request['questions']['choice_c1']['criteria'])
        for qid, question in request['questions'].items():
            if qid.startswith('choice_'):
                answers[qid] = {'type': 'choice', 'choice': 'offline', 'confidence': .9, 'probabilities': {x: (1.0 if x == 'offline' else 0.0) for x in options}}
            elif qid.startswith('impact_'):
                answers[qid] = {'type': 'score', 'score': 2, 'confidence': .9, 'probabilities': {'0': 0, '1': 0, '2': 1, '3': 0}}
            else:
                answers[qid] = {'type': 'noul', 'noul': .2}
        body = {'model': 'jev-test', 'answers': answers, 'reasoning': 'Synthetic test rationale'}
        result = fk.assess({'product': 'recipe', 'comments': self.comments, 'mode': 'live'}, 'test-key', lambda request_bytes, key: json.dumps(body).encode())
        self.assertEqual(result['choices']['c1']['suggestion'], 'offline')
        self.assertEqual(result['supports']['offline'], .2)
        self.assertEqual(result['inspection']['response'], body)
        self.assertIn('not Jev thinking', result['inspection']['note'])
        self.assertEqual(result['inspection']['request']['state']['comments'], self.comments)
        body['answers']['choice_c1']['choice'] = []
        with self.assertRaisesRegex(RuntimeError, 'failed'):
            fk.assess({'product': 'recipe', 'comments': self.comments, 'mode': 'live'}, 'test-key', lambda request_bytes, key: json.dumps(body).encode())

    def test_live_http_errors_are_actionable(self):
        payload = {'product': 'recipe', 'comments': self.comments, 'mode': 'live'}
        for status, expected in ((401, 'API key'), (422, 'question schema'), (429, 'rate limited'), (529, 'rate limited'), (500, 'HTTP error')):
            def rejected(body, key):
                raise urllib.error.HTTPError(fk.ENDPOINT, status, 'Rejected', {}, None)
            with self.subTest(status=status), self.assertRaisesRegex(RuntimeError, expected):
                fk.assess(payload, 'test-key', rejected)

    def test_request_limits_and_origin(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), fk.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/api/assess'
        body = json.dumps({'product': 'recipe', 'comments': self.comments, 'mode': 'baseline'}).encode()
        try:
            def send(headers):
                request = urllib.request.Request(url, body, headers, method='POST')
                with urllib.request.urlopen(request) as response:
                    return response.status
            self.assertEqual(send({'Content-Type': 'application/json'}), 200)
            for headers in ({'Content-Type': 'text/plain'}, {'Content-Type': 'application/json', 'Origin': 'http://evil.test'}, {'Content-Type': 'application/json', 'Host': 'evil.test'}):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    send(headers)
                self.assertEqual(caught.exception.code, 400)
                caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
