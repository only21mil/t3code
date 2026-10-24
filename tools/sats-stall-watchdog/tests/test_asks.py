"""Open human asks in T3 threads reach Sats once per ask message."""
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import sats_stall_asks as asks  # noqa: E402
import sats_stall_watchdog as watchdog  # noqa: E402

T0 = 1792360000.0  # 2026-10-18T21:46:40Z
# Key-shaped token for the masking tests: a secret prefix plus 24+ mixed-case alphanumerics,
# built at runtime so no key-shaped literal sits in source.
FAKE_KEY = 'sk' + '-' + 'synthetic' + 'FIXTURE' + ''.join(map(str, range(10))) + 'NotARealKey'
FAKE_FRAG = FAKE_KEY[3:19]


def label(occurrence):
    """A hook occurrence without its per-ask key: 'generation-1-BLOCKED-ask-<32 hex>' reads 'generation-1-BLOCKED'.
    Tests of one ask per generation compare labels; the per-ask tests compare whole occurrences."""
    return re.sub(r'-ask-[0-9a-f]{32}$', '', occurrence)


def iso(at):
    import datetime
    return datetime.datetime.fromtimestamp(at, datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def message(position, kind, text, at, run='run:thread:t1:ordinal:1', ident=None, status='completed'):
    ident = ident or 'message:%d' % position
    return {'position': position, 'visibility': 'local', 'itemId': 'item:%d' % position, 'messageId': ident,
            'runId': run, 'type': kind, 'status': status, 'text': text, 'textTruncated': False,
            'updatedAt': iso(at)}


class FakeT3:
    """Answers t3_project_list, t3_thread_list and t3_thread_read from a dict model."""

    def __init__(self, projects, threads):
        self.projects, self.threads, self.calls = projects, threads, []
        self.next_read_offset = 0
        self.failing = set()
        self.failing_text = set()  # threads whose text continuation reads fail
        self.cut_text = set()      # threads whose text continuation reads never finish
        self.failing_lists = set()

    def initialize(self):
        pass

    def call(self, name, args):
        self.calls.append((name, dict(args)))
        if name == 't3_project_list':
            return {'projects': self.projects, 'nextCursor': None}
        if name == 't3_thread_list':
            if args['projectId'] in self.failing_lists:
                raise asks.Gap('mcp-transport-unavailable')
            rows = [dict(t['meta']) for t in self.threads.values()
                    if t['meta']['projectId'] == args['projectId'] and not t['meta'].get('archived')
                    and (args.get('includeSubagents') or t['meta'].get('parentThreadId') is None)]
            for row in rows:
                row['itemCount'] = len(self.threads[row['threadId']]['items'])
            return {'threads': rows, 'nextCursor': None}
        if name == 't3_thread_read':
            if args['threadId'] in self.failing:
                raise asks.Gap('mcp-tool-error')
            thread = self.threads[args['threadId']]
            meta = dict(thread['meta'], itemCount=len(thread['items']))
            if 'textOffset' in args:
                if args['threadId'] in self.failing_text:
                    raise asks.Gap('mcp-tool-error')
                item = next(i for i in thread['items'] if i['itemId'] == args['itemId'])
                cut = args['threadId'] in self.cut_text
                return {'thread': meta, 'items': [dict(item, text=item['_rest'], textTruncated=cut,
                                                       nextTextOffset=args['textOffset'] + asks.TEXT_LIMIT if cut else None)]}
            after = args.get('afterPosition')
            items = [i for i in thread['items'] if after is None or i['position'] > after]
            if args.get('view') == 'messages':
                items = [i for i in items if i['type'] in {'user_message', 'assistant_message', 'proposed_plan'}]
            page = items[:args.get('limit', 50)]
            return {'thread': meta, 'items': page, 'hasMore': len(items) > len(page),
                    'nextPosition': page[-1]['position'] if page else after}
        raise AssertionError(name)


def thread(tid, items, status='completed', project='p1', settled=False, settled_at=None, archived=False, parent=None):
    return {'meta': {'threadId': tid, 'projectId': project, 'title': 'Title of ' + tid, 'status': status,
                     'latestRunId': 'run:thread:%s:ordinal:2' % tid, 'settled': settled,
                     'settledAt': iso(settled_at) if settled_at else None, 'archived': archived,
                     'parentThreadId': parent, 'relationshipToParent': 'subagent' if parent else None,
                     'pendingRequestCount': 0, 'updatedAt': iso(max(i_['_at'] for i_ in items) if items else T0)},
            'items': items}


def build(*rows):
    items = []
    for position, (kind, text, at) in enumerate(rows):
        item = message(position, kind, text, at)
        item['_at'] = at
        items.append(item)
    return items


PROJECTS = [{'id': 'p1', 'workspaceRoot': '/home/victor/work', 'deletedAt': None},
            {'id': 'p2', 'workspaceRoot': '/home/other/x', 'deletedAt': None},
            {'id': 'p3', 'workspaceRoot': '/home/victor/projects/a', 'deletedAt': None},
            {'id': 'p4', 'workspaceRoot': '/home/victor/work/mason_t3', 'deletedAt': None}]
SCOPE = {'ids': ['p1'], 'roots': ['/home/victor'], 'exclude': ['p4']}
ASK = 'Done with phase 1.\nNEEDS-VICTOR t1 Chat live; unlock MacBook for browser check /home/victor/work/x/FINAL.md'


class Harness(unittest.TestCase):
    def setUp(self):
        base = ROOT / 'tests' / '.tmp'
        base.mkdir(exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix='asks-', dir=base))
        self.sent = []
        self.receipts = []

    def send(self, plan):
        self.sent.append(plan)
        if self.receipts:
            return self.receipts.pop(0)
        return {'transport': 'hook', 'accepted': True, 'http_status': 200, 'event_id': 'e' * 64,
                'sats_receipt': 'DELIVERED', 'recipient_run_id': '0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b'}

    def occurrences(self):
        """(thread, hook occurrence) per send: the occurrence is generation-<n>-<event state>."""
        return [(p['thread_id'], label(p['occurrence'])) for p in self.sent]

    def evidence(self, plan):
        return json.loads(Path(plan['evidence']).read_text())

    def event_status(self, tid='t9'):
        state = asks.AskState(self.directory)
        try:
            return {label(e['occurrence']): e['status'] for e in state.events('fd:' + tid)}
        finally:
            state.close()

    def tick(self, client, host='fd', scope=SCOPE, dry_run=False, max_notices=10, state=None, now=T0 + 3600, seed=None, max_reads=25):
        events = []
        own = state is None
        state = state or asks.AskState(None if dry_run else self.directory)
        try:
            count = asks.tick_host(client, host, state, lambda action, **f: events.append(dict(f, action=action)),
                                   self.send if not dry_run else None, scope=scope, now=now,
                                   max_notices=max_notices, evidence_dir=self.directory / 'asks', seed=seed,
                                   max_reads=max_reads)
        finally:
            if own:
                state.close()
        return count, events


class DetectionTests(unittest.TestCase):
    def test_markers_decision_ids_and_prose(self):
        self.assertEqual(asks.classify(ASK, final=False)[0], 'decision')
        self.assertEqual(asks.classify('**NEEDS-VICTOR:** pick A or B', final=False)[0], 'decision')
        self.assertEqual(asks.classify('- NEEDS-VICTOR BLOCKED t1 no key /x', final=False)[0], 'blocker')
        self.assertEqual(asks.classify('**Decision for you:** A or B', final=False)[0], 'decision')
        self.assertEqual(asks.classify('Recorded as DECISION-PUSH-2 in DECISION-PUSH.md', final=False)[0], 'decision')
        self.assertIsNone(asks.classify('Changed text needs your OK on its new hash.', final=False))
        for text in ('Changed text needs your OK on its new hash before anything goes out.',
                     "It's a host setting change, so I'll wait for your OK.",
                     'Still waiting on you:\n- the Muse rules change',
                     'Tell me what you think of the set, especially frames 4, 5 and 6.',
                     'Should I delete them?',
                     'Once Victor unlocks it, I will run the check.',
                     'Two calls for you:\n1. Rotate the password.'):
            with self.subTest(text=text):
                self.assertEqual(asks.classify(text, final=True)[0], 'decision')
        self.assertEqual(asks.classify('BLOCKED: the key is missing; I need your OK to rotate it.', final=True)[0], 'blocker')

    def test_notice_shaped_blocked_line_in_a_final_message(self):
        line = 'Tried again.\nmcp:cb22985a BLOCKED unlock MBP, keep awake 15 min /home/victor/work/x/MBP-UNLOCK-BLOCKED.md'
        kind, excerpt, markers, event = asks.classify(line, final=True)
        self.assertEqual((kind, event), ('blocker', 'BLOCKED'))
        self.assertTrue(markers[0].startswith('mcp:cb22985a BLOCKED'))
        self.assertEqual(asks.classify('BLOCKED: no signing key on the mini', final=True)[0], 'blocker')
        self.assertIsNone(asks.classify(line, final=False))
        self.assertIsNone(asks.classify('It reports here as a DONE or BLOCKED notice.', final=True))

    def test_reports_without_an_ask_stay_quiet(self):
        for text in ('DONE. All 20 tests pass and the fix is installed.',
                     'Victor approved this at 10:02; Sats relayed his OK and I published it.',
                     'Done.\n\n**Next steps**\n1. Want me to add a dashboard?\n2. Should I also clean the logs?',
                     'Done.\n```\nShould I? needs your OK\n```\nAll set.',
                     'Receipts are in RECEIPT.md. Nothing is waiting on Victor right now.',
                     'No longer waiting on you; Sats answered.',
                     'That needs no decision from Victor; it is written up as one blocker.'):
            with self.subTest(text=text):
                self.assertIsNone(asks.classify(text, final=True))

    def test_excerpt_keeps_paths_and_masks_keys(self):
        _, excerpt, _, _ = asks.classify('NEEDS-VICTOR t1 rotate /home/victor/work/t3-decision-delivery-fix-20261018/x.md '
                                         'key ' + FAKE_KEY, final=False)
        self.assertIn('/home/victor/work/t3-decision-delivery-fix-20261018/x.md', excerpt)
        self.assertNotIn(FAKE_FRAG, excerpt)
        for key in ('AKIAIOSFODNN7EXAMPLE', 'ghp_abcdefghijklmnopqrstuvwxyz0123456789', 'crsr_0123456789abcdef0123456789abcdef'):
            with self.subTest(key=key):
                self.assertNotIn(key, asks.classify('NEEDS-VICTOR t1 key ' + key + ' /x', final=False)[1])

    def test_project_scope(self):
        allowed = asks.allowed_projects(PROJECTS + [{'id': 'p5', 'workspaceRoot': '/home/victor/../etc', 'deletedAt': None},
                                                   {'id': 'p6', 'workspaceRoot': '/home/victor/x', 'deletedAt': '2026-10-01'}],
                                        **SCOPE)
        self.assertEqual(allowed, ['p1', 'p3'])
        self.assertEqual(asks.allowed_projects(PROJECTS, ids=None, roots=None, exclude=None), [])


