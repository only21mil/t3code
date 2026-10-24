"""notice-delay-rca-20261023 patch 2: a settle naming another thread runs only for a terminal ACCEPTED RESULT with
no live children and no pending votes. Offline: a fake MCP rpc, RESULT.md files under the test's own directory."""
import importlib.util
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mcp_call', ROOT / 'mcp_call.py')
mcp_call = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_call)
guard = getattr(mcp_call, 'sweep_settle_refusal', None)
# The guard reads replies with the stall watchdog's classify(); the candidate's own watchdog source stands in for the
# installed one (WATCHDOG_SRC overrides, for a copy of these tests run elsewhere).
if hasattr(mcp_call, 'WATCHDOG_LIB'):
    mcp_call.WATCHDOG_LIB = os.environ.get('WATCHDOG_SRC') or str(ROOT.parent / 'tools/sats-stall-watchdog/src')


def text(value):
    return {'content': [{'type': 'text', 'text': json.dumps(value)}]}


class FakeRpc:
    """t3_thread_read and t3_thread_list over a dict model; any other tool is a test failure."""

    def __init__(self, threads):
        self.threads, self.calls = threads, []

    def __call__(self, method, params):
        self.calls.append((method, params))
        assert method == 'tools/call', method
        name, args = params['name'], params['arguments']
        if name == 't3_thread_list':
            rows = [dict(t['thread']) for t in self.threads.values() if args.get('includeSubagents')]
            return text({'threads': rows, 'nextCursor': None})
        assert name == 't3_thread_read', name
        model = self.threads[args['threadId']]
        after = args.get('afterPosition', -1)
        return text({'thread': model['thread'], 'recentRuns': model.get('runs', []),
                     'items': [i for i in model.get('items', []) if i['position'] > after][:args.get('limit', 50)]})


def reply(position, body, kind='assistant_message'):
    return {'position': position, 'type': kind, 'status': 'completed', 'text': body}


class SettleGuardTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get('TMPDIR') or ROOT)
        self.directory = Path(tempfile.mkdtemp(prefix='settle-guard-', dir=base))
        self.result = self.directory / 'lane' / 'RESULT.md'
        self.result.parent.mkdir()
        self.result.write_text('DONE\n\nReviewed: Opus ACCEPT, DeepSeek ACCEPT.\n')

    def model(self, items, children=(), active=None):
        parent = {'thread': {'threadId': 'p', 'projectId': 'proj', 'activeRunId': active, 'pendingRequestCount': 0,
                             'itemCount': len(items) + 1, 'parentThreadId': None}, 'items': items}
        threads = {'p': parent}
        for n, (status, verdict, model, *title) in enumerate(children):
            tid = 'c%d' % n
            threads[tid] = {'thread': {'threadId': tid, 'projectId': 'proj', 'parentThreadId': 'p', 'model': model,
                                       'title': title[0] if title else 'review-r1-' + model,
                                       'activeRunId': 'run' if status == 'running' else None, 'itemCount': 2},
                            'runs': [{'status': status, 'completedAt': '2026-10-23T23:%02d:00Z' % n}],
                            'items': [reply(1, verdict)]}
        return FakeRpc(threads)

    def done(self):
        return [reply(0, 'brief', 'user_message'), reply(1, 'DONE. Result: %s' % self.result)]

    def test_guard_exists(self):
        self.assertTrue(callable(guard), 'mcp_call.py has no sweep_settle_refusal')

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_accepted_terminal_result_with_finished_children_may_settle(self):
        rpc = self.model(self.done(), children=[('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT\nno findings', 'deepseek')])
        self.assertIsNone(guard(rpc, 'fd', 'p'))
        self.assertNotIn('t3_thread_organize', [c[1]['name'] for c in rpc.calls])

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_each_missing_condition_refuses(self):
        cases = {
            'active run': (self.model(self.done(), active='run:1'), 'active run'),
            'no DONE reply': (self.model([reply(0, 'brief', 'user_message'), reply(1, 'Sol R2 vote is REQUEST_CHANGES.')]),
                              'no reply leads with DONE'),
            'reply after DONE asks': (self.model(self.done() + [reply(2, 'NEEDS-VICTOR p pick A /x')]), 'asks Victor'),
            'message after DONE': (self.model(self.done() + [reply(2, 'one more thing', 'user_message')]), 'arrived after'),
            'live child (4f5dd34b)': (self.model(self.done(), children=[('completed', 'REQUEST_CHANGES', 'sol'),
                                                                       ('running', '', 'deepseek')]), 'still working'),
            'newest vote rejects': (self.model(self.done(), children=[('completed', 'REQUEST_CHANGES', 'sol')]), 'REQUEST_CHANGES'),
        }
        for name, (rpc, reason) in cases.items():
            with self.subTest(name):
                self.assertIn(reason, guard(rpc, 'fd', 'p') or '')

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_result_must_lead_with_done_and_say_why_no_review(self):
        self.result.write_text('BLOCKED\n')  # 7237c08a and 7a9c4131: reviewed, but BLOCKED
        self.assertIn('line 1 is not DONE', guard(self.model(self.done(), children=[('completed', 'ACCEPT', 'opus')]), 'fd', 'p'))
        self.result.write_text('DONE\n')
        self.assertIn('review is not required', guard(self.model(self.done()), 'fd', 'p'))
        self.result.write_text('DONE\nReview is not required: proof thread.\n')
        self.assertIsNone(guard(self.model(self.done()), 'fd', 'p'))

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses(self):
        # After a DONE reply and an accepted RESULT, the reply forms the watchdog notifies keep the thread open.
        children = [('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT', 'deepseek')]
        later = {'decision for you': '**Decision for you:** may I also push T05 upstream?',
                 'inline bold BLOCKED': 'The reviewed result is **BLOCKED**: RESULT.md:1 names the missing key.',
                 'closed as BLOCKED': 'Closed as BLOCKED. The key never arrived.',
                 'fenced NEEDS-VICTOR': 'Open asks:\n```\nNEEDS-VICTOR p pick A or B /x\n```',
                 'decision from you, ask shape': 'C14 needs a decision from you before the push.'}
        for name, text in later.items():
            with self.subTest(name):
                self.assertIn('a reply after DONE is BLOCKED or asks Victor',
                              guard(self.model(self.done() + [reply(2, text)], children=children), 'fd', 'p') or '')
        own = [reply(0, 'brief', 'user_message'), reply(1, 'DONE. Result: %s\n**Decision for you:** archive the lane?' % self.result)]
        self.assertIn('the DONE reply is BLOCKED or asks Victor', guard(self.model(own, children=children), 'fd', 'p') or '')
        for text in ('Those are late notices. The objective is DONE and settled.', 'Decision from Victor: GO, recorded.',
                     'It reports here as a DONE or BLOCKED notice.'):
            with self.subTest(text=text):
                self.assertIsNone(guard(self.model(self.done() + [reply(2, text)], children=children), 'fd', 'p'))

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_SOL6_a_required_reviewer_without_accept_refuses(self):
        refused = {
            'BLOCKED peer': [('completed', 'ACCEPT', 'opus'), ('completed', 'BLOCKED: the provider rejected the review', 'deepseek')],
            'peer with no reply': [('completed', 'ACCEPT', 'opus'), ('completed', '', 'deepseek')],
            'peer run failed': [('completed', 'ACCEPT', 'opus'), ('failed', 'ACCEPT', 'deepseek')],
            'newest review BLOCKED': [('completed', 'ACCEPT', 'deepseek'), ('completed', 'BLOCKED: rerun cap', 'deepseek')],
        }
        for name, children in refused.items():
            with self.subTest(name):
                self.assertIn('ended without an ACCEPT', guard(self.model(self.done(), children=children), 'fd', 'p') or '')
        allowed = {
            'all ACCEPT': [('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT', 'deepseek')],
            'BLOCKED review rerun to ACCEPT': [('completed', 'BLOCKED: provider rejected', 'deepseek'), ('completed', 'ACCEPT', 'opus'),
                                               ('completed', 'ACCEPT', 'deepseek')],
            'producer child is no vote': [('completed', 'DONE. Patch written.', 'opus', 'produce-fix'),
                                          ('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT', 'deepseek')],
        }
        for name, children in allowed.items():
            with self.subTest(name):
                self.assertIsNone(guard(self.model(self.done(), children=children), 'fd', 'p'))

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_NEW2_a_producer_or_repair_child_is_no_required_reviewer(self):
        # DeepSeek round 2: any title containing "review" made a producer or repair child a required reviewer, so a
        # settle with every real vote ACCEPT was refused. Titles below are the fleet's (RCA presettle evidence).
        accepted = [('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT', 'deepseek')]
        for title in ('Round-1 repair of review findings', 'Opus 5.5 High · repair_muse_exec_final_report',
                      'gpt-6.1-sol high - Kimi K3.1 repair round 1 findings', 'Repair review round 2 findings',
                      'Sol 6.1 Max · produce_openrouter_hub_audit', 'Opus 5.5 High · verify_muse_exec_fleet_r3'):
            with self.subTest(producer=title):
                children = [('completed', 'DONE. Findings repaired.', 'sol', title)] + accepted
                self.assertIsNone(guard(self.model(self.done(), children=children), 'fd', 'p'))
        # A genuine review seat that ended without a vote is still required, in each naming form.
        for title in ('review_mbp_standby_key_replace_deepseek', 'Sol 6.1 Max · review_openrouter_hub_audit',
                      'DeepSeek V4.1 Flash High review · review_muse_exec_route_r2', 'deepseek-v4.1-flash high - Kimi K3.1 review round 1 DeepSeek',
                      'claude-opus-5-5 high - Kimi K3.1 re-review 2 Opus', 'deepseek-v4.1-flash high - Kimi K3.1 focused re-review DeepSeek'):
            with self.subTest(reviewer=title):
                children = accepted + [('completed', 'BLOCKED: the provider rejected the review', 'sol', title)]
                self.assertIn('ended without an ACCEPT', guard(self.model(self.done(), children=children), 'fd', 'p') or '')

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named(self):
        # Review round 3 (DeepSeek R3-5, Sol's title hold): a producer word after the review words made a repair child
        # a required reviewer, and a "<model> - re-review of <task>" seat was missed. The lane's exact T3 titles
        # (notice-package-20261023, read back from t3_thread_list): both reviewer seats in every round count, and the
        # repair seat in every round does not.
        accepted = [('completed', 'ACCEPT', 'opus'), ('completed', 'ACCEPT', 'deepseek')]
        producers = ['Notice package review round 2 repair by Sol', 'Round-2 review findings, repair by Opus'] + [
            'Opus 5.5 XHigh repair · repair_notice_package_20261023_r%d' % n for n in (1, 2, 3)]
        for title in producers:
            with self.subTest(producer=title):
                children = [('completed', 'DONE. Findings repaired.', 'sol', title)] + accepted
                self.assertIsNone(guard(self.model(self.done(), children=children), 'fd', 'p'))
        seats = ['DeepSeek V4.1 Flash high - re-review of notice package', 'DeepSeek V4.1 Flash high - re-review of the repair',
                 'Sol 6.1 High - review of repair round 2', 'Sol 6.1 High review · review_hub_fix_r2'] + [
            '%s High review · review_notice_package_20261023_r%d' % (seat, n) for seat in ('Sol 6.1', 'DeepSeek') for n in (1, 2, 3)]
        for title in seats:
            with self.subTest(reviewer=title):
                children = accepted + [('completed', 'BLOCKED: the provider rejected the review', 'sol', title)]
                self.assertIn('ended without an ACCEPT', guard(self.model(self.done(), children=children), 'fd', 'p') or '')

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_SOL5_missing_watchdog_detection_refuses(self):
        rpc = self.model(self.done(), children=[('completed', 'ACCEPT', 'opus')])
        with patch.object(mcp_call, 'WATCHDOG_LIB', str(self.directory / 'absent')), \
                patch.dict(sys.modules, {'sats_stall_asks': None}):
            with self.assertRaises(SystemExit) as stop:
                guard(rpc, 'fd', 'p')
        self.assertIn('ask detection is unavailable', str(stop.exception))

    def main_calls(self, arguments, refusal):
        """Drive main() over a fake transport. Returns the tools/call names it sent and the guard's calls."""
        sent, checked = [], []

        class Response:
            def __init__(self, body):
                self.body, self.headers = body, {'content-type': 'application/json'}

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return self.body

        def urlopen(request, timeout=None):
            message = json.loads(request.data)
            if message['method'] == 'tools/call':
                sent.append(message['params']['name'])
            return Response(json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': {'serverInfo': {}, 'content': []}}).encode())

        def recorded(rpc, host, tid):
            checked.append((host, tid))
            return refusal
        with patch.object(mcp_call, 'host_url', lambda name: 'http://fixture'), \
                patch.object(mcp_call, 'read_token', lambda name: 'fixture-token'), \
                patch.object(mcp_call, 'PACK', str(self.directory)), \
                patch.object(mcp_call, 'sweep_settle_refusal', recorded), \
                patch.object(mcp_call.urllib.request, 'urlopen', urlopen), \
                patch('builtins.print'):
            try:
                mcp_call.main(['--host', 'mbp', 'call', 't3_thread_organize', json.dumps(arguments)])
            except SystemExit as stop:
                return sent, checked, str(stop)
        return sent, checked, None

    @unittest.skipIf(guard is None, 'no guard in this mcp_call.py')
    def test_main_guards_a_settle_naming_a_thread_and_nothing_else(self):
        # The 19:39 sweep's call: refused before any settle reaches the server.
        sent, checked, stop = self.main_calls({'action': 'settle', 'threadId': 'mcp:4f5dd34b'}, 'child c1 is still working')
        self.assertEqual((sent, checked), ([], [('mbp', 'mcp:4f5dd34b')]))
        self.assertIn('settle refused for mcp:4f5dd34b', stop)
        sent, checked, stop = self.main_calls({'action': 'settle', 'threadId': 'mcp:3e9f5d46'}, None)
        self.assertEqual((sent, checked, stop), (['t3_thread_organize'], [('mbp', 'mcp:3e9f5d46')], None))
        # A thread settling itself names no threadId and keeps canon's self-settle checks; other actions pass through.
        for arguments in ({'action': 'settle'}, {'action': 'archive', 'threadId': 'mcp:x'}):
            with self.subTest(arguments=arguments):
                sent, checked, stop = self.main_calls(arguments, 'must not be asked')
                self.assertEqual((sent, checked, stop), (['t3_thread_organize'], [], None))

if __name__ == '__main__':
    unittest.main()
