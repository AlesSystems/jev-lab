import copy
import json
import unittest

from jev_habitat import EXAMPLES, ROOMS, evaluate, make_request, parse_response, validate_request


def sample_response(request):
    options = list(request['questions']['action']['criteria'])
    return {
        'model': 'jev-test',
        'answers': {
            'action': {'type': 'choice', 'choice': 'lights', 'confidence': .91, 'probabilities': {key: (1 if key == 'lights' else 0) for key in options}},
            'brightness': {'type': 'score', 'score': 1, 'confidence': .8, 'legend': {str(i): label for i, label in enumerate(request['questions']['brightness']['criteria'])}, 'probabilities': {'0': 0, '1': 1, '2': 0, '3': 0}},
            'applicable': {'type': 'noul', 'noul': .94},
        },
        'usage': {'input_tokens': 100, 'output_tokens': 24},
    }


class HabitatTests(unittest.TestCase):
    def setUp(self):
        self.payload = {'text': EXAMPLES[0]['text'], 'room': EXAMPLES[0]['room'], 'devices': copy.deepcopy(ROOMS[EXAMPLES[0]['room']]['initial']), 'mode': 'fixture'}

    def test_fixture_requires_exact_example_and_state(self):
        self.assertEqual(evaluate(self.payload)['source'], 'Illustrative fixture')
        for field, value in [('text', 'Dim the lights for a film, please'), ('room', 'study')]:
            changed = copy.deepcopy(self.payload)
            changed[field] = value
            with self.assertRaises(ValueError): evaluate(changed)
        changed = copy.deepcopy(self.payload)
        changed['devices']['lights'] = 3
        with self.assertRaises(ValueError): evaluate(changed)

    def test_low_applicability_fixture_has_visible_target(self):
        example = next(item for item in EXAMPLES if item['text'].startswith('Maybe'))
        payload = {'text': example['text'], 'room': example['room'], 'devices': copy.deepcopy(ROOMS[example['room']]['initial']), 'mode': 'fixture'}
        result = evaluate(payload)
        self.assertLess(result['answers']['applicable']['noul'], .7)
        self.assertEqual(result['target'], 3)
        self.assertNotEqual(result['target'], payload['devices']['lights'])

    def test_invalid_boundary(self):
        for key, value in [('room', 'garage'), ('text', ''), ('mode', 'other')]:
            changed = copy.deepcopy(self.payload)
            changed[key] = value
            with self.assertRaises(ValueError): validate_request(changed)
        changed = copy.deepcopy(self.payload)
        changed['devices']['lights'] = True
        with self.assertRaises(ValueError): validate_request(changed)

    def test_live_parser_rejects_malformed_answers(self):
        request = make_request(self.payload)
        valid = sample_response(request)
        valid['reasoning'] = 'Synthetic test rationale'
        self.assertEqual(parse_response(valid, request)['inspection']['response'], valid)
        self.assertIn('not Jev thinking', parse_response(valid, request)['inspection']['note'])
        self.assertEqual(parse_response(valid, request)['answers']['brightness']['score'], 1)
        mutations = [
            lambda b: b['answers']['action']['probabilities'].update({'lights': float('nan')}),
            lambda b: b['answers']['brightness'].update({'score': 3}),
            lambda b: b['answers']['action'].update({'choice': 'music_on'}),
            lambda b: b['answers']['applicable'].update({'noul': 2}),
            lambda b: b['answers'].pop('brightness'),
        ]
        for mutate in mutations:
            body = copy.deepcopy(valid)
            mutate(body)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): parse_response(body, request)

    def test_missing_key_and_provider_failure_do_not_fall_back(self):
        live = {**self.payload, 'mode': 'live'}
        with self.assertRaisesRegex(RuntimeError, 'TYPESAFE_API_KEY'): evaluate(live)
        with self.assertRaises(RuntimeError): evaluate(live, 'key', lambda body, key: b'broken')

    def test_nonlight_score_remains_available_but_unused_by_action(self):
        request = make_request(self.payload)
        body = sample_response(request)
        body['answers']['action']['choice'] = 'music_on'
        body['answers']['action']['probabilities'] = {key: (1 if key == 'music_on' else 0) for key in request['questions']['action']['criteria']}
        parsed = parse_response(body, request)
        self.assertEqual(parsed['answers']['brightness']['score'], 1)
        self.assertEqual(parsed['action'], 'music_on')
        self.assertIsNone(parsed['target'])


if __name__ == '__main__': unittest.main()