class ScanTests(Harness):
    def test_terminal_unsettled_ask_notifies_once_across_restarts(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))})
        count, events = self.tick(client)
        # The brief opens generation 1 (START); the NEEDS-VICTOR ask is its one BLOCKED, sent with the BLOCKED kind.
        self.assertEqual(count, 2)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START'), ('t1', 'generation-1-BLOCKED')])
        plan = self.sent[1]
        self.assertEqual((plan['kind'], plan['thread_id'], plan['host'], plan['run']), ('blocker', 't1', 'fd', 'generation-1'))
        self.assertIn('NEEDS-VICTOR t1 Chat live', plan['message'])
        self.assertLessEqual(len(plan['message']), asks.MESSAGE_LIMIT)
        evidence = self.evidence(plan)
        self.assertEqual((evidence['message_id'], evidence['state'], evidence['generation']), ('message:1', 'BLOCKED', 1))
        self.assertEqual(stat.S_IMODE(os.stat(plan['evidence']).st_mode), 0o600)
        sent = [e for e in events if e['action'] == 'event-notice']
        self.assertEqual([e['sats_receipt'] for e in sent], ['DELIVERED', 'DELIVERED'])
        self.assertNotIn('Chat live', json.dumps(events))
        # Same ask on a later tick, a restarted state and a thread update: never again.
        self.assertEqual(self.tick(client)[0], 0)
        client.threads['t1']['meta']['updatedAt'] = iso(T0 + 999)
        self.assertEqual(self.tick(client)[0], 0)
        self.assertEqual(len(self.sent), 2)

    def test_settled_override_and_follow_up_after_settle(self):
        overridden = thread('t1', build(('assistant_message', ASK, T0)), settled=True, settled_at=T0 + 5)
        follow_up = thread('t2', build(('assistant_message', 'old report', T0),
                                       ('user_message', 'follow-up', T0 + 100),
                                       ('assistant_message', 'Should I delete them?', T0 + 200)),
                           settled=True, settled_at=T0 + 10)
        client = FakeT3(PROJECTS, {'t1': overridden, 't2': follow_up})
        # t1's settle closes its ask and is no DONE (its last reply is the ask). t2's follow-up after the settle is
        # new work: START; its prose ask is a local record.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences(), [('t2', 'generation-1-START')])

    def test_long_provider_message_ids(self):
        items = build(('assistant_message', ASK, T0))
        items[0]['messageId'] = 'message:provider:muse:native-item:' + 'muse%3Aprovider-thread%3A' * 12 + 'end'
        client = FakeT3(PROJECTS, {'t1': thread('t1', items)})
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.evidence(self.sent[0])['message_id'], items[0]['messageId'])

    def test_legacy_thread_without_run_ids(self):
        items = build(('assistant_message', ASK, T0))
        items[0]['runId'] = None
        legacy = thread('t1', items)
        legacy['meta']['latestRunId'] = None
        client = FakeT3(PROJECTS, {'t1': legacy})
        self.assertEqual(self.tick(client)[0], 1)
        # The notice's hook run is the generation, so a missing message run id changes nothing on the wire.
        self.assertEqual((self.sent[0]['run'], label(self.sent[0]['occurrence'])), ('generation-0', 'generation-0-BLOCKED'))
        state = asks.AskState(self.directory)
        try:
            self.assertRegex(state.rows('asks', 'ask-')[0][1]['run'], r'^t3-thread-[0-9a-f]{32}$')
        finally:
            state.close()

    def test_later_user_reply_overrides(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0), ('user_message', 'GO', T0 + 5)))})
        # The reply closes the ask, which never sends; the reply itself is new work after stopped history: START.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])

    def test_running_thread_markers_only(self):
        items = build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1),
                      ('assistant_message', 'Should I delete them?', T0 + 2))
        client = FakeT3(PROJECTS, {'t1': thread('t1', items, status='running')})
        self.assertEqual(self.tick(client)[0], 2)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START'), ('t1', 'generation-1-BLOCKED')])
        self.assertEqual(self.evidence(self.sent[1])['message_id'], 'message:1')
        # The run ends with the prose ask as its final message: a prose ask is a local record, never a notice.
        client.threads['t1']['meta'].update(status='completed', updatedAt=iso(T0 + 50))
        count, events = self.tick(client)
        self.assertEqual((count, len(self.sent)), (0, 2))
        notice = next(e for e in events if e['action'] == 'ask-local')
        self.assertEqual((notice['message_id'], notice['kind']), ('message:2', 'decision'))

    def test_streaming_final_is_reread(self):
        items = build(('user_message', 'brief', T0), ('assistant_message', 'Working', T0 + 1))
        items[-1]['status'] = 'streaming'
        client = FakeT3(PROJECTS, {'t1': thread('t1', items, status='running')})
        self.assertEqual(self.tick(client)[0], 1)  # the brief's START
        items[-1].update(status='completed', text='Working.\nNEEDS-VICTOR t1 need key /x')
        client.threads['t1']['meta'].update(status='completed', updatedAt=iso(T0 + 9))
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences()[-1], ('t1', 'generation-1-BLOCKED'))

    def test_scope_subagents_and_unchanged_threads(self):
        client = FakeT3(PROJECTS, {
            't1': thread('t1', build(('assistant_message', ASK, T0))),
            'child': thread('child', build(('assistant_message', ASK, T0)), parent='t1'),
            'other': thread('other', build(('assistant_message', ASK, T0)), project='p2'),
            'mason': thread('mason', build(('assistant_message', ASK, T0)), project='p4'),
            'rooted': thread('rooted', build(('assistant_message', ASK, T0)), project='p3')})
        self.assertEqual(self.tick(client)[0], 2)
        self.assertEqual(sorted(p['thread_id'] for p in self.sent), ['rooted', 't1'])
        reads = [c for c in client.calls if c[0] == 't3_thread_read']
        self.assertEqual(len(reads), 2)
        client.calls.clear()
        self.tick(client)
        self.assertEqual([c for c in client.calls if c[0] == 't3_thread_read'], [])

    def test_known_thread_that_disappears_is_read_by_id(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', 'report', T0)))})
        self.assertEqual(self.tick(client)[0], 0)
        t1 = client.threads['t1']
        t1['meta'].update(archived=True, settled=True, settledAt=iso(T0 + 10), updatedAt=iso(T0 + 300))
        extra = build(('user_message', 'one more', T0 + 200), ('assistant_message', 'Should I delete them?', T0 + 300))
        for offset, item in enumerate(extra):
            item.update(position=len(t1['items']) + offset, messageId='message:x%d' % offset)
        t1['items'] += extra
        # Read by ID: the new message is new work (START); its prose ask is a local record.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])

    def test_seeded_archived_thread_never_listed_is_read_by_id(self):
        archived = thread('t9', build(('assistant_message', 'report', T0), ('user_message', 'more', T0 + 100),
                                      ('assistant_message', 'Should I delete them?', T0 + 200)),
                          archived=True, settled=True, settled_at=T0 + 50)
        closed = thread('t8', build(('assistant_message', ASK, T0)), archived=True, settled=True, settled_at=T0 + 50)
        foreign = thread('t7', build(('assistant_message', ASK, T0 + 100)), project='p2', archived=True, settled=True, settled_at=T0)
        client = FakeT3(PROJECTS, {'t9': archived, 't8': closed, 't7': foreign})
        # Both are read by ID. A seeded thread's first read is history (no START), t9's prose ask is a local
        # record and t8's settle closes its marker ask.
        self.assertEqual(self.tick(client, seed=['t9', 't8', 't7'])[0], 0)
        self.assertEqual({c[1]['threadId'] for c in client.calls if c[0] == 't3_thread_read'}, {'t9', 't8', 't7'})
        state = asks.AskState(self.directory)
        try:
            self.assertEqual([(a['thread_id'], a['state']) for _, a in state.rows('asks', 'ask-')], [('t9', 'local')])
        finally:
            state.close()
        client.calls.clear()
        self.tick(client, seed=['t9', 't8', 't7'], now=T0 + 3700)
        self.assertEqual([c for c in client.calls if c[0] == 't3_thread_read'], [])  # backoff, foreign never again
        self.assertEqual(self.sent, [])

    def test_listed_but_unread_thread_is_known_after_archive(self):
        items = build(('assistant_message', 'report', T0), ('user_message', 'more', T0 + 100),
                      ('assistant_message', 'Should I delete them?', T0 + 200))
        client = FakeT3(PROJECTS, {'t1': thread('t1', items)})
        self.assertEqual(self.tick(client, max_reads=0)[0], 0)
        client.threads['t1']['meta'].update(archived=True, settled=True, settledAt=iso(T0 + 150))
        # Known though never read: read by ID from its start. 'more' is new work (START); the prose ask is local,
        # and the settle predates the last reply, so no DONE.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])

    def test_partial_listing_failure_keeps_listed_threads_in_scope(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0))),
                                   't3': thread('t3', build(('assistant_message', ASK, T0)), project='p3')})
        client.failing_lists.add('p3')
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.sent[0]['thread_id'], 't1')
        client.failing_lists.clear()
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.sent[1]['thread_id'], 't3')

    def test_deferred_ask_in_backoff_thread_is_reconciled_before_send(self):
        archived = thread('t9', build(('assistant_message', 'old', T0), ('user_message', 'more', T0 + 100),
                                      ('assistant_message', 'Should I delete them?', T0 + 200)),
                          archived=True, settled=True, settled_at=T0 + 50)
        client = FakeT3(PROJECTS, {'t9': archived})
        self.assertEqual(self.tick(client, seed=['t9'], max_notices=0)[0], 0)
        reply = build(('user_message', 'answered', T0 + 300))[0]
        reply.update(position=3, messageId='message:reply')
        archived['items'].append(reply)
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)
        self.assertEqual(self.sent, [])

    def deferred_asks(self, count):
        """An archived seeded thread whose `count` marker asks were claimed as its one BLOCKED but not sent (notice cap 0)."""
        rows = [('assistant_message', 'old', T0), ('user_message', 'more', T0 + 100)]
        rows += [('assistant_message', ASK.replace('t1', 'a%d' % n), T0 + 200 + n) for n in range(count)]
        archived = thread('t9', build(*rows), archived=True, settled=True, settled_at=T0 + 50)
        client = FakeT3(PROJECTS, {'t9': archived})
        self.assertEqual(self.tick(client, seed=['t9'], max_notices=0)[0], 0)
        return client, archived

    def append(self, archived, kind, text, at):
        item = build((kind, text, at))[0]
        item.update(position=len(archived['items']), messageId='message:late%d' % len(archived['items']),
                    itemId='item:late%d' % len(archived['items']))
        archived['items'].append(item)

    def test_agent_artifacts_after_an_ask_leave_it_open(self):
        # canon 4a02910 (needs-victor fix 2026-10-23): a delegated completion or server wake is not Victor's answer.
        # Ported from the per-message canon suite: here each deferred ask's own BLOCKED sends once, read back from
        # its evidence because the hook plan carries no message id.
        artifacts = [{'createdBy': 'agent', 'creationSource': 'server', 'delegatedCompletion': {'taskIds': ['t']}},
                     {'createdBy': 'agent', 'creationSource': 'server'}, {'createdBy': 'agent', 'creationSource': 'provider'},
                     {'createdBy': 'system', 'creationSource': 'server'}]
        for fields in artifacts:
            self.assertFalse(asks.answers(dict(type='user_message', **fields)), fields)
        for fields in ({'createdBy': 'user', 'creationSource': 'web'}, {'createdBy': 'agent', 'creationSource': 'mcp'}, {}):
            self.assertTrue(asks.answers(dict(type='user_message', **fields)), fields)
        client, archived = self.deferred_asks(2)
        self.append(archived, 'user_message', 'child task finished', T0 + 400)
        archived['items'][-1].update(createdBy='agent', creationSource='server')
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 2)
        self.assertEqual(sorted(self.evidence(p)['message_id'] for p in self.sent), ['message:2', 'message:3'])

    def test_reply_during_backoff_closes_every_deferred_ask_in_the_thread(self):
        for count in (2, 3):
            with self.subTest(asks=count):
                self.setUp()
                client, archived = self.deferred_asks(count)
                self.append(archived, 'user_message', 'answered', T0 + 400)
                self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)  # before next_check
                self.assertEqual(self.event_status(), {'generation-0-BLOCKED': 'overridden'})
                # Restart, reread by ID: the answer after BLOCKED is resumed work, so generation 1 and its START.
                self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 9000)[0], 1)
                self.assertEqual(self.occurrences(), [('t9', 'generation-1-START')])

    def test_settle_during_backoff_closes_every_deferred_ask_in_the_thread(self):
        client, archived = self.deferred_asks(3)
        archived['meta'].update(settledAt=iso(T0 + 500))
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)
        self.assertEqual(self.sent, [])
        self.assertEqual(self.event_status(), {'generation-0-BLOCKED': 'overridden'})

    def test_failed_refresh_holds_every_deferred_ask_then_reply_closes_them(self):
        client, archived = self.deferred_asks(3)
        client.failing.add('t9')
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)
        reads = [c for c in client.calls if c[0] == 't3_thread_read' and c[1]['threadId'] == 't9']
        self.append(archived, 'user_message', 'answered', T0 + 400)
        client.failing.clear()
        client.calls.clear()
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3950)[0], 0)
        self.assertEqual(len([c for c in client.calls if c[0] == 't3_thread_read']), 1)  # one read serves all three
        self.assertEqual(self.sent, [])
        self.assertEqual(self.event_status(), {'generation-0-BLOCKED': 'overridden'})
        self.assertTrue(reads)

    def test_reply_closes_only_the_asks_before_it(self):
        client, archived = self.deferred_asks(2)
        self.append(archived, 'user_message', 'answered', T0 + 400)
        self.append(archived, 'assistant_message', ASK.replace('t1', 'a9'), T0 + 500)
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)
        # The answer closes generation 0's BLOCKED and opens generation 1; the later ask is generation 1's BLOCKED.
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 9000)[0], 2)
        self.assertEqual(self.occurrences(), [('t9', 'generation-1-START'), ('t9', 'generation-1-BLOCKED')])
        self.assertEqual(self.evidence(self.sent[1])['message_id'], 'message:late5')
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 20000)[0], 0)

    def progress(self, archived, count):
        for _ in range(count):
            self.append(archived, 'assistant_message', 'working', T0 + 300)

    def test_reply_beyond_three_pages_still_closes_every_deferred_ask(self):
        client, archived = self.deferred_asks(2)
        self.progress(archived, 151)
        self.append(archived, 'user_message', 'answered', T0 + 400)  # position 155, past one 150-item read
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)  # partial read: held
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 9000)[0], 0)  # scan resumes, reply closes both
        self.assertEqual(self.event_status(), {'generation-0-BLOCKED': 'overridden'})
        # The scan that reaches the answer opens generation 1: START, never the closed BLOCKED.
        self.tick(client, seed=['t9'], now=T0 + 20000)
        self.assertEqual(self.occurrences(), [('t9', 'generation-1-START')])

    def test_open_ask_held_by_a_partial_read_is_sent_once_when_reads_finish(self):
        client, archived = self.deferred_asks(1)
        self.progress(archived, 151)
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 3900)[0], 0)
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 9000)[0], 1)
        self.assertEqual(self.tick(client, seed=['t9'], now=T0 + 20000)[0], 0)
        self.assertEqual(self.occurrences(), [('t9', 'generation-0-BLOCKED')])
        self.assertEqual(self.evidence(self.sent[0])['message_id'], 'message:2')

    def test_listed_thread_partial_scan_does_not_send_answered_asks(self):
        listed = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1),
                                    ('assistant_message', ASK.replace('t1', 'b1'), T0 + 2)))
        client = FakeT3(PROJECTS, {'t1': listed})
        self.assertEqual(self.tick(client, max_notices=0)[0], 0)
        self.progress(listed, 151)
        self.append(listed, 'user_message', 'answered', T0 + 400)
        listed['meta']['updatedAt'] = iso(T0 + 400)
        # The deferred START still goes; the partial scan's reread closes the BLOCKED before it can send.
        self.assertEqual(self.tick(client)[0], 1)
        self.tick(client, now=T0 + 9000)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START'), ('t1', 'generation-2-START')])
        self.assertEqual(self.event_status('t1')['generation-1-BLOCKED'], 'overridden')

    def long_message(self, archived, at):
        """A later assistant message whose text needs one continuation read."""
        self.append(archived, 'assistant_message', 'working ' * 10, at)
        archived['items'][-1].update(textTruncated=True, nextTextOffset=asks.TEXT_LIMIT, _rest='still working')

    def test_failed_text_read_sends_nothing_then_the_next_read_reconciles(self):
        cases = [(listed, answered, failure) for failure in ('error', 'cut') for listed in (True, False) for answered in (True, False)]
        for listed, answered, failure in cases:
            with self.subTest(listed=listed, answered=answered, failure=failure):
                self.setUp()
                if listed:
                    target = thread('t9', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1),
                                                ('assistant_message', ASK.replace('t1', 'b1'), T0 + 2)))
                    client, seed, now = FakeT3(PROJECTS, {'t9': target}), None, T0 + 3600
                    self.assertEqual(self.tick(client, max_notices=0)[0], 0)
                else:
                    (client, target), seed, now = self.deferred_asks(2), ['t9'], T0 + 3600
                # Both asks are bound to BLOCKED events, claimed but held by the notice cap: their lines differ, so
                # each is its own ask (notice-package-20261023 item 6).
                stored = [a['message_id'] for a in self.asks() if a['state'] == 'bound']
                self.assertEqual(len(stored), 2)
                blocked = 'generation-%d-BLOCKED' % (1 if listed else 0)
                marker = self.thread_record('t9')
                self.long_message(target, T0 + 300)
                if answered:
                    self.append(target, 'user_message', 'answered', T0 + 400)
                target['meta']['updatedAt'] = iso(T0 + 400)
                (client.failing_text if failure == 'error' else client.cut_text).add('t9')
                count, events = self.tick(client, seed=seed, now=now + 9000)
                self.assertEqual((count, self.sent), (0, []))
                self.assertIn('mcp-tool-error' if failure == 'error' else 'ask-text-truncated', [e.get('reason') for e in events])
                self.assertEqual({a['state'] for a in self.asks()}, {'bound'})
                self.assertEqual(self.event_status()[blocked], 'pending')
                after = self.thread_record('t9')
                self.assertEqual((after.get('position'), after.get('sig')), (marker.get('position'), marker.get('sig')))
                client.failing_text.clear()
                client.cut_text.clear()
                # One BLOCKED per ask. An answer closes them and opens the next generation.
                expected = {(True, True): ['generation-1-START', 'generation-2-START'],
                            (True, False): ['generation-1-START', 'generation-1-BLOCKED', 'generation-1-BLOCKED'],
                            (False, True): ['generation-1-START'],
                            (False, False): ['generation-0-BLOCKED', 'generation-0-BLOCKED']}[(listed, answered)]
                self.assertEqual(self.tick(client, seed=seed, now=now + 30000)[0], len(expected))
                self.assertEqual(self.tick(client, seed=seed, now=now + 90000)[0], 0)
                states = {a['message_id']: a['state'] for a in self.asks()}
                self.assertEqual(sorted(states), sorted(stored))
                self.assertEqual(set(states.values()), {'bound'})
                self.assertEqual(self.event_status()[blocked], 'overridden' if answered else 'sent')
                self.assertEqual([o for _, o in self.occurrences()], expected)
                self.assertIsNotNone(self.thread_record('t9').get('position'))
                self.assertGreater(self.thread_record('t9')['position'], marker['position'])

    def asks(self):
        state = asks.AskState(self.directory)
        try:
            return [value for _, value in state.rows('asks', 'ask-')]
        finally:
            state.close()

    def thread_record(self, tid):
        state = asks.AskState(self.directory)
        try:
            return state.get('threads', 'thread:fd:' + tid) or {}
        finally:
            state.close()

    def test_transient_failures_never_drop_a_known_thread(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', 'report', T0)))})
        self.tick(client)
        t1 = client.threads['t1']
        t1['meta'].update(archived=True, settled=True, settledAt=iso(T0 + 10))
        extra = build(('user_message', 'more', T0 + 200), ('assistant_message', 'Should I delete them?', T0 + 300))
        for offset, item in enumerate(extra):
            item.update(position=1 + offset, messageId='message:y%d' % offset)
        t1['items'] += extra
        client.failing.add('t1')
        now = T0 + 3600
        for _ in range(4):
            now += 90000
            self.assertEqual(self.tick(client, now=now)[0], 0)
        client.failing.clear()
        self.assertEqual(self.tick(client, now=now + 90000)[0], 1)

    def test_deferred_ask_answered_or_settled_before_send_is_not_sent(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0))),
                                   't2': thread('t2', build(('assistant_message', ASK, T0)))})
        self.assertEqual(self.tick(client, max_notices=0)[0], 0)
        reply = build(('user_message', 'GO', T0 + 10))[0]
        reply.update(position=1, messageId='message:reply')
        client.threads['t1']['items'].append(reply)
        client.threads['t1']['meta']['updatedAt'] = iso(T0 + 10)
        client.threads['t2']['meta'].update(settled=True, settledAt=iso(T0 + 20), updatedAt=iso(T0 + 20))
        # Neither BLOCKED sends. t1's answer is resumed work (START); t2's settle after its ask is no DONE.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])
        self.assertEqual(self.event_status('t2'), {'generation-0-BLOCKED': 'overridden'})

    def test_marker_secrets_are_masked_everywhere(self):
        key = FAKE_KEY
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', 'NEEDS-VICTOR t1 rotate ' + key + ' /x/y.md', T0)))})
        self.assertEqual(self.tick(client)[0], 1)
        self.assertNotIn(FAKE_FRAG, self.sent[0]['message'])
        self.assertNotIn(FAKE_FRAG, Path(self.sent[0]['evidence']).read_text())
        self.assertNotIn(FAKE_FRAG.encode(), (self.directory / 'asks.sqlite3').read_bytes())

    def test_failed_delivery_retries_same_occurrence_three_times(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0)))})
        failed = {'transport': 'hook', 'accepted': False, 'http_status': 503, 'reason': 'hook-rejected'}
        self.receipts = [dict(failed), dict(failed), dict(failed), dict(failed)]
        for _ in range(5):
            self.tick(client)
        self.assertEqual(len(self.sent), 3)
        self.assertEqual(len({(p['occurrence'], p['message']) for p in self.sent}), 1)

    def test_accepted_without_recipient_delivery_is_not_resent_but_logged_failed(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0)))})
        self.receipts = [{'transport': 'hook', 'accepted': True, 'http_status': 200, 'sats_receipt': 'FAILED',
                          'delivery_failure': 'native_recipient_delivery_unavailable'}]
        _, events = self.tick(client)
        self.assertEqual(self.tick(client)[0], 0)
        notice = next(e for e in events if e['action'] == 'event-notice')
        self.assertEqual(notice['sats_receipt'], 'FAILED')
        self.assertEqual(notice['delivery_failure'], 'native_recipient_delivery_unavailable')

    def test_notice_cap_defers_the_rest(self):
        threads = {'t%d' % n: thread('t%d' % n, build(('assistant_message', ASK, T0 + n))) for n in range(5)}
        client = FakeT3(PROJECTS, threads)
        self.assertEqual(self.tick(client, max_notices=2)[0], 2)
        self.assertEqual(self.tick(client, max_notices=2)[0], 2)
        self.assertEqual(self.tick(client, max_notices=2)[0], 1)
        self.assertEqual(len(set(self.occurrences())), 5)

    def test_dry_run_sends_and_writes_nothing(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0)))})
        count, events = self.tick(client, dry_run=True)
        self.assertEqual(count, 0)
        self.assertEqual(self.sent, [])
        self.assertEqual([e['action'] for e in events if e['action'].startswith('ask-')], ['ask-detected'])
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_shared_family_host_is_never_scanned(self):
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(('assistant_message', ASK, T0)))})
        count, events = self.tick(client, host='m3mbp')
        self.assertEqual((count, client.calls), (0, []))


