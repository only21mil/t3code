"""notice-package-20261023 item 7 in sats-completion-notify: (b) any non-2xx body's error code is kept and logged,
bounded and scrubbed, instead of an allowlist; (c) a failed drainer kick is an error line, never silence.
State goes to a directory under TMPDIR; nothing reaches the network or systemd."""
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
import urllib.error
from unittest.mock import patch

NOTIFIER = Path(os.environ.get('NOTIFIER_SOURCE', Path(__file__).resolve().parents[1] / 'sats-completion-notify'))
# Key-shaped values for the masking checks, built at runtime so no key-shaped literal sits in source.
FAKE_KEY = 'sk' + '-ant-' + 'Fixture' + ''.join(map(str, range(10))) + 'NotARealKeyAtAll'
MIXED = 'Ab' + '3' * 12 + 'cD' + '9' * 12


def load():
    module = types.ModuleType('notify_under_test')
    module.__file__ = str(NOTIFIER)
    exec(compile(NOTIFIER.read_bytes(), str(NOTIFIER), 'exec'), module.__dict__)
    return module


class Body:
    def __init__(self, raw):
        self.stream = io.BytesIO(raw)

    def read(self, size=-1):
        return self.stream.read(size)


class ItemSevenTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get('TMPDIR') or NOTIFIER.parent)
        self.directory = Path(tempfile.mkdtemp(prefix='notify-item7-', dir=base))
        self.notify = load()
        self.notify.configure_state(str(self.directory))
        self.notify.ensure_state()

    def code(self, body):
        projection = self.notify.project_http_error_body(Body(json.dumps(body).encode() if not isinstance(body, bytes) else body))
        self.assertFalse(projection['raw_body_retained'])
        return projection['diagnostics'].get('error_code')

    def log_lines(self):
        path = self.directory / 'hook.log'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_any_error_code_is_kept_whatever_it_is(self):
        cases = {
            'webhook_not_accepted': {'code': 'webhook_not_accepted'},
            'invalid_request_error': {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'bad lane'}},
            'E42': {'errors': [{'code': 'E42', 'message': 'x'}]},
            'Bad Request': {'error': 'Bad Request'},
            'not_found': {'detail': 'not_found'},
            '429': {'error': {'code': 429}},
            'unauthorized': {'code': 'unauthorized'},  # one of the five old allowlisted codes still reads the same
        }
        for expected, body in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(self.code(body), expected)
        self.assertEqual(self.code(b'webhook_not_accepted'), 'webhook_not_accepted')  # a one-line text body
        self.assertIsNone(self.code({'message': 'Your request echoed some free text'}))  # a message is prose
        self.assertIsNone(self.code(b'<html>\n<body>gateway</body>\n</html>'))

    def test_codes_are_bounded_and_scrubbed(self):
        self.assertEqual(self.code({'code': FAKE_KEY}), '[masked]')
        self.assertEqual(self.code({'code': 'bad key ' + MIXED + ' here'}), 'bad key [masked] here')
        self.assertEqual(self.code({'error': 'line one\nline\ttwo\x00'}), 'line one line two')
        long = self.code({'code': 'x_' * 200})
        self.assertEqual(len(long), self.notify.ERROR_CODE_LIMIT)
        self.assertNotIn(FAKE_KEY, json.dumps(self.notify.project_http_error_body(Body(json.dumps({'error': {'code': FAKE_KEY}}).encode()))))

    def test_quota_message_keeps_its_counts(self):
        message = 'Automation run rate limit exceeded: global limit 30 per minute, current_count=31'
        fields = self.notify.project_http_error_body(Body(json.dumps({'error': {'message': message}}).encode()))['diagnostics']
        self.assertEqual((fields['error_code'], fields['limit'], fields['current_count']), ('automation_global_rate_limit', 30, 31))

    def test_http_error_projection_reaches_the_requeue_log_line(self):
        # f13pro a9acdeb1's BLOCKED: HTTP 400 with an 87-byte JSON body; the receipts kept no code.
        key = 'k' * 64
        milestones = self.directory / 'milestones'
        (milestones / (key + '.json')).write_text(json.dumps({'event_id': 'e' * 64, 'lane': 't3-f13pro-x'}))

        def opener(request, timeout=None):
            raise urllib.error.HTTPError('http://fixture', 400, 'Bad Request', {}, io.BytesIO(b'{"error":{"code":"lane_not_bound"}}'))
        with patch.object(self.notify, 'webhook', lambda *a, **k: ('http://fixture', 'fixture-key', 'cache')), \
                patch.object(self.notify, 'spaced_post', lambda url, deadline, send: (True, send())), \
                patch.object(self.notify.OPENER, 'open', opener):
            self.assertFalse(self.notify.retry_milestone({'key': key, 'lane': 't3-f13pro-x', 'kind': 'blocker'}))
        line = self.log_lines()[-1]
        self.assertEqual((line['action'], line['http'], line.get('error_code')), ('milestone-post', 400, 'lane_not_bound'))
        attempt = json.loads((milestones / (key + '.attempts.jsonl')).read_text().splitlines()[-1])
        self.assertEqual(attempt['http_error_body']['diagnostics']['error_code'], 'lane_not_bound')
        self.assertNotIn('fixture-key', (self.directory / 'hook.log').read_text())

    def test_failed_kick_is_an_error_line_and_never_raises(self):
        def failed(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 5, None, b'Failed to start sats-completion-requeue.service: Unit '
                                               b'sats-completion-requeue.service not found.\n')
        with patch.dict(os.environ, {'SATS_REQUEUE_NO_KICK': ''}), patch.object(self.notify.subprocess, 'run', failed):
            self.notify.kick_drainer()
        errors = (self.directory / 'errors.log').read_text()
        self.assertIn('requeue-kick', errors)
        self.assertIn('exit=5', errors)
        self.assertIn('not found', errors)
        self.assertEqual(self.log_lines()[-1]['action'], 'requeue-kick-failed')
        # An unwritable error log still cannot break the delivery path that kicked.
        (self.directory / 'errors.log').unlink()
        (self.directory / 'errors.log').mkdir()
        with patch.dict(os.environ, {'SATS_REQUEUE_NO_KICK': ''}), patch.object(self.notify.subprocess, 'run', failed):
            self.notify.kick_drainer()

    def test_successful_kick_logs_nothing(self):
        def started(argv, **kwargs):
            self.assertEqual(argv, ['systemctl', '--user', 'start', '--no-block', 'sats-completion-requeue.service'])
            return subprocess.CompletedProcess(argv, 0, None, b'')
        with patch.dict(os.environ, {'SATS_REQUEUE_NO_KICK': ''}), patch.object(self.notify.subprocess, 'run', started):
            self.notify.kick_drainer()
        self.assertFalse((self.directory / 'errors.log').exists())
        self.assertEqual(self.log_lines(), [])


class UnitFileTests(unittest.TestCase):
    """The drainer the notifier kicks and its timer exist as user units, running the notifier's own requeue entry."""
    UNITS = Path(__file__).resolve().parents[1] / 'systemd'

    def test_units_run_the_existing_drainer(self):
        service = (self.UNITS / 'sats-completion-requeue.service').read_text()
        timer = (self.UNITS / 'sats-completion-requeue.timer').read_text()
        self.assertIn('ExecStart=%h/.local/bin/sats-completion-notify requeue', service)
        self.assertIn('Type=oneshot', service)
        self.assertIn('Unit=sats-completion-requeue.service', timer)
        self.assertIn('WantedBy=timers.target', timer)
        timeout = int(next(line for line in service.splitlines() if line.startswith('TimeoutStartSec=')).split('=')[1])
        self.assertGreater(timeout, 840 + 90 + 60)  # requeue_main max_runtime + idle exit + one slow post
        source = NOTIFIER.read_text()
        self.assertIn('if sys.argv[1:2] == ["requeue"]:', source)


if __name__ == '__main__':
    unittest.main()
