import http.client
import io
import json
import threading
import urllib.error
from unittest.mock import patch
import unittest
from http.server import ThreadingHTTPServer

from demos.launch_lab import launch_lab as lab


class AssessmentTests(unittest.TestCase):
    def test_catalog_shape_and_rules(self):
        self.assertEqual(len(lab.RELEASES), 3)
        for release in lab.RELEASES.values():
            self.assertEqual(len(release['evidence']), 6)
            self.assertEqual(len(release['metrics']), 3)
        friday = list(item['id'] for item in lab.RELEASES['friday']['evidence'])
        assessed = lab.assess({'release': 'friday', 'selected': ['fr_comment'], 'mode': 'fixture'})
        self.assertEqual(assessed['status'], 'blocked')
        self.assertEqual(set(assessed['blocked_by']), {'fr_retry', 'fr_rollback'})
        self.assertLess(assessed['support'], .2)
        self.assertEqual(assessed['input']['state']['evidence'][0]['id'], 'fr_comment')
        self.assertNotIn('fr_browser', json.dumps(assessed['input']))
        self.assertEqual(lab.assess({'release': 'midnight', 'selected': [item['id'] for item in lab.RELEASES['midnight']['evidence']], 'mode': 'fixture'})['status'], 'supported')
        self.assertEqual(lab.assess({'release': 'profile', 'selected': [item['id'] for item in lab.RELEASES['profile']['evidence']], 'mode': 'fixture'})['status'], 'blocked')

    def test_input_and_response_boundaries(self):
        for payload in (
            {'release': 'friday', 'selected': ['fr_browser', 'fr_browser'], 'mode': 'fixture'},
            {'release': 'friday', 'selected': ['mi_browser'], 'mode': 'fixture'},
            {'release': 'other', 'selected': [], 'mode': 'fixture'},
        ):
            with self.assertRaises(lab.AssessmentError):
                lab.assess(payload)
        with self.assertRaises(lab.AssessmentError):
            lab.assess({'release': 'friday', 'selected': [], 'mode': 'live'})
        body = lab.request_body('friday', ['fr_comment'])
        valid = lab.assess({'release': 'friday', 'selected': ['fr_comment'], 'mode': 'fixture'})['answers']
        invalid = json.loads(json.dumps(valid))
        invalid['next_check']['choice'] = []
        with self.assertRaises(lab.AssessmentError):
            lab.parse_answers({'model': 'jev', 'answers': invalid}, body['questions'])
        with self.assertRaises(lab.AssessmentError):
            lab.probability(10**1000)

    def test_live_http_errors_have_actionable_messages(self):
        body = lab.request_body('friday', [])
        expected = {
            401: 'API key',
            422: 'payload',
            429: 'rate limit',
            529: 'overloaded',
        }
        for code, phrase in expected.items():
            with self.subTest(code=code):
                error = urllib.error.HTTPError(lab.ENDPOINT, code, 'failure', {}, io.BytesIO(b''))
                with patch.object(lab.urllib.request, 'urlopen', side_effect=error):
                    try:
                        with self.assertRaisesRegex(lab.AssessmentError, phrase):
                            lab.live_answers(body, 'secret')
                    finally:
                        error.close()

    def test_live_retains_typed_answers_and_rejects_malformed(self):
        selected = ['mi_browser', 'mi_lag']
        fixture = lab.assess({'release': 'midnight', 'selected': selected, 'mode': 'fixture'})
        self.assertIsNone(fixture['inspection'])
        raw_response = {'model': 'jev-latest', 'answers': fixture['answers'], 'reasoning': 'Synthetic test rationale', 'usage': {'input_tokens': 42}}
        def transport(body, key):
            self.assertEqual(key, 'secret')
            self.assertEqual(json.loads(body)['state']['evidence'][0]['id'], 'mi_browser')
            return json.dumps(raw_response).encode()
        result = lab.assess({'release': 'midnight', 'selected': selected, 'mode': 'live'}, 'secret', transport)
        self.assertEqual(result['mode'], 'live')
        self.assertEqual(result['answers'], fixture['answers'])
        self.assertEqual(result['inspection']['request'], result['input'])
        self.assertEqual(result['inspection']['response'], raw_response)
        with self.assertRaises(lab.AssessmentError):
            lab.assess({'release': 'midnight', 'selected': selected, 'mode': 'live'}, 'secret', lambda *_: b'{bad')


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), lab.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, payload=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        data = json.dumps(payload).encode() if payload is not None else None
        common = {'Host': f'127.0.0.1:{self.server.server_port}', 'Content-Type': 'application/json'}
        common.update(headers or {})
        conn.request(method, path, data, common)
        response = conn.getresponse()
        status, body = response.status, response.read()
        conn.close()
        return status, body

    def test_get_and_assessment(self):
        status, data = self.request('GET', '/api/config')
        self.assertEqual(status, 200)
        self.assertIn('friday', json.loads(data)['releases'])
        status, data = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'Would you ship', data)
        status, data = self.request('POST', '/api/assess', {'release': 'friday', 'selected': ['fr_comment'], 'mode': 'fixture'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)['status'], 'blocked')

    def test_http_boundary(self):
        payload = {'release': 'friday', 'selected': [], 'mode': 'fixture'}
        self.assertEqual(self.request('POST', '/api/assess', payload, {'Origin': 'http://evil.test'})[0], 403)
        self.assertEqual(self.request('POST', '/api/assess', payload, {'Host': 'evil.test'})[0], 403)
        self.assertEqual(self.request('POST', '/api/assess', payload, {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request('POST', '/api/assess', {'release': 'wrong', 'selected': [], 'mode': 'fixture'})[0], 400)
        self.assertEqual(self.request('POST', '/api/assess', {'release': 'friday', 'selected': [], 'mode': 'live'})[0], 503)
        self.assertEqual(self.request('GET', '/secret')[0], 404)


if __name__ == '__main__':
    unittest.main()