class CoverageTests(unittest.TestCase):
    def test_config_covers_five_victor_hosts(self):
        config = json.loads((ROOT / 'config' / 'watchdog.json').read_text())
        hosts = watchdog.roster(ROOT / 'config' / 'hosts')
        names = {h['name'] for h in hosts}
        for name in ('fd', 'mbp', 'mini', 'yoga', 'f13pro'):
            self.assertIn(name, config['allowed_hosts'])
            self.assertIn(name, names)
            self.assertIn(name, watchdog.AUTHORIZED_HOSTS)
            self.assertTrue(config['t3_projects'][name], name)
            self.assertTrue(config['t3_ask_scope'][name]['roots'], name)
        host = next(h for h in hosts if h['name'] == 'f13pro')
        aliases, url = watchdog.AUTHORIZED_HOSTS['f13pro']
        self.assertIn(host['alias'], aliases)
        self.assertEqual(host['t3url'], url)
        self.assertNotIn('m3mbp', config['t3_ask_scope'])
        self.assertEqual(config['t3_ask_seed_file'], '~/.config/sats-stall-watchdog/ask-seed.json')
        seed = json.loads((ROOT / 'config' / 'ask-seed.json').read_text())['threads']
        self.assertEqual(sorted(seed), ['f13pro', 'fd', 'mbp', 'mini', 'yoga'])
        self.assertTrue(all(asks.ID.fullmatch(t) for ids in seed.values() for t in ids))


class TransportTests(unittest.TestCase):
    def test_hook_arguments(self):
        base = ROOT / 'tests' / '.tmp'
        base.mkdir(exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix='ask-hook-', dir=base))
        hook = directory / 'hook'
        record = directory / 'argv.json'
        hook.write_text('#!/usr/bin/env python3\nimport json,sys\nopen(%r,"w").write(json.dumps(sys.argv[1:]))\n'
                        'print(json.dumps({"event_id":"e","state":"WEBHOOK_ACCEPTED","http_status":200,'
                        '"sats_receipt":"DELIVERED","recipient_run_id":"0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b"}))\n' % str(record))
        hook.chmod(0o700)
        transport = watchdog.AskTransport({'hook_cli': str(hook)}, directory)
        plan = {'host': 'fd', 'thread_id': 'mcp:t1', 'run': 'generation-3', 'kind': 'blocker', 'occurrence': 'generation-3-FAILED',
                'message': 'T3 fd mcp:t1 FAILED generation 3: build broke', 'evidence': str(directory / 'e.json')}
        receipt = transport(plan)
        argv = json.loads(record.read_text())
        self.assertTrue(receipt['accepted'])
        self.assertEqual(receipt['sats_receipt'], 'DELIVERED')
        pairs = dict(zip(argv[1::2], argv[2::2]))
        self.assertEqual(argv[0], 'milestone')
        # FAILED keeps its state in the occurrence and goes out with the BLOCKED kind; the run is the generation.
        self.assertEqual(pairs['--kind'], 'blocker')
        self.assertEqual(pairs['--recipient'], 'Sats')
        self.assertEqual(pairs['--owner-thread-id'], 'mcp:t1')
        self.assertEqual(pairs['--occurrence'], 'generation-3-FAILED')
        self.assertEqual(pairs['--run'], 'generation-3')
        self.assertRegex(pairs['--lane'], r'^t3-fd-[0-9a-f]{32}$')
        self.assertTrue(Path(pairs['--lanedir']).is_dir())


