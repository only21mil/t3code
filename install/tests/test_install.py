"""install/watchdog_gate.py (DS-H1) and install/replay_recheck.py (SOL-7), offline: a fake systemctl on PATH and fake
thread reads. Writes only under TMPDIR (the lane's .tmp-run in receipts.sh)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate, recheck = load('watchdog_gate'), load('replay_recheck')
FAKE = '''#!/usr/bin/env bash
[ "$FAKE_RC" = 1 ] && exit 1
case "$*" in
  *"show -p LoadState --value sats-stall-watchdog."*) echo "$FAKE_LOAD" ;;
  *"show -p ActiveState --value sats-stall-watchdog.service") echo "$FAKE_SERVICE" ;;
  *"show -p ActiveState --value sats-stall-watchdog.timer") echo "$FAKE_TIMER" ;;
  *"show -p NextElapseUSecRealtime --value sats-stall-watchdog.timer") echo ;;
  *"show -p NextElapseUSecMonotonic --value sats-stall-watchdog.timer") echo "$FAKE_MONO" ;;
  *"list-timers --all --output=json") [ "$FAKE_LIST" = fail ] && exit 1; echo "$FAKE_LIST" ;;
  *) echo "unexpected systemctl $*" >&2; exit 9 ;;
esac
'''


def span(seconds):
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    return '%dd %dh %dmin %.6fs' % (d, h, m, s)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix='gate-', dir=os.environ.get('TMPDIR') or ROOT))
        (self.directory / 'systemctl').write_text(FAKE)
        (self.directory / 'systemctl').chmod(0o700)

    def run_gate(self, service='inactive', timer='active', next_in=240.0, listing=True, mono_in=None, rc=0, load='loaded'):
        next_usec = None if next_in is None else int((time.time() + next_in) * 1e6)
        rows = [{'next': next_usec, 'left': next_usec, 'unit': 'sats-stall-watchdog.timer', 'activates': 'sats-stall-watchdog.service'}]
        env = dict(os.environ, PATH=str(self.directory) + ':' + os.environ['PATH'], FAKE_SERVICE=service, FAKE_TIMER=timer,
                   FAKE_RC=str(rc), FAKE_LOAD=load,
                   FAKE_LIST=json.dumps(rows) if listing else 'fail',
                   FAKE_MONO=span(time.monotonic() + mono_in) if mono_in is not None else 'infinity')
        out = subprocess.run([sys.executable, '-I', str(ROOT / 'watchdog_gate.py')], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stderr, '')
        return out.returncode, json.loads(out.stdout)

    def test_DSH1_a_monotonic_timer_with_empty_realtime_passes_from_list_timers(self):
        code, report = self.run_gate(next_in=240)
        self.assertEqual((code, report['ok'], report['source']), (0, True, 'list-timers'))
        self.assertAlmostEqual(report['left'], 240, delta=5)

    def test_DSH1_without_list_timers_the_monotonic_next_elapse_decides(self):
        code, report = self.run_gate(listing=False, mono_in=200)
        self.assertEqual((code, report['source']), (0, 'monotonic'))
        self.assertAlmostEqual(report['left'], 200, delta=5)
        self.assertEqual(self.run_gate(listing=False, mono_in=30)[0], 3)

    def test_busy_or_near_ticks_wait(self):
        for name, kwargs in {'tick running': {'service': 'activating'}, 'tick near': {'next_in': 60},
                             'no next elapse while the timer runs': {'next_in': None}}.items():
            with self.subTest(name):
                self.assertEqual(self.run_gate(**kwargs)[0], 3)
        self.assertEqual(self.run_gate(timer='inactive', next_in=None)[0], 0)  # a stopped timer schedules no tick

    def test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed(self):
        # Sol round 2: systemctl rc=1 with empty stdout read as service '' and timer '', and the gate said ok, exit 0.
        cases = {'systemctl exits 1 with empty stdout': {'rc': 1, 'listing': False}, 'unknown service state': {'service': 'bogus'},
                 'empty service state': {'service': ''}, 'service in maintenance': {'service': 'maintenance'},
                 'unknown timer state': {'timer': 'bogus'}, 'failed timer': {'timer': 'failed'},
                 'units not found (systemd reads them inactive)': {'load': 'not-found', 'timer': 'inactive', 'next_in': None}}
        for name, kwargs in cases.items():
            with self.subTest(name):
                code, report = self.run_gate(**kwargs)
                self.assertEqual((code, report['ok']), (3, False))
        self.assertEqual(self.run_gate(service='failed')[0], 0)  # the last tick failed and is over

    def test_timespan(self):
        self.assertAlmostEqual(gate.timespan('2d 15h 17min 58.829349s'), 2 * 86400 + 15 * 3600 + 17 * 60 + 58.829349)
        self.assertEqual(gate.timespan('1month 2w 500ms'), 2629800 + 2 * 604800 + 0.5)
        for text in ('infinity', '', 'n/a', '5 minutes'):
            self.assertIsNone(gate.timespan(text))


class RecheckTests(unittest.TestCase):
    CHECK = {'host': 'f13pro', 'thread_id': 'mcp:t', 'ask_position': 27}

    def reader(self, items, thread='mcp:t', page=50):
        calls = []

        def read(host, arguments):
            calls.append((host, arguments))
            after = [i for i in items if i['position'] > arguments['afterPosition']]
            return {'thread': {'threadId': thread, 'settled': True}, 'items': after[:page], 'hasMore': len(after) > page}
        return read, calls

    def test_SOL7_only_a_user_message_after_the_ask_answers_it(self):
        read, calls = self.reader([{'position': 20, 'type': 'user_message'}, {'position': 28, 'type': 'assistant_message'}])
        self.assertFalse(recheck.answered(read, self.CHECK))  # settled, but nobody answered
        self.assertEqual(calls[0][1]['afterPosition'], 27)
        read, _ = self.reader([{'position': 28 + n, 'type': 'assistant_message'} for n in range(60)] + [{'position': 99, 'type': 'user_message'}])
        self.assertTrue(recheck.answered(read, self.CHECK))  # on the second page
        read, _ = self.reader([], thread='mcp:other')
        with self.assertRaises(ValueError):
            recheck.answered(read, self.CHECK)

    def test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer(self):
        # The live base cb8a6cc0's rule: a delegated completion, a server or provider wake or a system notice is not
        # Victor's answer, so the replay stays; a person or a Sats relay through MCP answers it.
        for fields, verdict in (({'createdBy': 'agent', 'creationSource': 'server'}, False),
                                ({'createdBy': 'agent', 'creationSource': 'provider'}, False),
                                ({'createdBy': 'system', 'creationSource': 'server'}, False),
                                ({'createdBy': 'agent', 'creationSource': 'server', 'delegatedCompletion': {'taskIds': ['t']}}, False),
                                ({'createdBy': 'user', 'creationSource': 'web'}, True), ({'createdBy': 'agent', 'creationSource': 'mcp'}, True)):
            with self.subTest(fields=fields):
                read, _ = self.reader([{'position': 28, 'type': 'assistant_message'}, dict(position=30, type='user_message', **fields)])
                self.assertEqual(recheck.answered(read, self.CHECK), verdict)

    def manifest(self, directory, check=CHECK):
        entries = [{'file': 'a.json', 'decision': 'replay', **({'answer_check': check} if check else {})},
                   {'file': 'b.json', 'decision': 'archive'}]
        path = directory / 'manifest.json'
        path.write_text(json.dumps({'entries': entries}))
        return path

    def fake_mcp_call(self, directory, items):
        """A stand-in mcp_call.py: main() writes PACK/mcp-last-result.json as the real one does."""
        path = directory / 'mcp_call.py'
        path.write_text('import json\nPACK = "/nonexistent/live-pack"\n'
                        'def main(argv):\n'
                        '    assert argv[:4] == ["--host", "f13pro", "call", "t3_thread_read"], argv\n'
                        '    page = {"thread": {"threadId": "mcp:t"}, "items": %s, "hasMore": False}\n'
                        '    open(PACK + "/mcp-last-result.json", "w").write(json.dumps({"content": [{"type": "text", "text": json.dumps(page)}]}))\n'
                        '    print("server: fake")\n' % json.dumps(items))
        return path

    def test_SOL7_the_read_goes_through_mcp_call_with_its_pack_in_the_record(self):
        directory = Path(tempfile.mkdtemp(prefix='recheck-', dir=os.environ.get('TMPDIR') or ROOT))
        os.environ.pop('NOTICE_PACKAGE_THREAD_READER', None)
        for items, verdict in (([{'position': 30, 'type': 'assistant_message'}], 'replay'),
                               ([{'position': 31, 'type': 'user_message'}], 'answered')):
            scratch = directory / ('scratch-' + verdict)
            out = subprocess.run([sys.executable, '-I', str(ROOT / 'replay_recheck.py'), str(self.manifest(directory)),
                                  str(self.fake_mcp_call(directory, items)), str(scratch)], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(out.stdout)[verdict], ['a.json'])
            self.assertTrue((scratch / 'mcp-last-result.json').is_file())
        # An entry without its answer_check is unverified, and an existing scratch path refuses to run at all.
        out = subprocess.run([sys.executable, '-I', str(ROOT / 'replay_recheck.py'), str(self.manifest(directory, check=None)),
                              str(self.fake_mcp_call(directory, [])), str(directory / 'scratch-none')], capture_output=True, text=True, timeout=60)
        self.assertEqual([u['file'] for u in json.loads(out.stdout)['unverified']], ['a.json'])
        (directory / 'link').symlink_to(directory)
        out = subprocess.run([sys.executable, '-I', str(ROOT / 'replay_recheck.py'), str(self.manifest(directory)),
                              str(self.fake_mcp_call(directory, [])), str(directory / 'link')], capture_output=True, text=True, timeout=60)
        self.assertNotEqual(out.returncode, 0)

    def test_SOL7_the_reviewed_triage_names_the_replay_asks_position(self):
        manifest = json.loads((ROOT / 'requeue-triage.json').read_text())
        replay = [e for e in manifest['entries'] if e['decision'] == 'replay']
        self.assertEqual([(e['answer_check']['host'], e['answer_check']['thread_id'], e['answer_check']['ask_position']) for e in replay],
                         [('f13pro', 'mcp:a9acdeb1-4e97-4e68-953c-72681ef9cf07', 27)])


if __name__ == '__main__':
    unittest.main()
