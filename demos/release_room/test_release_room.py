import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from demos.release_room import release_room as room


class ReleaseRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), room.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, payload, headers=None):
        request = urllib.request.Request(self.url + path, json.dumps(payload).encode(), headers or {'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def feedback_payload(self):
        return {'product': 'recipe', 'mode': 'baseline', 'comments': [{'id': f'c{i+1}', 'text': text} for i, text in enumerate(room.feedback.PRODUCTS['recipe']['comments'])]}

    def test_release_blockers_cannot_be_removed_by_evidence_selection(self):
        status, result = self.post('/api/release', {'release': 'friday', 'selected': [], 'mode': 'fixture'})
        self.assertEqual(status, 200)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['blocked_by'], ['fr_retry', 'fr_rollback'])

    def test_ready_fixture_and_edited_feedback_rejection(self):
        selected = [item['id'] for item in room.release.RELEASES['midnight']['evidence']]
        status, result = self.post('/api/release', {'release': 'midnight', 'selected': selected, 'mode': 'fixture'})
        self.assertEqual((status, result['status'], result['support']), (200, 'supported', .9))
        payload = self.feedback_payload()
        self.assertEqual(self.post('/api/feedback', payload)[0], 200)
        payload['comments'][0]['text'] = 'The shopping list disappears offline.'
        status, result = self.post('/api/feedback', payload)
        self.assertEqual(status, 400)
        self.assertIn('only covers the original', result['error'])

    def test_live_trace_is_forwarded_without_loss(self):
        request = room.release.request_body('midnight', [])
        raw = {'model': 'jev-test', 'answers': room.release.fixture_answers('midnight', [], request), 'reasoning': 'Provider-returned text', 'extra': [1, 2]}
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': 'test-key'}), patch.object(room.release, 'live_answers', return_value=raw):
            status, result = self.post('/api/release', {'release': 'midnight', 'selected': [], 'mode': 'live'})
        self.assertEqual(status, 200)
        self.assertEqual(result['inspection']['request'], request)
        self.assertEqual(result['inspection']['response'], raw)

    def test_failure_is_independent_and_does_not_fall_back(self):
        with patch.object(room.feedback, 'assess', side_effect=RuntimeError('Jev unavailable')):
            status, result = self.post('/api/feedback', self.feedback_payload())
        self.assertEqual((status, result), (503, {'error': 'Jev unavailable'}))
        self.assertEqual(self.post('/api/release', {'release': 'friday', 'selected': [], 'mode': 'fixture'})[0], 200)

    def test_boundary_rejects_foreign_origin_invalid_json_shape_and_content_type(self):
        payload = {'release': 'friday', 'selected': [], 'mode': 'fixture'}
        self.assertEqual(self.post('/api/release', payload, {'Content-Type': 'application/json', 'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.post('/api/release', payload, {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.post('/api/release', {'release': []})[0], 400)
        self.assertEqual(self.post('/api/release', {'release': 'friday', 'selected': ['unknown'], 'mode': 'fixture'})[0], 400)

    def test_config_only_exposes_public_product_data(self):
        with patch.dict('os.environ', {'TYPESAFE_API_KEY': 'test-secret'}), urllib.request.urlopen(self.url + '/api/config') as response:
            data = response.read()
        config = json.loads(data)
        self.assertTrue(config['live_available'])
        self.assertNotIn(b'test-secret', data)
        self.assertNotIn('baseline', config['products']['recipe'])


if __name__ == '__main__':
    unittest.main()