class ThreadNoticeTests(Harness):
    """A T3 thread posts its own terminal notice inside the turn (sats-pm-visible-swarm § T3 terminal notice).
    Each ask reaches Sats once in either order: the ask waits for its turn to end, then the thread's
    delivered notice carries it, a queued or in-flight one makes it wait, and anything else sends it."""
    RUN = 'run:thread:t1:ordinal:1'  # the runId build() gives every message

    def transport(self):
        hook, self.calls, self.state = self.directory / 'hook', self.directory / 'hook-calls', self.directory / 'hook-state'
        hook.write_text('#!/usr/bin/env python3\nimport json,sys\na=sys.argv\n'
                        'open(%r,"a").write(a[a.index("--owner-thread-id")+1]+" "+a[a.index("--kind")+1]+"\\n")\n'
                        'print(json.dumps({"event_id":"e","state":"WEBHOOK_ACCEPTED","http_status":200,'
                        '"sats_receipt":"DELIVERED","recipient_run_id":"0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b"}))\n' % str(self.calls))
        hook.chmod(0o700)
        (self.state / 'milestones').mkdir(parents=True)
        (self.state / 'requeue').mkdir()
        self.send = watchdog.AskTransport({'hook_cli': str(hook), 'hook_state_dir': str(self.state)}, self.directory)

    def hook_calls(self):
        return len(self.hooked())

    def hooked(self, kind='blocker'):
        """Thread ids of the hook calls of one kind: blocker is the BLOCKED notice these tests are about."""
        lines = self.calls.read_text().splitlines() if self.calls.exists() else []
        return sorted(line.split(' ')[0] for line in lines if line.split(' ')[1] == kind)

    def notice(self, tid, kind, suffix):
        import hashlib
        identity = ['t3-' + tid, tid, kind, self.RUN]
        key = hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()
        return self.state / 'requeue' / (key + '.json') if suffix == 'requeue' else self.state / 'milestones' / (key + '.' + suffix)

    def proof(self, tid, kind, run_id):
        self.notice(tid, kind, 'acceptance.json').write_text(json.dumps({'http_status': 200, 'recipient_run_id': run_id}))

    def test_watchdog_first_waits_for_the_turn_and_the_threads_notice_is_the_one_delivery(self):
        self.transport()
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1)), status='running')
        t1['meta']['activeRunId'] = t1['meta']['latestRunId'] = self.RUN
        client = FakeT3(PROJECTS, {'t1': t1})
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (1, 0))  # mid-turn marker: only the brief's START
        self.assertEqual(self.hooked('start'), ['t1'])
        self.proof('t1', 'blocker', '0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b')  # the thread's notice, inside the turn
        client.threads['t1']['meta'].update(status='completed', updatedAt=iso(T0 + 50))
        count, events = self.tick(client)
        self.assertEqual((count, self.hook_calls()), (0, 0))
        notice = next(e for e in events if e['action'] == 'ask-bound')
        self.assertEqual((notice['state'], notice['status']), ('BLOCKED', 'thread-notice'))
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (0, 0))

    def test_failed_notice_falls_back_and_queued_or_in_flight_notice_waits(self):
        import fcntl
        self.transport()
        uuid = '0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b'
        client = FakeT3(PROJECTS, {tid: thread(tid, build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + n)))
                                   for n, tid in enumerate(('t1', 't2', 't3', 't4', 't5'), 1)})
        self.proof('t1', 'decision', uuid)  # delivered: the thread's notice is the ask's one delivery
        self.proof('t2', 'blocker', None)   # 2xx without a recipient run id: the hook's FAILED, so the ask sends
        self.notice('t3', 'decision', 'requeue').write_text('{}')  # the hook queued its own retries
        lock = os.open(self.notice('t4', 'blocker', 'lock'), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)    # the thread's notice is still in flight
        self.proof('t5', 'done', uuid)      # a DONE notice carries no ask
        self.tick(client)
        self.assertEqual(self.hooked(), ['t2', 't5'])
        self.notice('t3', 'decision', 'requeue').unlink()  # the requeue delivered it
        self.proof('t3', 'decision', uuid)
        os.close(lock)                      # the in-flight notice ended without a delivery
        self.tick(client)
        self.assertEqual(self.hooked(), ['t2', 't4', 't5'])
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (0, 3))
        self.assertEqual(self.hooked('start'), ['t1', 't2', 't3', 't4', 't5'])  # one START per generation

    UUID = '0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b'

    def ended(self, *tids):
        return FakeT3(PROJECTS, {tid: thread(tid, build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1)))
                                 for tid in tids})

    def between_reads(self, step):
        """Run step() once, right after the watchdog's first read of a thread notice's acceptance proof."""
        from unittest import mock
        import threading
        original, fired = Path.read_text, []

        def read_text(path, *args, **kwargs):
            try:
                return original(path, *args, **kwargs)
            finally:
                if path.name.endswith('.acceptance.json') and not fired and threading.current_thread() is threading.main_thread():
                    fired.append(path.name)
                    step()
        return mock.patch.object(Path, 'read_text', read_text)

    def hook_side(self, lock, then):
        """A hook process's critical section for one occurrence: take its lock (waiting, as the hook does), run then()."""
        import fcntl
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            then()
        finally:
            os.close(fd)

    def test_queued_notice_drained_between_reads_is_the_one_delivery(self):
        import threading
        self.transport()
        client = self.ended('t1')
        entry = self.notice('t1', 'blocker', 'requeue')
        entry.write_text('{}')  # the thread's notice failed three times and the hook queued it

        def drain():  # requeue_main: retry_milestone delivers under the lock, then the entry goes
            self.hook_side(self.notice('t1', 'blocker', 'lock'), lambda: self.proof('t1', 'blocker', self.UUID))
            entry.unlink()
        drainer = threading.Thread(target=drain)
        with self.between_reads(lambda: (drainer.start(), drainer.join(0.5))):
            self.tick(client)
        self.assertEqual(self.hook_calls(), 0)
        drainer.join(5)
        self.assertFalse(entry.exists())
        self.tick(client)
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (0, 0))

    def test_in_flight_notice_finishing_between_reads_is_the_one_delivery(self):
        import threading
        self.transport()
        client = self.ended('t1')
        holding, go = threading.Event(), threading.Event()

        def emit():  # _emit_milestone: holds the lock across its POST, writes the proof, releases
            self.hook_side(self.notice('t1', 'blocker', 'lock'),
                           lambda: (holding.set(), go.wait(5), self.proof('t1', 'blocker', self.UUID)))
        sender = threading.Thread(target=emit)
        sender.start()
        holding.wait(5)
        try:
            with self.between_reads(lambda: (go.set(), sender.join(0.5))):
                self.tick(client)
        finally:
            go.set()
            sender.join(5)
        self.assertEqual(self.hook_calls(), 0)
        self.tick(client)
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (0, 0))

    def test_ask_waits_for_a_notice_started_as_the_turn_stopped(self):
        self.transport()
        client = self.ended('t1')
        stopped = T0 + 1  # the thread's updatedAt: its turn stopped then
        self.assertEqual((self.tick(client, now=stopped + 5)[0], self.hook_calls()), (1, 0))  # the brief's START only
        self.proof('t1', 'decision', self.UUID)  # the notice the turn started reaches the hook and delivers
        self.assertEqual((self.tick(client, now=stopped + asks.TURN_GRACE)[0], self.hook_calls()), (0, 0))
        self.assertEqual((self.tick(client, now=stopped + 3600)[0], self.hook_calls()), (0, 0))

    def test_repeated_ask_in_one_turn_is_one_decision(self):
        self.transport()
        repeated = build(('user_message', 'brief', T0), ('assistant_message', 'Checking.\n' + ASK, T0 + 1),
                         ('assistant_message', ASK, T0 + 2))
        client = FakeT3(PROJECTS, {'t1': thread('t1', repeated),
                                   't2': thread('t2', [dict(i) for i in repeated])})
        self.proof('t1', 'decision', None)       # the thread's notice failed: the turn's one ask goes out once
        self.proof('t2', 'decision', self.UUID)  # the thread's notice delivered: nothing goes out
        for _ in range(3):
            self.tick(client)
        self.assertEqual(self.hooked(), ['t1'])
        state = asks.AskState(self.directory)
        try:
            rows = [value for _, value in state.rows('asks', 'ask-')]
            events = {e['thread_id']: e['status'] for e in state.events('fd:') if e['state'] == 'BLOCKED'}
        finally:
            state.close()
        # Every ask is bound to its generation's one BLOCKED: sent once for t1, the thread's own notice for t2.
        self.assertEqual(sorted((r['thread_id'], r['state'], r['event_id'][:6]) for r in rows),
                         [('t1', 'bound', 'event-')] * 2 + [('t2', 'bound', 'event-')] * 2)
        self.assertEqual(events, {'t1': 'sent', 't2': 'thread-notice'})

    def payload(self, tid, kind, message):
        """The hook's frozen payload of the thread's own notice (milestones/<key>.json), as _emit_milestone writes it."""
        self.notice(tid, kind, 'json').write_text(json.dumps({'milestone_message': message, 'event': 'milestone'}))

    def test_SOL2_a_delivered_turn_notice_covers_only_the_asks_it_carried(self):
        # Two distinct asks in one run. The thread's delivered notice carried one of them, so the other still gets its
        # fallback BLOCKED; with no readable message, neither is shown carried and both send.
        self.transport()
        first, second = 'NEEDS-VICTOR pick route A or B for T01 /x/RESULT.md', 'NEEDS-VICTOR rotate the hub key /y/RESULT.md'
        rows = build(('user_message', 'brief', T0), ('assistant_message', first, T0 + 1), ('assistant_message', second, T0 + 2))
        client = FakeT3(PROJECTS, {tid: thread(tid, [dict(i) for i in rows]) for tid in ('t1', 't2', 't3')})
        for tid in ('t1', 't2', 't3'):
            self.proof(tid, 'blocker', self.UUID)
        self.payload('t1', 'blocker', 'mcp:t1 NEEDS-VICTOR pick route A or B for T01')
        self.payload('t2', 'blocker', 'mcp:t2 rotate the hub key')
        for _ in range(3):
            self.tick(client)
        self.assertEqual(self.hooked(), ['t1', 't2', 't3', 't3'])
        state = asks.AskState(self.directory)
        try:
            statuses = {tid: [(e['position'], e['status']) for e in state.events('fd:' + tid) if e['state'] == 'BLOCKED']
                        for tid in ('t1', 't2', 't3')}
        finally:
            state.close()
        self.assertEqual(statuses, {'t1': [(1, 'thread-notice'), (2, 'sent')], 't2': [(1, 'sent'), (2, 'thread-notice')],
                                    't3': [(1, 'sent'), (2, 'sent')]})
        # The message test itself: decision IDs, or the words of a marker line, either way round.
        ask = {'thread_id': 'mcp:t9', 'markers': ['NEEDS-VICTOR DECISION-PUSH-2 approve the T05 push /x']}
        self.assertTrue(asks.notice_carries('mcp:t9 BLOCKED DECISION-PUSH-2', ask))
        self.assertTrue(asks.notice_carries('mcp:t9 NEEDS-VICTOR approve the T05 push', ask))
        self.assertFalse(asks.notice_carries('mcp:t9 NEEDS-VICTOR rotate the key', ask))
        self.assertFalse(asks.notice_carries(None, ask))

    def test_SOL2_r2_complete_decision_ids_and_a_phrase_of_one_ask_only(self):
        # Round-2 probes. Sol: a notice naming DECISION-PUSH-20 also carried the DECISION-PUSH-2 ask (substring match).
        # DeepSeek (NEW-1): a generic "BLOCKED: needs Victor" notice carried every ask by marker words. A phrase that
        # both asks of the turn hold carries neither. Each ask a delivered notice did not carry sends its own BLOCKED.
        self.transport()
        turns = {'t1': ('NEEDS-VICTOR DECISION-PUSH-2 approve the T05 push /x', 'NEEDS-VICTOR DECISION-PUSH-20 approve the T06 push /y',
                        'mcp:t1 BLOCKED DECISION-PUSH-20'),
                 't2': ('NEEDS-VICTOR: BLOCKED, needs Victor to pick route A or B for T01 /x',
                        'NEEDS-VICTOR: BLOCKED, needs Victor to rotate the hub key /y', 'mcp:t2 BLOCKED: needs Victor'),
                 't3': ('NEEDS-VICTOR approve the T05 push to main /x', 'NEEDS-VICTOR approve the T05 push to staging /y',
                        'mcp:t3 approve the T05 push')}
        threads = {}
        for tid, (first, second, message) in turns.items():
            threads[tid] = thread(tid, build(('user_message', 'brief', T0), ('assistant_message', first, T0 + 1),
                                             ('assistant_message', second, T0 + 2)))
            self.proof(tid, 'blocker', self.UUID)
            self.payload(tid, 'blocker', message)
        client = FakeT3(PROJECTS, threads)
        for _ in range(3):
            self.tick(client)
        state = asks.AskState(self.directory)
        try:
            statuses = {tid: [(e['position'], e['status']) for e in state.events('fd:' + tid) if e['state'] == 'BLOCKED'] for tid in turns}
        finally:
            state.close()
        self.assertEqual(statuses, {'t1': [(1, 'sent'), (2, 'thread-notice')], 't2': [(1, 'sent'), (2, 'sent')],
                                    't3': [(1, 'sent'), (2, 'sent')]})
        self.assertEqual(self.hooked(), ['t1', 't2', 't2', 't3', 't3'])
        ask = {'thread_id': 'mcp:t9', 'markers': ['NEEDS-VICTOR DECISION-PUSH-2 approve the T05 push /x']}
        for message in ('mcp:t9 BLOCKED DECISION-PUSH-20', 'mcp:t9 BLOCKED DECISION-PUSH-2X', 'mcp:t9 BLOCKED: needs Victor',
                        'mcp:t9 NEEDS-VICTOR needs a decision from Victor', 'mcp:t9 BLOCKED DECISION-PUSH-3 approve the T05 push'):
            with self.subTest(message=message):
                self.assertFalse(asks.notice_carries(message, ask))
        self.assertTrue(asks.notice_carries('mcp:t9 BLOCKED DECISION-PUSH-2, approve?', ask))
        other = {'thread_id': 'mcp:t9', 'markers': ['NEEDS-VICTOR approve the T05 push to main /y']}
        self.assertTrue(asks.notice_carries('mcp:t9 approve the T05 push', ask))
        self.assertFalse(asks.notice_carries('mcp:t9 approve the T05 push', ask, [other]))

    def test_SOL2_r3_marker_words_paths_and_negated_sentences_decide_what_a_notice_carries(self):
        # Review round 3 (Sol). t1: the ask and the delivered notice open with different marker words, which broke the
        # phrase, so both asks sent. t2: two asks differ only by /repo/main and /repo/staging; dropping paths made them
        # one, so a notice naming /repo/main covered neither. t3: a notice naming neither path covers neither. t4: "Do
        # not act on" embeds the ask's line, and that negated sentence covered it.
        self.transport()
        main, staging = 'NEEDS-VICTOR approve the T05 push to /repo/main', 'NEEDS-VICTOR approve the T05 push to /repo/staging'
        turns = {'t1': ('NEEDS-VICTOR pick route A or B for T01 /x/RESULT.md', 'NEEDS-VICTOR rotate the hub key /y/RESULT.md',
                        'mcp:t1 BLOCKED rotate the hub key'),
                 't2': (main, staging, 'mcp:t2 BLOCKED approve the T05 push to /repo/main'),
                 't3': (main, staging, 'mcp:t3 BLOCKED approve the T05 push'),
                 't4': ('NEEDS-VICTOR pick route A or B for T01 /x', 'BLOCKED: rotate the hub key /y', 'mcp:t4 Do not act on BLOCKED: rotate the hub key')}
        threads = {}
        for tid, (first, second, message) in turns.items():
            threads[tid] = thread(tid, build(('user_message', 'brief', T0), ('assistant_message', first, T0 + 1),
                                             ('assistant_message', second, T0 + 2)))
            self.proof(tid, 'blocker', self.UUID)
            self.payload(tid, 'blocker', message)
        client = FakeT3(PROJECTS, threads)
        for _ in range(3):
            self.tick(client)
        state = asks.AskState(self.directory)
        try:
            statuses = {tid: [(e['position'], e['status']) for e in state.events('fd:' + tid) if e['state'] == 'BLOCKED'] for tid in turns}
        finally:
            state.close()
        self.assertEqual(statuses, {'t1': [(1, 'sent'), (2, 'thread-notice')], 't2': [(1, 'thread-notice'), (2, 'sent')],
                                    't3': [(1, 'sent'), (2, 'sent')], 't4': [(1, 'sent'), (2, 'sent')]})
        self.assertEqual(self.hooked(), ['t1', 't2', 't3', 't3', 't4', 't4'])
        # The message test itself. A notice covers each ask one of its sentences alone carries.
        hub, route = ({'thread_id': 'mcp:t9', 'markers': [line]} for line in ('Decision for you: rotate the hub key', 'BLOCKED: pick route A or B for T01'))
        self.assertTrue(asks.notice_carries('mcp:t9 NEEDS-VICTOR rotate the hub key', hub, [route]))
        message = 'mcp:t9 BLOCKED: rotate the hub key. Also pick route A or B for T01.'
        self.assertEqual((asks.notice_carries(message, hub, [route]), asks.notice_carries(message, route, [hub])), (True, True))
        for message in ('mcp:t9 BLOCKED: never rotate the hub key', "mcp:t9 Don't rotate the hub key", 'mcp:t9 BLOCKED: needs Victor',
                        'mcp:t9 BLOCKED rotate the hub key /z/other.md'):
            with self.subTest(message=message):
                self.assertFalse(asks.notice_carries(message, hub, [route]))


class UpgradeTests(Harness):
    """Ask state the round-4 watchdog wrote (tests/preimage/sats_stall_asks.py, live 570acb59) has no turn or event.
    The first open of the new state baselines the thread as generation 0, and a blocker or NEEDS-VICTOR record is
    that generation's one BLOCKED: a sent one is its baseline, a pending one is decided once, so the thread still
    gets at most one delivery across the upgrade."""
    RUN, UUID = ThreadNoticeTests.RUN, ThreadNoticeTests.UUID
    transport, hook_calls, hooked, notice, proof = (ThreadNoticeTests.transport, ThreadNoticeTests.hook_calls,
                                                    ThreadNoticeTests.hooked, ThreadNoticeTests.notice, ThreadNoticeTests.proof)

    def unpatched(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('preimage_asks', ROOT / 'tests/preimage/sats_stall_asks.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def repeated(self, legacy=False):
        rows = [('user_message', 'brief', T0), ('assistant_message', 'Checking.\n' + ASK, T0 + 1), ('assistant_message', ASK, T0 + 2)]
        if legacy:
            rows.insert(1, ('assistant_message', 'Earlier.\n' + ASK, T0 + 0.5))
        items = build(*rows)
        if legacy:
            items[1]['runId'] = None  # written before T3 had run ids
        return FakeT3(PROJECTS, {'t1': thread('t1', items)})

    def seed(self, client, accepted=()):
        """One pass of the unpatched watchdog: each send whose index is in accepted is delivered, the rest fail."""
        old, calls = self.unpatched(), []

        def send(plan):
            calls.append(plan['message_id'])
            if len(calls) - 1 in accepted:
                return {'accepted': True, 'http_status': 200, 'sats_receipt': 'DELIVERED', 'recipient_run_id': self.UUID}
            return {'accepted': False, 'http_status': 502, 'reason': 'transport-exception'}
        state = old.AskState(self.directory)
        try:
            old.tick_host(client, 'fd', state, lambda action, **f: None, send, scope=SCOPE, now=T0 + 3,
                          evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        rows = self.rows()
        self.assertTrue(rows and all('turn' not in r for r in rows))
        return calls

    def rows(self):
        state = asks.AskState(self.directory)
        try:
            return sorted((value for _, value in state.rows('asks', 'ask-')), key=lambda r: r['position'])
        finally:
            state.close()

    def summary(self):
        return [(r['message_id'], r['state'], r.get('event_id') is not None) for r in self.rows()]

    def blocked(self):
        state = asks.AskState(self.directory)
        try:
            return [(e['generation'], e['status']) for e in state.events('fd:t1') if e['state'] == 'BLOCKED']
        finally:
            state.close()

    def test_upgrade_failed_notice_is_one_fallback_for_old_records(self):
        client = self.repeated()
        self.assertEqual(self.seed(client), ['message:1', 'message:2'])
        self.transport()
        self.proof('t1', 'decision', None)  # the thread's notice: 200 without a recipient run id, FAILED
        for _ in range(3):
            self.tick(client)
        self.assertEqual(self.hooked(), ['t1'])
        self.assertEqual(self.summary(), [('message:1', 'bound', True), ('message:2', 'bound', True)])
        self.assertEqual(self.blocked(), [(0, 'sent')])

    def test_upgrade_turn_already_sent_by_the_old_watchdog_sends_nothing(self):
        client = self.repeated()
        self.assertEqual(self.seed(client, accepted={0}), ['message:1', 'message:2'])
        self.transport()
        self.proof('t1', 'decision', None)
        for _ in range(3):
            self.tick(client)
        self.assertEqual(self.hooked(), [])
        self.assertEqual(self.summary(), [('message:1', 'sent', False), ('message:2', 'bound', True)])
        self.assertEqual(self.blocked(), [(0, 'baseline')])

    def test_upgrade_delivered_notice_sends_nothing(self):
        client = self.repeated()
        self.seed(client)
        self.transport()
        self.proof('t1', 'decision', self.UUID)
        for _ in range(3):
            self.tick(client)
        self.assertEqual(self.hooked(), [])
        self.assertEqual(self.summary(), [('message:1', 'bound', True), ('message:2', 'bound', True)])
        self.assertEqual(self.blocked(), [(0, 'thread-notice')])

    def test_upgrade_message_without_run_id_stays_its_own_decision(self):
        client = self.repeated(legacy=True)
        self.assertEqual(self.seed(client), ['message:1', 'message:2', 'message:3'])
        self.transport()
        self.proof('t1', 'decision', None)
        for _ in range(3):
            self.tick(client)
        # A message without a run id is no longer its own decision: one generation, one BLOCKED.
        self.assertEqual(self.hooked(), ['t1'])
        self.assertEqual(self.summary(), [('message:1', 'bound', True), ('message:2', 'bound', True), ('message:3', 'bound', True)])
        self.assertEqual(self.blocked(), [(0, 'sent')])

    def test_upgrade_backfill_survives_restarts_and_sends_once(self):
        client = self.repeated()
        self.seed(client)
        self.transport()
        self.proof('t1', 'decision', None)
        stopped = T0 + 2
        self.assertEqual((self.tick(client, now=stopped + 5)[0], self.hook_calls()), (0, 0))  # turn grace: nothing decided
        self.assertEqual(self.summary(), [('message:1', 'pending', False), ('message:2', 'pending', False)])
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (1, 1))
        after = self.summary()
        self.assertEqual((self.tick(client)[0], self.hook_calls()), (0, 1))
        self.assertEqual(self.summary(), after)
        self.assertEqual(len(self.rows()), 2)



class DoneTriggerTests(Harness):
    """notice-delay-rca-20261023 patch 1, round-1 H1 (.stage/check_tick.py): a due DONE held only by TURN_GRACE makes
    the scan reread the thread next tick, although its listing never changes again after the turn ends."""

    def reads(self, client):
        return sum(1 for name, _ in client.calls if name == 't3_thread_read')

    def test_done_inside_the_grace_is_reread_once_and_claimed(self):
        end = T0 + 60
        t1 = thread('t1', build(('user_message', 'go', T0), ('assistant_message', 'DONE. Verdict: trial K3.1 Pro.', end)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=end + 30)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])
        before = self.reads(client)
        self.tick(client, now=end + 330)
        self.assertEqual(self.reads(client) - before, 1)
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START'), ('t1', 'generation-1-DONE')])
        before = self.reads(client)
        self.tick(client, now=end + 630)
        self.assertEqual((self.reads(client) - before, len(self.sent)), (0, 2))

    def test_done_then_blocked_and_no_done_line_send_no_done(self):
        end = T0 + 60
        threads = {tid: thread(tid, build(*[('user_message', 'go', T0)] + [('assistant_message', text, end) for text in texts]))
                   for tid, texts in (('t1', ('DONE. first pass', 'BLOCKED waiting on key /x/RESULT.md')),
                                      ('t2', ('Still working on it.',)))}
        client = FakeT3(PROJECTS, threads)
        for offset in (30, 330, 630):
            self.tick(client, now=end + offset)
        self.assertNotIn('generation-1-DONE', [o for _, o in self.occurrences()])
        self.assertIn(('t1', 'generation-1-BLOCKED'), self.occurrences())

    def test_negated_lead_and_settle_alone_send_no_done(self):
        t1 = thread('t1', build(('user_message', 'go', T0), ('assistant_message', 'Not DONE yet, review pending.', T0 + 60)),
                    settled=True, settled_at=T0 + 120)
        self.tick(FakeT3(PROJECTS, {'t1': t1}))
        self.assertEqual(self.occurrences(), [('t1', 'generation-1-START')])



# Real timeline items read on 2026-10-23 for notice-package-20261023 (tests/fixtures; texts, ids and times unchanged).
EVIDENCE = json.loads((ROOT / 'tests/fixtures/notice-package-20261023.json').read_text())


def evidence_text(key, position):
    return next(i['text'] for i in EVIDENCE['threads'][key]['items'] if i['position'] == position)


def evidence_thread(key, upto=None, lead=None):
    """A FakeT3 thread of real items up to position `upto`. lead: a synthetic opening user message at that position,
    for a fixture whose real opening message was not frozen (it opens the generation; its text is not evidence)."""
    record = EVIDENCE['threads'][key]
    items = [dict(i) for i in record['items'] if upto is None or i['position'] <= upto]
    if lead is not None:
        first = items[0]
        items.insert(0, dict(first, position=lead, type='user_message', text='brief (synthetic opening message)',
                             messageId='message:synthetic-%d' % lead, itemId='item:synthetic-%d' % lead))
    last = items[-1]
    meta = {'threadId': record['threadId'], 'projectId': 'p1', 'title': record['title'], 'status': 'completed',
            'latestRunId': last['runId'], 'settled': False, 'settledAt': None, 'archived': False, 'parentThreadId': None,
            'relationshipToParent': None, 'pendingRequestCount': 0, 'updatedAt': last['updatedAt']}
    return record['threadId'], {'meta': meta, 'items': items}


def after_turn(t):
    return asks.timestamp(t['meta']['updatedAt']) + 3600


class MarkersAnywhereTests(Harness):
    """notice-package-20261023 item 5: NEEDS-VICTOR, BLOCKED and DECISION- markers count inside fenced and inline
    code; a leading "Closed as BLOCKED" and a bold **BLOCKED** of a final message are BLOCKED; "Decision for you:"
    is an ask, not a local record; a negation still disqualifies."""

    def test_fenced_asks_mbp_64539631(self):
        kind, excerpt, markers, event = asks.classify(evidence_text('64539631', 171), final=False)
        self.assertEqual((event, len(markers)), ('BLOCKED', 28))
        self.assertTrue(all(m.startswith('NEEDS-VICTOR mcp:64539631-ea2a-480c-8e12-d64acb208816 ') for m in markers))
        self.assertIn('P1 exporter diagnosis', markers[0])
        self.assertIn('Shadow poller disposition', markers[-1])

    def test_closed_as_blocked_mbp_64539631(self):
        kind, excerpt, markers, event = asks.classify(evidence_text('64539631', 174), final=True)
        self.assertEqual((kind, event), ('blocker', 'BLOCKED'))
        self.assertTrue(markers[0].startswith('Closed as BLOCKED.'))
        self.assertIsNone(asks.classify(evidence_text('64539631', 174), final=False))  # BLOCKED lines: final only

    def test_inline_bold_blocked_fd_7237c08a(self):
        kind, excerpt, markers, event = asks.classify(evidence_text('7237c08a', 25), final=True)
        self.assertEqual((kind, event), ('blocker', 'BLOCKED'))
        self.assertTrue(markers[0].startswith('The reviewed result is **BLOCKED**'))
        # The same thread's earlier progress lines mention BLOCKED without the notice shape and are not final.
        self.assertIsNone(asks.classify(evidence_text('7237c08a', 23), final=False))

    def test_decision_for_you_is_an_ask_c95235ec(self):
        kind, excerpt, markers, event = asks.classify(evidence_text('c95235ec-524', 524), final=True)
        self.assertEqual((kind, event), ('decision', 'BLOCKED'))
        self.assertTrue(markers[0].startswith('**Decision for you:** should P05 delete'))
        stored = EVIDENCE['c95235ec_local_decision_asks']['asks']
        self.assertEqual(len(stored), 17)  # the asks the live watchdog kept local in that thread
        for ask in stored:
            with self.subTest(position=ask['position']):
                self.assertEqual(asks.classify('\n'.join(ask['markers']), final=False)[3], 'BLOCKED')

    def test_markers_inside_inline_code_and_fences(self):
        self.assertEqual(asks.classify('`NEEDS-VICTOR t1 pick A or B /x`', final=False)[3], 'BLOCKED')
        self.assertEqual(asks.classify('Status:\n```\nNEEDS-VICTOR t1 pick A /x\n```', final=False)[3], 'BLOCKED')
        self.assertEqual(asks.classify('Done.\n`BLOCKED` waiting on the key /x/RESULT.md', final=True)[3], 'BLOCKED')
        self.assertEqual(asks.classify('```\nmcp:t1 BLOCKED no key /x\n```', final=True)[3], 'BLOCKED')
        decision = asks.classify('Logged.\n```\nDECISION-PUSH-2 approve the push\n```', final=False)
        self.assertEqual((decision[2], decision[3]), (['DECISION-PUSH-2 approve the push'], None))  # matched, stays local

    def test_negations_and_reports_do_not_match(self):
        for text in ('Not BLOCKED: the key arrived and the push went out.', 'not BLOCKED anymore /x',
                     'The lane is no longer **BLOCKED**; it finished.', 'Nothing is **BLOCKED** now.',
                     '| 7237c08a | hub-openrouter-check | **BLOCKED** |', 'It reports here as a DONE or BLOCKED notice.',
                     'That needs no decision from Victor; it is written up as one blocker.'):
            with self.subTest(text=text):
                verdict = asks.classify(text, final=True)
                self.assertTrue(verdict is None or verdict[3] is None, verdict)

    def test_DSM2_decision_reports_stay_local_and_decision_asks_send(self):
        # A decision line sends only when it is for Victor or asks for his decision; a report of one stays local.
        for text in ('**Decision from Victor:** GO on P05.', 'Decisions from Victor: A, then B.', 'Decision from you: approved at 21:40.',
                     '**Decisions from Victor** are in DECISIONS-CURRENT.md.', 'That needs no decision from Victor; it is one blocker.'):
            with self.subTest(text=text):
                verdict = asks.classify(text, final=True)
                self.assertTrue(verdict is None or verdict[3] is None, verdict)
        for text in ('**Decision for you:** may P03 have a 4th review round?', '- **Two decisions for you:**',
                     '**C14 needs a decision from you.** The repair found no maintained hub client.',
                     'This needs a decision from **Victor**: which key?', '**Decisions for Victor:** pick A or B.',
                     'A decision from Victor is needed before the push.'):
            with self.subTest(text=text):
                self.assertEqual(asks.classify(text, final=True)[3], 'BLOCKED')
                self.assertEqual(asks.classify(text, final=False)[3], 'BLOCKED')

    def test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done(self):
        tid, t = evidence_thread('7237c08a')
        client = FakeT3(PROJECTS, {tid: t})
        self.tick(client, now=after_turn(t))
        rows = {a['position']: (a['event'], a['state']) for a in self.rows_for(tid)}
        self.assertEqual(rows[25][0], 'BLOCKED')
        self.assertIn(('fd', 'generation-1-START'), [(p['host'], p['occurrence']) for p in self.sent])
        t['meta'].update(settled=True, settledAt='2026-10-24T00:39:26.701Z', updatedAt='2026-10-24T00:39:26.701Z')
        self.tick(client, now=after_turn(t) + 7200)
        self.assertNotIn('DONE', [p['occurrence'].split('-')[2] for p in self.sent])

    def test_decision_for_you_sends_a_blocked_c95235ec(self):
        tid, t = evidence_thread('c95235ec-524', upto=524, lead=0)
        self.tick(FakeT3(PROJECTS, {tid: t}), now=after_turn(t))
        self.assertEqual([(p['occurrence'].split('-')[2], p['kind']) for p in self.sent], [('START', 'start'), ('BLOCKED', 'blocker')])

    def rows_for(self, tid):
        state = asks.AskState(self.directory)
        try:
            return [value for _, value in state.rows('asks', 'ask-') if value['thread_id'] == tid]
        finally:
            state.close()



def blocked_sends(sent):
    return [p['occurrence'] for p in sent if label(p['occurrence']).endswith('-BLOCKED')]


class PerAskTests(Harness):
    """notice-package-20261023 item 6: each new ask is its own BLOCKED notice; START and DONE stay one per generation."""

    def test_c95235ec_generation_4_sends_four(self):
        # Generation 4 of F-D c95235ec (origin 2282) carried four NEEDS-VICTOR asks; the live key sent one.
        tid, t = evidence_thread('c95235ec-gen4', upto=2368)
        client = FakeT3(PROJECTS, {tid: t})
        self.assertEqual(self.tick(client, now=after_turn(t))[0], 5)
        self.assertEqual(len(set(blocked_sends(self.sent))), 4)
        self.assertEqual(sorted(e['position'] for e in self.stored_events(tid) if e['state'] == 'BLOCKED'), [2289, 2296, 2305, 2315])
        self.assertEqual(self.tick(client, now=after_turn(t) + 600)[0], 0)
        # Victor's next message (2370) is a new generation with its own START and nothing more.
        _, whole = evidence_thread('c95235ec-gen4')
        t['items'].append(whole['items'][-1])
        t['meta']['updatedAt'] = whole['meta']['updatedAt']
        self.tick(client, now=after_turn(whole))
        self.assertEqual([label(p['occurrence']) for p in self.sent[5:]], ['generation-2-START'])

    def test_5a44357c_t01_and_24285_each_send(self):
        tid, t = evidence_thread('5a44357c', upto=404, lead=0)
        self.tick(FakeT3(PROJECTS, {tid: t}), now=after_turn(t))
        by_position = {e['position']: e for e in self.stored_events(tid) if e['state'] == 'BLOCKED'}
        self.assertEqual(sorted(by_position), [385, 397, 404])
        self.assertTrue(by_position[397]['excerpt'].startswith('NEEDS-VICTOR mcp:5a44357c-47a0-4250-a7fc-d5b9a1bb9738 T01 pick route'))
        self.assertTrue(by_position[404]['excerpt'].startswith('NEEDS-VICTOR mcp:5a44357c-47a0-4250-a7fc-d5b9a1bb9738 24285 push replies OK'))
        self.assertEqual({e['status'] for e in by_position.values()}, {'sent'})
        self.assertEqual(len({e['occurrence'] for e in by_position.values()}), 3)

    def test_mbp_64539631_fenced_asks_and_close_out_are_two_asks(self):
        tid, t = evidence_thread('64539631', lead=98)
        self.tick(FakeT3(PROJECTS, {tid: t}), now=after_turn(t))
        self.assertEqual(sorted(e['position'] for e in self.stored_events(tid) if e['state'] == 'BLOCKED'), [171, 174])

    def test_fd_7237c08a_three_asks_and_no_done_on_settle(self):
        tid, t = evidence_thread('7237c08a')
        client = FakeT3(PROJECTS, {tid: t})
        self.tick(client, now=after_turn(t))
        self.assertEqual(sorted(e['position'] for e in self.stored_events(tid) if e['state'] == 'BLOCKED'), [12, 19, 25])
        t['meta'].update(settled=True, settledAt='2026-10-24T00:39:26.701Z', updatedAt='2026-10-24T00:39:26.701Z')
        self.tick(client, now=after_turn(t) + 7200)
        self.assertNotIn('DONE', {e['state'] for e in self.stored_events(tid)})

    def test_start_and_done_stay_one_per_generation(self):
        rows = [('user_message', 'brief', T0), ('assistant_message', 'NEEDS-VICTOR t1 pick A /x', T0 + 1),
                ('assistant_message', 'NEEDS-VICTOR t1 pick B /y', T0 + 2), ('assistant_message', 'DONE. Both recorded.', T0 + 3),
                ('assistant_message', 'DONE. Still done.', T0 + 4)]
        t1 = thread('t1', build(*rows))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.tick(client, now=T0 + 7200)
        states = sorted(e['state'] for e in self.stored_events('t1'))
        self.assertEqual(states, ['BLOCKED', 'BLOCKED', 'DONE', 'START'])
        state = asks.AskState(self.directory)
        try:
            with state.transaction():
                self.assertFalse(state.claim(asks.event('fd', 't1', 1, 'START', 9, T0)))
                self.assertFalse(state.claim(asks.event('fd', 't1', 1, 'DONE', 9, T0)))
                self.assertFalse(state.claim(asks.event('fd', 't1', 1, 'BLOCKED', 9, T0, ask=asks.ask_key({'markers': ['NEEDS-VICTOR t1 pick A /x']}))))
                self.assertTrue(state.claim(asks.event('fd', 't1', 1, 'BLOCKED', 9, T0, ask=asks.ask_key({'markers': ['NEEDS-VICTOR t1 pick C /z']}))))
        finally:
            state.close()

    def test_an_ask_sent_under_the_old_key_is_not_sent_again_after_the_upgrade(self):
        # The live watchdog (406e3fd9) sends the first ask under the one-BLOCKED-per-generation key and binds the
        # second ask to it unsent. After the upgrade a re-wake repeats the first ask (nothing) and the second (sent).
        old = preimage_live()
        first, second = 'NEEDS-VICTOR t1 O19 exact text OK /x', 'NEEDS-VICTOR t1 T01 pick route /y'
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', first, T0 + 1), ('assistant_message', second, T0 + 2)))
        client = FakeT3(PROJECTS, {'t1': t1})
        state = old.AskState(self.directory)
        try:
            old.tick_host(client, 'fd', state, lambda action, **f: None, self.send, scope=SCOPE, now=T0 + 3600,
                          evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        self.assertEqual([p['occurrence'] for p in self.sent], ['generation-1-START', 'generation-1-BLOCKED'])
        for n, text in enumerate(('Still waiting.\n' + first, 'Still waiting.\n' + second), 3):
            t1['items'].append(dict(build(('assistant_message', text, T0 + 100 * n))[0], position=n, messageId='message:%d' % n,
                                    itemId='item:%d' % n, runId='run:thread:t1:ordinal:%d' % n))
        t1['meta'].update(updatedAt=iso(T0 + 400))
        self.tick(client, now=T0 + 7200)
        self.tick(client, now=T0 + 7800)
        later = [p['message'] for p in self.sent[2:]]
        self.assertEqual(len(later), 1)
        self.assertIn('T01 pick route', later[0])

    def stored_events(self, tid):
        state = asks.AskState(self.directory)
        try:
            return state.events('fd:' + tid)
        finally:
            state.close()


def preimage_live():
    import importlib.util
    spec = importlib.util.spec_from_file_location('live_20261023_asks', ROOT / 'tests/preimage/live-20261023/sats_stall_asks.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preimage_needs_victor():
    """The live base since 2026-10-23 22:55:52 CDT, cb8a6cc0 (the needs-victor fix; canon source 4a02910): the
    install's preimage and the module its rollback restores."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('live_needs_victor_asks', ROOT / 'tests/preimage/live-20261023-needs-victor/sats_stall_asks.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EventsMigrationTests(Harness):
    """The item-6 schema change and its rollback: transactional, rowids, ids and data kept, no VACUUM or checkpoint,
    and the older watchdog keeps working on either schema."""

    def v1_state(self):
        """State the live watchdog (406e3fd9) wrote: START, BLOCKED, URGENT and DONE rows over two threads."""
        old = preimage_live()
        threads = {'t1': thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 1))),
                   't2': thread('t2', build(('user_message', 'brief', T0), ('assistant_message', 'URGENT security: key in log /x', T0 + 1))),
                   't4': thread('t4', build(('user_message', 'brief', T0), ('assistant_message', 'All checks pass.', T0 + 2)),
                                settled=True, settled_at=T0 + 10)}
        state = old.AskState(self.directory)
        try:
            old.tick_host(FakeT3(PROJECTS, threads), 'fd', state, lambda action, **f: None, self.send, scope=SCOPE,
                          now=T0 + 3600, evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        return threads

    def schema(self):
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'))
        try:
            return (connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY name").fetchall(),
                    connection.execute('SELECT rowid, id, thread, generation, state, data FROM events ORDER BY rowid').fetchall(),
                    [r[0] for r in connection.execute('SELECT name FROM migrations ORDER BY name')],
                    connection.execute('PRAGMA integrity_check').fetchone()[0])
        finally:
            connection.close()

    def test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema(self):
        self.v1_state()
        before = self.schema()
        self.assertIn(asks.EVENTS_V1, [row[3] for row in before[0]])
        self.assertEqual(sorted(r[4] for r in before[1]), ['BLOCKED', 'DONE', 'START', 'START', 'START', 'URGENT'])
        asks.AskState(self.directory).close()  # first open of the new code upgrades in one transaction
        after = self.schema()
        self.assertIn(asks.EVENTS_V2, [row[3] for row in after[0]])
        self.assertEqual((after[1], after[3]), (before[1], 'ok'))
        self.assertEqual(after[2], ['events-per-ask', 'generations'])
        asks.AskState(self.directory).close()  # a second open changes nothing
        self.assertEqual(self.schema(), after)
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'), isolation_level=None)
        try:
            connection.execute('BEGIN IMMEDIATE')
            asks.downgrade_events(connection, T0)
            connection.execute('COMMIT')
        finally:
            connection.close()
        self.assertEqual(self.schema(), before)  # byte-identical schema, rows and migrations; no events_parked

    def test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas(self):
        threads = self.v1_state()
        state = asks.AskState(self.directory)
        try:
            with state.transaction():
                self.assertTrue(state.claim(asks.event('fd', 't1', 1, 'BLOCKED', 5, T0, ask=asks.ask_key({'markers': ['other ask']}))))
        finally:
            state.close()
        old = preimage_live()
        # Rolled back without the down-migration: the old code still reads and writes the per-ask table.
        threads['t3'] = thread('t3', build(('user_message', 'brief', T0), ('assistant_message', ASK.replace('t1', 't3'), T0 + 1)))
        state = old.AskState(self.directory)
        try:
            old.tick_host(FakeT3(PROJECTS, threads), 'fd', state, lambda action, **f: None, self.send, scope=SCOPE,
                          now=T0 + 3700, evidence_dir=self.directory / 'asks')
            self.assertEqual(sorted(e['state'] for e in state.events('fd:t3')), ['BLOCKED', 'START'])
            with state.transaction():
                self.assertFalse(state.claim(old.event('fd', 't3', 1, 'BLOCKED', 9, T0)))  # its one-per-generation rule holds
        finally:
            state.close()
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'), isolation_level=None)
        try:
            connection.execute('BEGIN IMMEDIATE')
            asks.downgrade_events(connection, T0)
            connection.execute('COMMIT')
            parked = connection.execute('SELECT thread, generation, state FROM events_parked').fetchall()
            sql = connection.execute("SELECT sql FROM sqlite_master WHERE name='events'").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual((parked, sql), ([('fd:t1', 1, 'BLOCKED')], asks.EVENTS_V1))
        state = old.AskState(self.directory)
        try:
            self.assertEqual(state.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(sorted(e['state'] for e in state.events('fd:t1')), ['BLOCKED', 'START'])
        finally:
            state.close()

    def downgrade(self):
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'), isolation_level=None)
        try:
            connection.execute('BEGIN IMMEDIATE')
            asks.downgrade_events(connection, T0)
            connection.execute('COMMIT')
        finally:
            connection.close()

    def per_ask_only(self):
        """A generation opened after the install: its two asks are per-ask BLOCKED rows only, both sent."""
        first, second = 'NEEDS-VICTOR t1 O19 exact text OK /x', 'NEEDS-VICTOR t1 T01 pick route /y'
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', first, T0 + 1), ('assistant_message', second, T0 + 2)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.assertEqual(self.tick(client)[0], 3)
        return t1, client, first

    def rewake(self, t1, position, text, at, run=None, kind='assistant_message'):
        t1['items'].append(dict(build((kind, text, at))[0], position=position, messageId='message:%d' % position,
                                itemId='item:%d' % position, runId=run or 'run:thread:t1:ordinal:%d' % position))
        t1['meta'].update(updatedAt=iso(at))

    def test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key(self):
        t1, client, first = self.per_ask_only()
        self.downgrade()
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'))
        try:
            kept = [(i, json.loads(d)) for i, d in connection.execute("SELECT id, data FROM events WHERE state='BLOCKED'")]
            parked = connection.execute('SELECT count(*) FROM events_parked').fetchone()[0]
        finally:
            connection.close()
        legacy = asks.event_key('fd', 't1', 1, 'BLOCKED')
        self.assertEqual(([i for i, _ in kept], [d['event_id'] for _, d in kept], parked), ([legacy], [legacy], 1))
        self.assertNotIn('ask', kept[0][1])
        self.assertEqual(kept[0][1]['per_ask_event_id'], asks.event_key('fd', 't1', 1, 'BLOCKED', asks.ask_key({'markers': [first]})))
        old, sent = preimage_live(), len(self.sent)
        state = old.AskState(self.directory)
        try:
            with state.transaction():
                self.assertFalse(state.claim(old.event('fd', 't1', 1, 'BLOCKED', 9, T0)))  # already sent: nothing more
            # A re-wake repeats the first ask and adds a third: the old one-per-generation rule binds both to the kept
            # row, so neither sends; Victor's answer opens generation 2, whose new ask sends once.
            self.rewake(t1, 3, 'Still waiting.\n' + first, T0 + 300)
            self.rewake(t1, 4, 'NEEDS-VICTOR t1 also rotate the key /z', T0 + 301)
            old.tick_host(client, 'fd', state, lambda action, **f: None, self.send, scope=SCOPE, now=T0 + 7200, evidence_dir=self.directory / 'asks')
            self.assertEqual(len(self.sent), sent)
            bound = [a for _, a in state.rows('asks', 'ask-') if a['state'] == 'bound' and a['position'] >= 3]
            self.assertEqual(len(bound), 2)
            self.assertTrue(all(state.event(a['event_id']) is not None for a in bound))  # bound to the kept row, not a missing id
            self.rewake(t1, 5, 'Victor: use the old key', T0 + 400, kind='user_message')
            self.rewake(t1, 6, 'NEEDS-VICTOR t1 confirm the old key is still valid /k', T0 + 401, run='run:thread:t1:ordinal:5')
            old.tick_host(client, 'fd', state, lambda action, **f: None, self.send, scope=SCOPE, now=T0 + 9000, evidence_dir=self.directory / 'asks')
            old.tick_host(client, 'fd', state, lambda action, **f: None, self.send, scope=SCOPE, now=T0 + 9600, evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        self.assertEqual([(p['occurrence'], p['kind']) for p in self.sent[sent:]], [('generation-2-START', 'start'), ('generation-2-BLOCKED', 'blocker')])

    def test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked(self):
        # Why rollback.sh runs the down-migration before it restores the old module: on the per-ask schema the old
        # module's legacy BLOCKED key is free beside the per-ask rows, so a repeated ask sends a second BLOCKED.
        t1, client, first = self.per_ask_only()
        old, sent = preimage_live(), len(self.sent)
        state = old.AskState(self.directory)
        try:
            self.rewake(t1, 3, 'Still waiting.\n' + first, T0 + 300)
            old.tick_host(client, 'fd', state, lambda action, **f: None, self.send, scope=SCOPE, now=T0 + 7200, evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        self.assertEqual([p['occurrence'] for p in self.sent[sent:]], ['generation-1-BLOCKED'])

    def test_a_failed_upgrade_changes_nothing(self):
        self.v1_state()
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'))
        connection.execute('CREATE TABLE events_v1 (x)')  # the rename target is taken: the upgrade fails midway
        connection.commit()
        connection.close()
        before = self.schema()
        with self.assertRaises(sqlite3.OperationalError):
            asks.AskState(self.directory)
        self.assertEqual(self.schema(), before)

    def test_no_vacuum_or_checkpoint(self):
        source = (ROOT / 'src/sats_stall_asks.py').read_text()
        self.assertNotRegex(source, r'\.execute\([^\n]*(?i:vacuum|checkpoint)')  # no executed VACUUM or checkpoint


class LiveBaseTests(Harness):
    """The live base since 2026-10-23 22:55:52 CDT is cb8a6cc0, the needs-victor fix (canon source 4a02910). Each
    behavior it adds is the candidate's too, and the rows and records it writes carry across the install and the
    rollback that restores it (LIVE-1). Prose that only names the markers is no ask in the candidate, where cb8a6cc0
    sends a BLOCKED for it (LIVE-2)."""
    ARTIFACTS = {'delegated completion': {'createdBy': 'agent', 'creationSource': 'server', 'delegatedCompletion': {'taskIds': ['x']}},
                 'system notice': {'createdBy': 'system', 'creationSource': 'server'},
                 'provider wake': {'createdBy': 'agent', 'creationSource': 'provider'},
                 'server wake': {'createdBy': 'agent', 'creationSource': 'server'}}
    ANSWERS = {'person': {'createdBy': 'user', 'creationSource': 'web'}, 'Sats relay': {'createdBy': 'agent', 'creationSource': 'mcp'}}

    def rewake(self, t, text, at, kind='assistant_message', **fields):
        position = len(t['items'])
        t['items'].append(dict(build((kind, text, at))[0], position=position, messageId='message:%d' % position, itemId='item:%d' % position,
                               runId='run:thread:%s:ordinal:%d' % (t['meta']['threadId'], position + 1), **fields))
        t['meta'].update(updatedAt=iso(at))

    def live_tick(self, live, client, now, directory=None, send=None):
        state = live.AskState(directory or self.directory)
        try:
            live.tick_host(client, 'fd', state, lambda action, **f: None, send or self.send, scope=SCOPE, now=now,
                           evidence_dir=(directory or self.directory) / 'asks')
        finally:
            state.close()

    def test_LIVE1_artifacts_leave_asks_and_urgent_open_at_find_and_reconcile(self):
        live = preimage_needs_victor()
        for fields in list(self.ARTIFACTS.values()) + list(self.ANSWERS.values()) + [{}]:
            item = dict(type='user_message', **fields)
            self.assertEqual(asks.answers(item), live.answers(item), fields)  # the live base's answers(), unchanged
        names = list(self.ARTIFACTS) + list(self.ANSWERS)
        threads = {}
        for n, name in enumerate(names):
            tid = 'a%d' % n
            threads[tid] = thread(tid, build(('user_message', 'brief', T0), ('assistant_message', 'NEEDS-VICTOR %s pick route A or B /x' % tid, T0 + 1),
                                             ('assistant_message', 'URGENT security: token in the CI log /x', T0 + 2)))
            self.rewake(threads[tid], 'child task finished', T0 + 3, kind='user_message', **{**self.ARTIFACTS, **self.ANSWERS}[name])
        self.tick(FakeT3(PROJECTS, threads), max_notices=50)
        sent = {(p['thread_id'], p['kind']) for p in self.sent}
        for n, name in enumerate(names):
            with self.subTest(name):
                still_open = name in self.ARTIFACTS
                self.assertEqual((('a%d' % n, 'blocker') in sent, ('a%d' % n, 'urgent') in sent), (still_open, still_open))
        # Reconcile: an ask stored pending while its turn ran stays open when only a server wake follows it.
        t = thread('r1', build(('user_message', 'brief', T0), ('assistant_message', 'NEEDS-VICTOR r1 rotate the hub key /y', T0 + 1)), status='running')
        t['meta']['activeRunId'] = t['items'][-1]['runId']
        client, start, state = FakeT3(PROJECTS, {'r1': t}), len(self.sent), asks.AskState(self.directory / 'reconcile')
        try:
            self.tick(client, state=state)
            self.assertEqual([a['state'] for _, a in state.rows('asks', 'ask-')], ['pending'])
            self.rewake(t, 'child task finished', T0 + 2, kind='user_message', **self.ARTIFACTS['server wake'])
            t['meta'].update(status='completed', activeRunId=None)
            self.tick(client, now=T0 + 7200, state=state)
        finally:
            state.close()
        self.assertEqual([p['thread_id'] for p in self.sent[start:] if p['kind'] == 'blocker'], ['r1'])

    def test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once(self):
        # The live base's rule: a later ask whose lines are all noticed in the generation sends nothing, merged or
        # repeated. The candidate also treats a reworded line that names only decisions already noticed as a
        # restatement (SOL-4), where the live base sends it again (last step).
        lines = ('NEEDS-VICTOR t1 pick route A or B /x', 'NEEDS-VICTOR t1 rotate the hub key /y', 'NEEDS-VICTOR t1 confirm the T05 text /z')
        steps = ((lines[0] + '\n' + lines[1], 1, 1), (lines[1], 0, 0), ('Still waiting.\n' + lines[1] + '\n' + lines[0], 0, 0),
                 (lines[0] + '\n' + lines[2], 1, 1), ('NEEDS-VICTOR t1 DECISION-RT-A pick the route /a', 1, 1),
                 ('NEEDS-VICTOR t1 DECISION-RT-B pick the key /b', 1, 1), ('NEEDS-VICTOR t1 DECISION-RT-A and DECISION-RT-B are both open /ab', 0, 1))
        live, live_sent = preimage_needs_victor(), []
        for module in ('candidate', 'live'):
            t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', lines[0], T0 + 1)))
            client, directory = FakeT3(PROJECTS, {'t1': t1}), self.directory / module
            directory.mkdir()
            sent = self.sent if module == 'candidate' else live_sent

            def tick(now):
                if module == 'candidate':
                    state = asks.AskState(directory)
                    try:
                        self.tick(client, now=now, state=state)
                    finally:
                        state.close()
                else:
                    self.live_tick(live, client, now, directory, send=lambda plan: (live_sent.append(plan), {'accepted': True})[1])
            tick(T0 + 3600)
            for n, (text, candidate_sends, live_sends) in enumerate(steps):
                before = len(sent)
                self.rewake(t1, text, T0 + 100 * (n + 2))
                tick(T0 + 3600 * (n + 2))
                with self.subTest(module=module, text=text):
                    self.assertEqual(len(sent) - before, candidate_sends if module == 'candidate' else live_sends)
        self.assertEqual(len({p['occurrence'] for p in self.sent if p['kind'] == 'blocker'}), 5)

    def test_LIVE1_rows_the_live_base_wrote_carry_over_the_install_and_its_rollback(self):
        live = preimage_needs_victor()
        lines = ['NEEDS-VICTOR t1 pick route A or B /x', 'NEEDS-VICTOR t1 rotate the hub key /y', 'NEEDS-VICTOR t1 confirm the T05 text /z',
                 'NEEDS-VICTOR t1 approve the T06 body /w', 'NEEDS-VICTOR t1 name the T08 reviewer /v']
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', lines[0], T0 + 1), ('assistant_message', lines[1], T0 + 2)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.live_tick(live, client, T0 + 3600)  # START, the generation's BLOCKED and the second ask's own row
        occurrences = [p['occurrence'] for p in self.sent]
        self.assertEqual(occurrences[:2], ['generation-1-START', 'generation-1-BLOCKED'])
        self.assertRegex(occurrences[2], r'^generation-1-BLOCKED-[0-9a-f]{16}$')
        self.rewake(t1, lines[2], T0 + 300)
        self.receipts = [{'transport': 'hook', 'accepted': False, 'reason': 'hook-rejected'}]
        self.live_tick(live, client, T0 + 7200)  # the third ask's own row is claimed, its send fails: pending at install
        pending = self.sent[-1]['occurrence']
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'))
        try:
            self.assertEqual(sorted(s for (s,) in connection.execute("SELECT state FROM events WHERE state LIKE 'BLOCKED%'")),
                             ['BLOCKED', 'BLOCKED:' + occurrences[2][-16:], 'BLOCKED:' + pending[-16:]])
        finally:
            connection.close()
        # Install: the candidate opens the same state (the events migration). Re-wakes restate the three asks and add
        # a fourth. The pending row goes out once under its own occurrence, the fourth ask once, the restatements never.
        start = len(self.sent)
        for n, text in enumerate(('Still waiting.\n' + lines[0], 'Still waiting.\n' + lines[1], 'Still waiting.\n' + lines[2], lines[3])):
            self.rewake(t1, text, T0 + 400 + n)
        self.tick(client, now=T0 + 10800)
        self.tick(client, now=T0 + 11400)
        after = [p['occurrence'] for p in self.sent[start:]]
        self.assertEqual(len(after), 2, after)
        self.assertEqual(after[0], pending)
        self.assertEqual((label(after[1]), after[1] != 'generation-1-BLOCKED'), ('generation-1-BLOCKED', True))
        # Rollback: the down-migration with the candidate, then the live base again. It restates the fourth ask (nothing)
        # and sends a fifth once under its own row.
        connection = sqlite3.connect(str(self.directory / 'asks.sqlite3'), isolation_level=None)
        try:
            connection.execute('BEGIN IMMEDIATE')
            asks.downgrade_events(connection, T0)
            connection.execute('COMMIT')
            self.assertEqual(connection.execute("SELECT sql FROM sqlite_master WHERE name='events'").fetchone()[0], asks.EVENTS_V1)
        finally:
            connection.close()
        start = len(self.sent)
        self.rewake(t1, 'Still waiting.\n' + lines[3], T0 + 500)
        self.rewake(t1, lines[4], T0 + 501)
        self.live_tick(live, client, T0 + 14400)
        self.live_tick(live, client, T0 + 15000)
        self.assertEqual(len(self.sent[start:]), 1)
        self.assertRegex(self.sent[-1]['occurrence'], r'^generation-1-BLOCKED-[0-9a-f]{16}$')

    def test_LIVE1_the_live_base_fixture_matrix_passes_on_the_candidate_and_the_live_base(self):
        # blocked-threads-rca-20261023's 19 cases (tests/needs_victor, from the MBP lane; cb8a6cc0 19/19 there).
        import subprocess
        script = ROOT / 'tests/needs_victor/test_needs_victor.py'
        for module in (ROOT / 'src/sats_stall_asks.py', ROOT / 'tests/preimage/live-20261023-needs-victor/sats_stall_asks.py'):
            out = subprocess.run([sys.executable, '-B', '-I', str(script), str(module)], capture_output=True, text=True, timeout=120)
            with self.subTest(module=module.parent.name):
                self.assertEqual((out.returncode, out.stdout.splitlines()[-1:]), (0, ['MATRIX PASS 19/19 sats_stall_asks.py']), out.stdout + out.stderr)

    def test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send(self):
        # 23:05 CT 2026-10-23: the live base sent a false BLOCKED (event-621be371) for a status bullet that names the
        # markers. The candidate reads such prose, plain, coded, fenced, bold or quoted, as no ask.
        live = preimage_needs_victor()
        fixture = json.loads((ROOT / 'tests/fixtures/live2-status-20261023.json').read_text())
        line = fixture['false_ask_line']
        self.assertEqual(live.classify(fixture['text'], final=True)[1:4:2], (line[2:], 'BLOCKED'))  # the live notice's excerpt
        verdict = asks.classify(fixture['text'], final=True)
        self.assertTrue(verdict is None or verdict[3] is None, verdict)
        mentions = (line, '- `NEEDS-VICTOR`, `BLOCKED` and `DECISION-` markers count anywhere.',
                    'Scope:\n```\nNEEDS-VICTOR and BLOCKED lines count inside fences\n```', '- **BLOCKED** and **NEEDS-VICTOR** lines count anywhere.',
                    '- "Decision for you:" prose counts as an ask.', '- `Decision for you` lines are asks now.', 'NEEDS-VICTOR or BLOCKED, either one.')
        for text in mentions:
            with self.subTest(mention=text):
                verdict = asks.classify(text, final=True)
                self.assertTrue(verdict is None or verdict[3] is None, verdict)
        for text in ('- NEEDS-VICTOR t1 pick route A or B /x', 'NEEDS-VICTOR, BLOCKED: need the hub key /x',
                     'Open asks:\n```\nNEEDS-VICTOR p pick A or B /x\n```', '`NEEDS-VICTOR t1 approve the T05 push /x`',
                     'The reviewed result is **BLOCKED**: RESULT.md:1.', '**NEEDS-VICTOR:** pick A or B',
                     '**Decision for you:** may I also push T05 upstream?', 'C14 needs a decision from you before the push.',
                     'Closed as BLOCKED. The key never arrived.'):
            with self.subTest(ask=text):
                self.assertEqual(asks.classify(text, final=True)[3], 'BLOCKED')
        # Through a tick, the status as a thread's final reply: the candidate sends START only, the live base a BLOCKED too.
        rows = build(('user_message', 'brief', T0), ('assistant_message', fixture['text'], T0 + 1))
        self.tick(FakeT3(PROJECTS, {'s1': thread('s1', rows)}))
        self.assertEqual([label(p['occurrence']) for p in self.sent], ['generation-1-START'])
        live_sent = []
        (self.directory / 'live').mkdir()
        self.live_tick(live, FakeT3(PROJECTS, {'s1': thread('s1', [dict(i) for i in rows])}), T0 + 3600, self.directory / 'live',
                       send=lambda plan: (live_sent.append(plan), {'accepted': True})[1])
        self.assertEqual([p['occurrence'] for p in live_sent], ['generation-1-START', 'generation-1-BLOCKED'])

    def test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate(self):
        # Review round 3. Sol and DeepSeek: the mention filter read a marker followed by one of its nouns, or by joined
        # marker names, as a mention even when a colon labelled a real request, so asks the live base sends went
        # silent; and a marker then descriptive prose, an upper-case AND, or a coverage status sentence still sent.
        live = preimage_needs_victor()
        asking = ('NEEDS-VICTOR and BLOCKED: pick A or B before I can proceed.', 'NEEDS-VICTOR tokens expired; approve replacing the credentials.',
                  'BLOCKED: lines 40-60 were not applied. Which branch?', 'NEEDS-VICTOR: tokens for the T05 push expire tomorrow; rotate now?',
                  'BLOCKED: prefix check fails on F-D; may I bypass?', 'NEEDS-VICTOR: tags on release r3 are wrong; which set?',
                  'Decision for you: lines 40 or 60 for the fix?', 'NEEDS-VICTOR tokens expired.', 'NEEDS-VICTOR - tags on r3 are wrong',
                  '**NEEDS-VICTOR** and **BLOCKED**: the hub key is missing /x')
        naming = ('NEEDS-VICTOR AND BLOCKED markers count anywhere.', 'NEEDS-VICTOR status is now covered by the suite.',
                  'NEEDS-VICTOR matches inside fences and inline code.', 'NEEDS-VICTOR now matches inside code spans.',
                  'BLOCKED lines are now counted anywhere.', 'NEEDS-VICTOR detection is covered by 3 tests.',
                  'Decisions for Victor count as asks now.', 'NEEDS-VICTOR Or BLOCKED lines count.')
        for text in asking:
            with self.subTest(ask=text):
                self.assertEqual(asks.classify(text, final=True)[3], 'BLOCKED')
        for text in asking[:7]:
            with self.subTest(live_base=text):
                self.assertIsNotNone(live.classify(text, final=True))  # the live base sends these asks too
        for text in naming:
            with self.subTest(mention=text):
                verdict = asks.classify(text, final=True)
                self.assertTrue(verdict is None or verdict[3] is None, verdict)
        threads = {}
        for prefix, texts in (('a', asking), ('m', naming)):
            for n, text in enumerate(texts):
                threads['%s%d' % (prefix, n)] = thread('%s%d' % (prefix, n), build(('user_message', 'brief', T0), ('assistant_message', text, T0 + 1)))
        self.tick(FakeT3(PROJECTS, threads), max_notices=100, max_reads=100)
        self.assertEqual(sorted((p['thread_id'], label(p['occurrence'])) for p in self.sent),
                         sorted([(tid, 'generation-1-START') for tid in threads] + [('a%d' % n, 'generation-1-BLOCKED') for n in range(len(asking))]))


if __name__ == '__main__':
    unittest.main()
