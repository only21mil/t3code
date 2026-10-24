"""Victor GO 3:18 PM CT 2026-10-20: Sats hears START, BLOCKED (NEEDS-VICTOR included), DONE and URGENT, each at most
once per host:thread, durable generation and event state. FAILED and CANCELED keep their own state and use the
BLOCKED kind. Re-wakes, retries and duplicates each yield exactly one notice; status, replies, milestones, stalls
and replans send nothing; existing state is baselined on the first run without spam."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

import test_asks as base
from test_asks import ASK, FakeT3, PROJECTS, SCOPE, T0, build, iso, label, message, thread

asks, watchdog = base.asks, base.watchdog
ROOT = base.ROOT
UUID = '0b7f3c2e-6a1d-4e5f-9a8b-1c2d3e4f5a6b'
LATER = T0 + 90000


class Generations(base.Harness):
    def add(self, t, kind, text, at, run, status='completed'):
        item = message(len(t['items']), kind, text, at, run=run, ident='message:g%d' % len(t['items']), status=status)
        t['items'].append(item)
        t['meta'].update(updatedAt=iso(at), latestRunId=run)
        return item

    def sent_events(self):
        return [(p['thread_id'], label(p['occurrence']), p['kind']) for p in self.sent]

    def db(self):
        return sqlite3.connect(str(self.directory / 'asks.sqlite3'))

    def events(self, tid='t1'):
        state = asks.AskState(self.directory)
        try:
            return state.events('fd:' + tid)
        finally:
            state.close()

    def ask_rows(self):
        state = asks.AskState(self.directory)
        try:
            return [value for _, value in state.rows('asks', 'ask-')]
        finally:
            state.close()

    def generations(self, tid='t1'):
        state = asks.AskState(self.directory)
        try:
            return state.generations('fd:' + tid)
        finally:
            state.close()


class EventTests(Generations):
    def test_start_once_per_generation(self):
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start')])
        self.assertEqual(self.sent[0]['run'], 'generation-1')
        for n in range(2, 5):  # re-wakes: new runs, new assistant output, no user message
            self.add(t1, 'assistant_message', 'working %d' % n, T0 + 100 * n, 'run:thread:t1:ordinal:%d' % n)
            self.assertEqual(self.tick(client, now=T0 + 3600 + n)[0], 0)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual([n for n, _ in self.generations()], [1])

    def test_done_once_on_the_done_reply_never_on_settle(self):
        # notice-delay-rca-20261023 patch 1: DONE is the generation's own reply that leads with DONE, once its turn
        # has ended and TURN_GRACE has passed. A settle neither sends it nor is needed for it.
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'All checks pass; RESULT.md written.', T0 + 60)))
        t2 = thread('t2', build(('user_message', 'brief', T0), ('assistant_message', 'DONE. All checks pass; RESULT.md written.', T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1, 't2': t2})
        self.assertEqual(self.tick(client)[0], 3)  # START each, and t2's DONE; t1's report does not lead with DONE
        for t in (t1, t2):
            t['meta'].update(settled=True, settledAt=iso(T0 + 120), updatedAt=iso(T0 + 120))
        self.assertEqual(self.tick(client, now=LATER)[0], 0)  # the settle sends nothing
        t2['meta'].update(settledAt=iso(T0 + 200), updatedAt=iso(T0 + 200))  # a second settle of the same work
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)
        self.assertEqual(sorted(self.sent_events()), [('t1', 'generation-1-START', 'start'), ('t2', 'generation-1-DONE', 'done'),
                                                      ('t2', 'generation-1-START', 'start')])

    def test_needs_victor_then_a_different_blocked_line_are_two_asks(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'NEEDS-VICTOR t1 pick A or B /x', T0 + 60)))
        self.assertEqual(asks.classify('NEEDS-VICTOR t1 pick A or B /x', final=True)[0], 'decision')  # the old label
        client = FakeT3(PROJECTS, {'t1': t1})
        self.assertEqual(self.tick(client)[0], 2)
        self.assertEqual(self.sent_events()[1], ('t1', 'generation-1-BLOCKED', 'blocker'))  # relabeled to BLOCKED
        # notice-package-20261023 item 6: a re-wake that blocks on something else is a new ask with its own notice;
        # repeating it, or the first ask, sends nothing more.
        self.add(t1, 'assistant_message', 'BLOCKED: still need the key /x/RESULT.md', T0 + 300, 'run:thread:t1:ordinal:2')
        self.assertEqual(self.tick(client, now=LATER)[0], 1)
        self.add(t1, 'assistant_message', 'BLOCKED: still need the key /x/RESULT.md', T0 + 400, 'run:thread:t1:ordinal:3')
        self.add(t1, 'assistant_message', 'NEEDS-VICTOR t1 pick A or B /x', T0 + 500, 'run:thread:t1:ordinal:4')
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-BLOCKED', 'generation-1-BLOCKED'])
        self.assertEqual(len({p['occurrence'] for p in self.sent}), 3)
        self.assertEqual({a['state'] for a in self.ask_rows()}, {'bound'})

    def test_urgent_sends_once_and_only_when_qualifying(self):
        for text in ('URGENT security: token in the log /x', '**URGENT** data at risk: backup disk at 99%',
                     '1. URGENT destructive migration is running on prod'):
            with self.subTest(text=text):
                self.assertIsNotNone(asks.URGENT_RE.search(text))
        for text in ('URGENT: please look', 'Not URGENT security', 'The URGENT security note is resolved.',
                     'urgent security: lower case', 'URGENTLY security'):
            with self.subTest(text=text):
                self.assertIsNone(asks.URGENT_RE.search(text))
        t1 = thread('t1', build(('user_message', 'brief', T0),
                                ('assistant_message', 'URGENT: please look at the dashboard', T0 + 10),
                                ('assistant_message', '```\nURGENT security: in a fence\n```\nfine', T0 + 20),
                                ('assistant_message', 'URGENT security: token printed in the CI log /x/RESULT.md', T0 + 30),
                                ('assistant_message', 'URGENT data at risk: disk at 99%', T0 + 40)), status='running')
        # Answered before the scan: a later user message closes the URGENT line, so it never sends.
        t2 = thread('t2', build(('user_message', 'brief', T0), ('assistant_message', 'URGENT security: key leaked /y', T0 + 10),
                                ('user_message', 'Victor: rotated it', T0 + 20)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1, 't2': t2})
        # URGENT rides its own urgent kind, once per generation, never relabeled as another kind.
        self.assertEqual(self.tick(client)[0], 3)
        self.assertEqual(sorted(self.sent_events()), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-1-URGENT', 'urgent'),
                                                      ('t2', 'generation-1-START', 'start')])
        urgent = [e for e in self.events() if e['state'] == 'URGENT']
        self.assertEqual([(e['status'], e['kind'], e['position'], e['occurrence']) for e in urgent],
                         [('sent', 'urgent', 3, 'generation-1-URGENT')])
        self.assertEqual([e['state'] for e in self.events('t2')], ['START'])
        self.add(t1, 'assistant_message', 'URGENT destructive: deleting the bucket now', T0 + 50, 'run:thread:t1:ordinal:2')
        self.assertEqual(self.tick(client, now=LATER)[0], 0)  # a re-wake repeats URGENT: the generation has its one
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)
        self.assertEqual(len([e for e in self.events() if e['state'] == 'URGENT']), 1)
        self.assertEqual(len(self.sent), 3)

    def test_failed_and_canceled_are_blocked_kind_with_their_own_keys(self):
        self.assertEqual(asks.classify('FAILED: build broke /x/RESULT.md', final=True)[3], 'FAILED')
        self.assertEqual(asks.classify('mcp:cb22985a CANCELLED by owner stop /x', final=True)[3], 'CANCELED')
        self.assertIsNone(asks.classify('FAILED: build broke /x', final=False))  # final messages only
        self.assertIsNone(asks.classify('Not FAILED yet; tests still run.', final=True))
        self.assertIsNone(asks.classify('Two tests FAILED earlier and pass now.', final=True))
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'FAILED: build broke /x/RESULT.md', T0 + 10)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.assertEqual(self.tick(client)[0], 2)
        self.add(t1, 'assistant_message', 'FAILED again: same error /x', T0 + 100, 'run:thread:t1:ordinal:2')  # re-wake repeat
        self.assertEqual(self.tick(client, now=LATER)[0], 0)
        self.add(t1, 'assistant_message', 'CANCELED: owner stopped the work /x', T0 + 200, 'run:thread:t1:ordinal:3')
        self.assertEqual(self.tick(client, now=LATER + 100)[0], 1)
        self.assertEqual(self.tick(client, now=LATER + 200)[0], 0)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-1-FAILED', 'blocker'),
                                              ('t1', 'generation-1-CANCELED', 'blocker')])
        self.assertEqual(sorted(e['state'] for e in self.events()), ['CANCELED', 'FAILED', 'START'])
        self.assertTrue(all('FAILED' in p['message'] or 'CANCELED' in p['message'] for p in self.sent[1:]))

    def test_rewake_with_new_run_id_sends_nothing_new(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        for n in range(2, 6):
            self.add(t1, 'assistant_message', 'Still waiting.\n' + ASK, T0 + 100 * n, 'run:thread:t1:ordinal:%d' % n)
            self.assertEqual(self.tick(client, now=LATER + n)[0], 0)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-BLOCKED'])
        blocked = [e['event_id'] for e in self.events() if e['state'] == 'BLOCKED']
        self.assertEqual(({a['event_id'] for a in self.ask_rows()}, len(blocked)), (set(blocked), 1))

    def test_duplicate_ticks_messages_and_concurrent_claims_are_one(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'Checking.\n' + ASK, T0 + 1),
                                ('assistant_message', ASK, T0 + 2)))
        client = FakeT3(PROJECTS, {'t1': t1})
        for _ in range(3):
            self.tick(client)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-BLOCKED'])
        first, second = asks.AskState(self.directory), asks.AskState(self.directory)
        try:
            value = asks.event('fd', 't1', 1, 'DONE', 2, T0)
            with first.transaction():
                self.assertTrue(first.claim(value))
            with second.transaction():
                self.assertFalse(second.claim(dict(value, message='different bytes')))
            with self.assertRaises(sqlite3.IntegrityError):
                with second.transaction():
                    second.db.execute('INSERT INTO generations VALUES (?,?,?,?)', ('fd:t1', 9, 'message:message:0', '{}'))
            with self.assertRaises(sqlite3.IntegrityError):
                with second.transaction():
                    second.db.execute('INSERT INTO events VALUES (?,?,?,?,?)', ('event-other', 'fd:t1', 1, 'START', '{}'))
        finally:
            first.close()
            second.close()
        self.assertEqual(self.events()[-1]['message'], value['message'])

    def test_resume_and_new_objective_open_new_generations_with_start(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.add(t1, 'user_message', 'Victor: GO on option A', T0 + 4000, 'run:thread:t1:ordinal:2')
        self.add(t1, 'assistant_message', 'DONE: option A applied.', T0 + 4100, 'run:thread:t1:ordinal:2')
        self.tick(client, now=LATER)
        t1['meta'].update(settled=True, settledAt=iso(T0 + 4200), updatedAt=iso(T0 + 4200))
        self.tick(client, now=LATER + 1)
        t1['meta'].update(settled=False, settledAt=None)
        self.add(t1, 'user_message', 'New objective: rotate the logs', T0 + 5000, 'run:thread:t1:ordinal:3')
        self.tick(client, now=LATER + 2)
        self.assertEqual([o for _, o, _ in self.sent_events()],
                         ['generation-1-START', 'generation-1-BLOCKED', 'generation-2-START', 'generation-2-DONE', 'generation-3-START'])
        self.assertEqual([(n, g['origin']) for n, g in self.generations()],
                         [(1, 'message:message:0'), (2, 'message:message:g2'), (3, 'message:message:g4')])

    def test_steer_inside_unfinished_work_joins_the_generation(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'working', T0 + 10)), status='running')
        t1['meta']['activeRunId'] = 'run:thread:t1:ordinal:1'
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.add(t1, 'user_message', '[From Sats] also check the mini', T0 + 20, 'run:thread:t1:ordinal:1')
        self.add(t1, 'user_message', '[From Sats] status?', T0 + 30, 'run:thread:t1:ordinal:2')
        self.add(t1, 'assistant_message', 'DONE: both checked.', T0 + 40, 'run:thread:t1:ordinal:2')
        self.tick(client, now=LATER)  # still running: its DONE waits for the turn to end
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START'])
        t1['meta'].update(status='completed', updatedAt=iso(T0 + 50))
        self.tick(client, now=LATER + 1)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-DONE'])

    def test_dismissal_settle_after_blocked_is_not_done(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        t1['meta'].update(settled=True, settledAt=iso(T0 + 4000), updatedAt=iso(T0 + 4000))
        self.assertEqual(self.tick(client, now=LATER)[0], 0)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-BLOCKED'])

    def test_status_replies_and_milestones_send_nothing(self):
        texts = ('Status: 3 of 5 producers done; reviews start after.', 'Milestone 2 reached; RESULT.md updated.',
                 'Answered your question: the key lives in the vault.', 'Done with phase 1, starting phase 2.',
                 'Should I also clean the logs?', 'Recorded as DECISION-PUSH-2 in DECISION-PUSH.md')
        rows = [('user_message', 'brief', T0)] + [('assistant_message', text, T0 + n) for n, text in enumerate(texts, 1)]
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(*rows))})
        count, events = self.tick(client)
        self.assertEqual((count, self.sent_events()), (1, [('t1', 'generation-1-START', 'start')]))
        self.assertEqual({a['state'] for a in self.ask_rows()}, {'local'})
        self.assertEqual(self.tick(client, now=LATER)[0], 0)

    def test_SOL1_a_done_led_progress_line_then_a_final_progress_reply_sends_no_done(self):
        # Sol's two-phase probe: DONE is the generation's final reply at claim time, so a DONE-led status line that a
        # later progress reply follows is progress. Read in one tick and across ticks, the turn ends with no DONE.
        rows = [('user_message', 'brief', T0), ('assistant_message', 'DONE with phase 1, starting phase 2.', T0 + 1),
                ('assistant_message', 'Phase 2 running.', T0 + 2)]
        client = FakeT3(PROJECTS, {'t1': thread('t1', build(*rows))})
        self.assertEqual(self.tick(client)[0], 1)
        t2 = thread('t2', build(*rows[:2]), status='running')
        t2['meta']['activeRunId'] = t2['items'][-1]['runId']
        client.threads['t2'] = t2
        self.tick(client, now=T0 + 100)  # the DONE-led line is read while its turn still runs
        self.add(t2, 'assistant_message', 'Phase 2 running.', T0 + 200, t2['items'][-1]['runId'])
        t2['meta'].update(status='completed', activeRunId=None)
        self.tick(client, now=LATER)
        self.assertEqual(sorted(self.sent_events()), [('t1', 'generation-1-START', 'start'), ('t2', 'generation-1-START', 'start')])
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)
        # Phase 2 finishes with its own DONE-led final reply: that is the generation's one DONE.
        self.add(t2, 'assistant_message', 'DONE. Both phases pass.', T0 + 300, t2['items'][-1]['runId'])
        self.tick(client, now=LATER + 2)
        self.assertEqual([o for t, o, _ in self.sent_events() if t == 't2'], ['generation-1-START', 'generation-1-DONE'])
        self.assertEqual([e['position'] for e in self.events('t2') if e['state'] == 'DONE'], [3])

    def test_SOL1_kimi_replies_that_restate_done_keep_it_on_the_done_replys_run(self):
        # mini 3e9f5d46 (RCA check_done.py texts): the DONE reply, then two later replies that restate DONE, the last
        # in a background-task wake run. The DONE still sends, once, for the DONE reply and its own run.
        kimi = ['DONE. Verdict: trial K3.1 Pro for bounded hard coding. Not fleet-wide yet.',
                'Those are late notices. The objective is DONE and settled.', 'Stale background scans stopped. The research stays DONE.']
        t1 = thread('t1', build(('user_message', 'brief', T0), *[('assistant_message', text, T0 + n) for n, text in enumerate(kimi, 1)]))
        t1['items'][-1]['runId'] = t1['meta']['latestRunId'] = 'run:thread:t1:ordinal:4'  # the wake
        self.assertEqual(self.tick(FakeT3(PROJECTS, {'t1': t1}))[0], 2)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-1-DONE', 'done')])
        done = next(e for e in self.events() if e['state'] == 'DONE')
        self.assertEqual((done['position'], done['turn_run']), (1, 'run:thread:t1:ordinal:1'))
        self.assertTrue(asks.keeps_done(kimi[1]) and asks.keeps_done(kimi[2]))
        self.assertFalse(any(asks.keeps_done(text) for text in ('Phase 2 running.', 'Phase 1 is DONE; phase 2 is running.',
                                                                'The objective is not DONE.', 'Nothing is DONE yet.')))

    def test_DSH2_single_read_message_after_a_done_reply_opens_a_generation(self):
        # DeepSeek's single-read probe: one read holds the DONE reply and Victor's follow-up. The follow-up closes
        # generation 1, whose DONE is claimed first for the DONE reply's own run, and opens generation 2 with its own
        # START; generation 2's progress reply sends nothing.
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'DONE. Report written.', T0 + 60),
                                ('user_message', 'Victor: also check the mini', T0 + 200),
                                ('assistant_message', 'Checking the mini now.', T0 + 260)))
        for item in t1['items'][2:]:
            item['runId'] = 'run:thread:t1:ordinal:2'
        self.assertEqual(self.tick(FakeT3(PROJECTS, {'t1': t1}))[0], 3)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-1-DONE', 'done'),
                                              ('t1', 'generation-2-START', 'start')])
        done = next(e for e in self.events() if e['state'] == 'DONE')
        self.assertEqual((done['generation'], done['position'], done['turn_run']), (1, 1, 'run:thread:t1:ordinal:1'))
        self.assertEqual([(n, g['position'], g.get('done_at')) for n, g in self.generations()], [(1, 0, 1), (2, 2, None)])

    def test_DSH2_grace_reread_message_after_a_done_reply_opens_a_generation(self):
        # DeepSeek's grace-reread probe: the DONE waits inside TURN_GRACE, then Victor's follow-up starts run 2 before
        # the reread. The reread claims generation 1's DONE for run 1 and opens generation 2; run 2 ends without a DONE.
        end = T0 + 60
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'DONE. Report written.', end)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=end + 30)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start')])
        self.add(t1, 'user_message', 'Victor: also check the mini', end + 100, 'run:thread:t1:ordinal:2')
        t1['meta'].update(status='running', activeRunId='run:thread:t1:ordinal:2')
        self.tick(client, now=end + 330)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-1-DONE', 'done'),
                                              ('t1', 'generation-2-START', 'start')])
        self.assertEqual(next(e['turn_run'] for e in self.events() if e['state'] == 'DONE'), 'run:thread:t1:ordinal:1')
        self.add(t1, 'assistant_message', 'Checked the mini; one more log to read.', end + 400, 'run:thread:t1:ordinal:2')
        t1['meta'].update(status='completed', activeRunId=None)
        self.assertEqual(self.tick(client, now=end + 1000)[0], 0)
        self.assertEqual(len(self.sent), 3)

    def test_DSH2_a_follow_up_inside_the_done_replys_grace_claims_that_done_after_the_grace(self):
        # The follow-up lands while the DONE reply's turn is inside TURN_GRACE: generation 2 opens at once and
        # generation 1's DONE goes out on the next tick, for run 1.
        end = T0 + 60
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'DONE. Report written.', end),
                                ('user_message', 'Victor: thanks, archive it', end + 10)))
        t1['items'][-1]['runId'] = 'run:thread:t1:ordinal:2'
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=end + 20)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-2-START', 'start')])
        self.tick(client, now=end + 330)
        self.assertEqual(self.sent_events()[2:], [('t1', 'generation-1-DONE', 'done')])
        self.assertEqual(self.tick(client, now=end + 630)[0], 0)


class RepairRound1Tests(Generations):
    """notice-package-20261023 round 1: SOL-3 (a record read while its message streamed is decided on its completed
    text) and SOL-4 (an ask's decision ID is its identity)."""

    def test_SOL3_a_streamed_decision_id_line_that_completes_as_decision_for_you_sends(self):
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        t1['meta']['activeRunId'] = 'run:thread:t1:ordinal:1'
        streaming = self.add(t1, 'assistant_message', 'Recording DECISION-P05-DELETE on the board', T0 + 10,
                             'run:thread:t1:ordinal:1', status='streaming')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=T0 + 20)
        self.assertEqual([(a['state'], a['event']) for a in self.ask_rows()], [('local', None)])  # an ID alone is local
        streaming.update(status='completed', text='Recording DECISION-P05-DELETE on the board.\n'
                                                   '**Decision for you:** should P05 delete `[mcp_servers.t3]` from the F-D config?')
        t1['meta'].update(status='completed', activeRunId=None, updatedAt=iso(T0 + 30))
        self.tick(client, now=LATER)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START', 'generation-1-BLOCKED'])
        self.assertEqual([(a['state'], a['event']) for a in self.ask_rows()], [('bound', 'BLOCKED')])
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)

    def test_SOL3_a_pending_ask_whose_completed_text_asks_nothing_stays_local(self):
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        t1['meta']['activeRunId'] = 'run:thread:t1:ordinal:1'
        streaming = self.add(t1, 'assistant_message', 'NEEDS-VICTOR t1 pick A or B /x', T0 + 10, 'run:thread:t1:ordinal:1', status='streaming')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=T0 + 20)
        self.assertEqual([a['state'] for a in self.ask_rows()], ['pending'])
        streaming.update(status='completed', text='Picked A myself; the brief allows it. Report written.')
        t1['meta'].update(status='completed', activeRunId=None, updatedAt=iso(T0 + 30))
        self.tick(client, now=LATER)
        self.assertEqual([o for _, o, _ in self.sent_events()], ['generation-1-START'])
        self.assertEqual([(a['state'], a['event']) for a in self.ask_rows()], [('local', None)])

    def test_SOL4_a_reworded_ask_with_the_same_decision_id_is_one_notice(self):
        threads = {tid: thread(tid, build(('user_message', 'brief', T0),
                                          ('assistant_message', 'NEEDS-VICTOR DECISION-PUSH-2 approve pushing T05 /x/RESULT.md', T0 + 1)))
                   for tid in ('t1', 't2')}
        client = FakeT3(PROJECTS, threads)
        self.assertEqual(self.tick(client)[0], 4)
        # A re-wake rewords t1's ask under the same decision ID, and asks t2 a second decision under its own ID.
        self.add(threads['t1'], 'assistant_message', 'Still waiting.\nNEEDS-VICTOR DECISION-PUSH-2: is T05 OK to push upstream? /x/RESULT.md',
                 T0 + 300, 'run:thread:t1:ordinal:2')
        self.add(threads['t2'], 'assistant_message', 'NEEDS-VICTOR DECISION-KEY-3 rotate the hub key /y/RESULT.md',
                 T0 + 300, 'run:thread:t2:ordinal:2')
        self.tick(client, now=LATER)
        blocked = sorted((t, o) for t, o, _ in self.sent_events() if o == 'generation-1-BLOCKED')
        self.assertEqual(blocked, [('t1', 'generation-1-BLOCKED'), ('t2', 'generation-1-BLOCKED'), ('t2', 'generation-1-BLOCKED')])
        self.assertEqual(asks.decision_ids({'markers': ['Recorded as DECISION-PUSH-2 in DECISION-PUSH.md']}), [])  # a cited ID
        self.assertEqual(asks.ask_key({'markers': ['NEEDS-VICTOR DECISION-PUSH-2 approve /x']}),
                         asks.ask_key({'markers': ['NEEDS-VICTOR DECISION-PUSH-2: OK to push? /x', 'Logged DECISION-OLD-1']}))


class SolLifecycleTests(Generations):
    """Code review SOL-01 and SOL-02: interleavings between periodic scans."""

    def test_answer_after_unobserved_block_opens_generation(self):
        # A NEEDS-VICTOR message and Victor's answer both land between two scans of an open generation.
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.add(t1, 'assistant_message', ASK, T0 + 10, 'run:thread:t1:ordinal:1')
        self.add(t1, 'user_message', 'Victor: GO on option A', T0 + 20, 'run:thread:t1:ordinal:2')
        self.add(t1, 'assistant_message', 'Option A complete.', T0 + 30, 'run:thread:t1:ordinal:2')
        t1['meta']['status'] = 'completed'
        self.tick(client, now=LATER)
        self.assertEqual([n for n, _ in self.generations()], [1, 2])
        # The answered blocker stays unsent; the answer is new work with its own START.
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-2-START', 'start')])

    def test_answer_after_block_held_in_turn_grace_opens_generation(self):
        # The blocker is seen while its turn may still post its own notice, so no event is claimed; the answer
        # arrives by the next scan. The generation's end is kept from the first scan, not from the event row.
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 10)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client, now=T0 + 15)
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start')])
        self.add(t1, 'user_message', 'Victor: GO on option A', T0 + 20, 'run:thread:t1:ordinal:2')
        self.tick(client, now=LATER)
        self.assertEqual([n for n, _ in self.generations()], [1, 2])
        self.assertEqual(self.sent_events(), [('t1', 'generation-1-START', 'start'), ('t1', 'generation-2-START', 'start')])

    def settle_after_terminal_seen_while_running(self, text):
        # The completed terminal message is first read while the thread still runs (not final, so unclassified),
        # then reread at the same position after completion and settle.
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', text, T0 + 10)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        t1['meta'].update(status='completed', settled=True, settledAt=iso(T0 + 20), updatedAt=iso(T0 + 20))
        self.tick(client, now=LATER)
        self.assertEqual([kind for _, _, kind in self.sent_events()], ['start'])
        self.assertTrue(self.generations()[-1][1]['last_marked'])

    def test_settle_after_completed_blocker_seen_while_running_is_not_done(self):
        self.settle_after_terminal_seen_while_running('BLOCKED: need the key /x/RESULT.md')

    def test_settle_after_completed_failed_seen_while_running_is_not_done(self):
        self.settle_after_terminal_seen_while_running('FAILED: build broke /x/RESULT.md')

    def test_settle_after_completed_canceled_seen_while_running_is_not_done(self):
        self.settle_after_terminal_seen_while_running('CANCELED: owner stopped the work /x')

    def answer_after_unobserved_terminal_reply(self, text):
        # Code re-review round 2: run 1 ends with a terminal reply and Victor answers in run 2, all between two
        # scans, so the reply is never the last item read. t2 is the control: the same words mid-turn, followed by
        # more work in the same run, end nothing, so Victor's later message there still joins generation 1.
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        t2 = thread('t2', build(('user_message', 'brief', T0)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1, 't2': t2})
        self.tick(client)
        self.add(t1, 'assistant_message', text, T0 + 10, 'run:thread:t1:ordinal:1')
        self.add(t1, 'user_message', 'Victor: GO on option A', T0 + 20, 'run:thread:t1:ordinal:2')
        self.add(t1, 'assistant_message', 'Option A complete.', T0 + 30, 'run:thread:t1:ordinal:2')
        self.add(t2, 'assistant_message', text, T0 + 10, 'run:thread:t2:ordinal:1')
        self.add(t2, 'assistant_message', 'Retried; all checks pass.', T0 + 15, 'run:thread:t2:ordinal:1')
        self.add(t2, 'user_message', 'Victor: thanks', T0 + 20, 'run:thread:t2:ordinal:2')
        t1['meta']['status'] = t2['meta']['status'] = 'completed'
        self.tick(client, now=LATER)
        self.assertEqual([n for n, _ in self.generations()], [1, 2])
        self.assertEqual([n for n, _ in self.generations('t2')], [1])
        # The obsolete terminal notice stays unsent; the answer is new work with its own START.
        expected = [('t1', 'generation-1-START', 'start'), ('t1', 'generation-2-START', 'start'), ('t2', 'generation-1-START', 'start')]
        self.assertEqual(sorted(self.sent_events()), expected)
        self.assertEqual(self.tick(client, now=LATER + 1)[0], 0)  # a later scan of the same state sends nothing
        self.assertEqual(sorted(self.sent_events()), expected)

    def test_answer_after_unobserved_final_blocked_opens_generation(self):
        self.answer_after_unobserved_terminal_reply('BLOCKED: need the key /x/RESULT.md')

    def test_answer_after_unobserved_final_failed_opens_generation(self):
        self.answer_after_unobserved_terminal_reply('FAILED: build broke /x/RESULT.md')

    def test_answer_after_unobserved_final_canceled_opens_generation(self):
        self.answer_after_unobserved_terminal_reply('CANCELED: owner stopped the work /x')


LIVE_HOOK = 'live-20261020/sats-completion-notify'
CANDIDATE_HOOK = 'candidate-20261020/sats-completion-notify'  # = code-round candidate/bin/sats-completion-notify


class InertLiveHook(Generations):
    """The frozen live hook (preimage/live-20261020, a1e138ca) through tests/inert_hook.py: real identity,
    payload freeze, acceptance proof and attempt ledger, only the POST replaced."""
    HOOK = LIVE_HOOK

    def setUp(self):
        super().setUp()
        self.registry = self.directory / 'bindings.json'
        self.registry.write_text('[]\n')
        self.registry.chmod(0o600)
        env = patch.dict(os.environ, {'WATCHDOG_TEST_ROOT': str(self.directory), 'WATCHDOG_TEST_STATUS': '200',
                                      'WATCHDOG_TEST_HOOK': self.HOOK, 'WATCHDOG_TEST_RUN_ID': UUID,
                                      'PYTHONDONTWRITEBYTECODE': '1', 'SATS_TEST': '1', 'SATS_STEP': 'unrelated-parent-step'})
        env.start()
        self.addCleanup(env.stop)
        self.hook = watchdog.AskTransport({'hook_cli': str(ROOT / 'tests/inert_hook.py'),
                                           'hook_state_dir': str(self.directory / 'hook-state')}, self.directory)

    def posts(self):
        path = self.directory / 'posts.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_transport_retry_after_ambiguous_result_is_one_notice(self):
        calls = []

        def ambiguous(plan):
            receipt = self.hook(plan)  # the hook posts and records its proof
            calls.append((label(plan['occurrence']), receipt.get('sats_receipt')))
            if len(calls) == 1:
                return {'transport': 'hook', 'accepted': False, 'reason': 'hook-timeout'}  # but the caller saw a timeout
            return receipt
        self.send = ambiguous
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.assertEqual([e['status'] for e in self.events()], ['pending', 'sent'])  # START ambiguous, BLOCKED sent
        self.tick(client, now=LATER)
        self.tick(client, now=LATER + 1)
        self.assertEqual([e['status'] for e in self.events()], ['sent', 'sent'])
        self.assertEqual(calls, [('generation-1-START', 'DELIVERED'), ('generation-1-BLOCKED', 'DELIVERED'),
                                 ('generation-1-START', 'DELIVERED')])
        posts = self.posts()
        # The retry reused the hook's proof: one POST per event, each keyed thread + generation + state.
        self.assertEqual([(p['event_kind'], p['run'], label(p['notice_occurrence'])) for p in posts],
                         [('start', 'generation-1', 'generation-1-START'), ('blocker', 'generation-1', 'generation-1-BLOCKED')])
        self.assertEqual(len({p['event_id'] for p in posts}), 2)
        self.assertTrue(all(p['recipient'] == 'Sats' and p['notice_binding']['owner_thread_id'] == 't1' for p in posts))
        self.assertIsNone(posts[0]['step'])  # parent SATS_* stripped
        self.assertIn('generation-1-BLOCKED', posts[1]['message'])  # the event state rides the body

    def test_restart_persists_claims_and_retries_the_same_occurrence(self):
        os.environ['WATCHDOG_TEST_STATUS'] = '503'
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = self.hook
        for n in range(4):  # each tick reopens the state, as each timer run does
            self.tick(client, now=LATER + n)
        statuses = {e['state']: (e['status'], e['attempts']) for e in self.events()}
        self.assertEqual(statuses, {'START': ('failed', 3), 'BLOCKED': ('failed', 3)})
        posts = self.posts()
        # The hook's own ledger caps attempts per occurrence: three POSTs each, one event id each, same bytes.
        self.assertEqual(sorted(label(p['notice_occurrence']) for p in posts), ['generation-1-BLOCKED'] * 3 + ['generation-1-START'] * 3)
        self.assertEqual(len({p['event_id'] for p in posts}), 2)
        self.assertEqual(len({json.dumps(p, sort_keys=True) for p in posts}), 2)
        # Generation numbering survives restarts: the next accepted message is generation 2.
        self.add(t1, 'user_message', 'Victor: retry with the new key', T0 + 9000, 'run:thread:t1:ordinal:2')
        os.environ['WATCHDOG_TEST_STATUS'] = '200'
        self.tick(client, now=LATER + 10)
        self.assertEqual(self.posts()[-1]['notice_occurrence'], 'generation-2-START')

    def test_interrupted_last_attempt_is_not_sent_again(self):
        t1 = thread('t1', build(('user_message', 'brief', T0)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = lambda plan: {'transport': 'hook', 'accepted': False, 'reason': 'hook-timeout'}
        self.tick(client)
        connection = self.db()
        try:
            row = json.loads(connection.execute("SELECT data FROM events WHERE state='START'").fetchone()[0])
            row.update(attempts=3, status='attempting')  # the process died inside its third attempt
            connection.execute("UPDATE events SET data=? WHERE state='START'", (json.dumps(row),))
            connection.commit()
        finally:
            connection.close()
        self.send = self.hook
        self.tick(client, now=LATER)
        self.assertEqual(self.posts(), [])
        self.assertEqual(self.events()[0]['status'], 'failed')

    def test_thread_own_done_notice_suppresses_the_watchdog_done(self):
        import hashlib
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', 'DONE. All checks pass.', T0 + 60)),
                    status='running')
        t1['meta']['activeRunId'] = t1['meta']['latestRunId']
        t1['items'][-1]['runId'] = t1['meta']['latestRunId']  # the DONE reply is the running turn's; it posts its own DONE
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = self.hook
        self.tick(client)  # the turn still runs: START only
        run = t1['meta']['latestRunId']
        key = hashlib.sha256(json.dumps(['t3-t1', 't1', 'done', run], separators=(',', ':')).encode()).hexdigest()
        (self.directory / 'hook-state' / 'milestones' / (key + '.acceptance.json')).write_text(
            json.dumps({'http_status': 200, 'recipient_run_id': UUID}))  # the turn posts its own DONE before it ends
        t1['meta'].update(status='completed', activeRunId=None, updatedAt=iso(T0 + 120))
        self.tick(client, now=LATER)
        self.assertEqual([p['notice_occurrence'] for p in self.posts()], ['generation-1-START'])
        self.assertEqual({e['state']: e['status'] for e in self.events()}, {'START': 'sent', 'DONE': 'thread-notice'})


class InertCandidateHook(InertLiveHook):
    """The same checks through the candidate hook (preimage/candidate-20261020), which adds only the urgent kind,
    then URGENT end to end: one POST per generation through the real hook code, retries reuse its proof."""
    HOOK = CANDIDATE_HOOK

    URGENT_LINE = 'URGENT security: token printed in the CI log /x/RESULT.md'

    def test_urgent_sends_once_through_the_hook(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', self.URGENT_LINE, T0 + 30)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = self.hook
        self.assertEqual(self.tick(client)[0], 2)
        self.add(t1, 'assistant_message', 'URGENT destructive: deleting the bucket now', T0 + 50, 'run:thread:t1:ordinal:2')
        for n in range(3):  # re-wake with a second URGENT line, then duplicate ticks
            self.assertEqual(self.tick(client, now=LATER + n)[0], 0)
        posts = self.posts()
        self.assertEqual([(p['event_kind'], p['run'], p['notice_occurrence'], p['outcome']) for p in posts],
                         [('start', 'generation-1', 'generation-1-START', 'START'),
                          ('urgent', 'generation-1', 'generation-1-URGENT', 'URGENT')])
        self.assertTrue(all(p['recipient'] == 'Sats' and p['notice_binding']['owner_thread_id'] == 't1' for p in posts))
        self.assertIn('kind: "urgent"', posts[1]['message'])
        self.assertIn('generation-1-URGENT', posts[1]['message'])
        self.assertNotIn('tell_victor', posts[1])
        self.assertEqual({e['state']: (e['status'], e['receipt'].get('recipient_run_id')) for e in self.events()},
                         {'START': ('sent', UUID), 'URGENT': ('sent', UUID)})

    def test_urgent_retry_after_ambiguous_result_is_one_notice(self):
        calls = []

        def ambiguous(plan):
            receipt = self.hook(plan)
            calls.append(plan['occurrence'])
            if plan['occurrence'].endswith('URGENT') and calls.count(plan['occurrence']) == 1:
                return {'transport': 'hook', 'accepted': False, 'reason': 'hook-timeout'}  # posted, but the caller timed out
            return receipt
        self.send = ambiguous
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', self.URGENT_LINE, T0 + 30)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.tick(client)
        self.assertEqual({e['state']: e['status'] for e in self.events()}, {'START': 'sent', 'URGENT': 'pending'})
        self.tick(client, now=LATER)
        self.tick(client, now=LATER + 1)
        self.assertEqual({e['state']: (e['status'], e['attempts']) for e in self.events()}, {'START': ('sent', 1), 'URGENT': ('sent', 2)})
        self.assertEqual(calls, ['generation-1-START', 'generation-1-URGENT', 'generation-1-URGENT'])
        self.assertEqual([p['notice_occurrence'] for p in self.posts()], ['generation-1-START', 'generation-1-URGENT'])

    def test_urgent_restart_after_transport_failure_retries_the_same_occurrence(self):
        os.environ['WATCHDOG_TEST_STATUS'] = '503'
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', self.URGENT_LINE, T0 + 30)), status='running')
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = self.hook
        for n in range(4):
            self.tick(client, now=LATER + n)
        self.assertEqual({e['state']: (e['status'], e['attempts']) for e in self.events()}, {'START': ('failed', 3), 'URGENT': ('failed', 3)})
        urgent = [p for p in self.posts() if p['event_kind'] == 'urgent']
        # The hook's ledger caps the occurrence at three POSTs of identical bytes; urgent is not requeued (not terminal).
        self.assertEqual(len(urgent), 3)
        self.assertEqual(len({json.dumps(p, sort_keys=True) for p in urgent}), 1)
        self.assertEqual(sorted((self.directory / 'hook-state' / 'requeue').glob('*.json')), [])

    def test_urgent_payload_passes_the_consumer_identity_check(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', self.URGENT_LINE, T0 + 30)), status='running')
        self.send = self.hook
        self.tick(FakeT3(PROJECTS, {'t1': t1}))
        payload = next(p for p in self.posts() if p['event_kind'] == 'urgent')

        def consumer(hook):
            loader = importlib.machinery.SourceFileLoader

            def frozen(name, path):
                return loader(name, str(ROOT / 'tests/preimage' / hook) if name == 'p5b_notifier' else path)
            with patch('importlib.machinery.SourceFileLoader', side_effect=frozen):
                loaded = importlib.machinery.SourceFileLoader('urgent_consumer', str(ROOT / 'tests/preimage/lightning_consumer.py'))
                module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loaded.name, loaded))
                loaded.exec_module(module)
                return module

        def check(module):  # lightning_consumer.forward's first check, on the posted body
            return module.notice.required_notice(payload, payload.get('event_kind'), payload.get('review_round'),
                                                 payload.get('notice_occurrence'), binding=payload['notice_binding'])
        # The consumer revalidates with the installed hook's NOTICE_KINDS: the candidate rebuilds the identical body ...
        self.assertEqual(check(consumer(CANDIDATE_HOOK)), payload)
        # ... while the live hook rejects the kind, which is why NOTICE_KINDS gains urgent with MILESTONE_KINDS.
        with self.assertRaisesRegex(ValueError, 'notice identity required'):
            check(consumer(LIVE_HOOK))


class HookKindTests(unittest.TestCase):
    """The hook change is additive: every existing milestone kind produces the same accepted body through the live and
    the candidate hook, and only the candidate accepts urgent."""
    KINDS = ('start', 'step', 'blocker', 'decision', 'done', 'stalled')

    def setUp(self):
        temporary = ROOT / 'tests/.tmp'
        temporary.mkdir(exist_ok=True)
        import tempfile
        self.temp = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def milestone(self, hook, kind):
        import subprocess
        import sys
        root = self.directory / ('%s-%s' % (hook.split('-')[0], kind))
        (root / 'lane').mkdir(parents=True)
        (root / 'bindings.json').write_text('[]\n')
        (root / 'bindings.json').chmod(0o600)
        env = {k: v for k, v in os.environ.items() if not k.startswith('SATS_')}
        env.update(WATCHDOG_TEST_ROOT=str(root), WATCHDOG_TEST_HOOK=hook, WATCHDOG_TEST_RUN_ID=UUID,
                   WATCHDOG_TEST_STATUS='200', PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, str(ROOT / 'tests/inert_hook.py'), 'milestone', '--lane', 't3-fd-0123abcd',
                                 '--lanedir', str(root / 'lane'), '--run', 'generation-1', '--kind', kind,
                                 '--message', 'T3 fd t1 %s generation 1: fixture' % kind.upper(), '--path', '/x/RESULT.md',
                                 '--recipient', 'Sats', '--occurrence', 'generation-1-' + kind.upper(), '--owner-thread-id', 't1'],
                                env=env, capture_output=True, text=True, timeout=60)
        posts = root / 'posts.jsonl'
        bodies = [json.loads(line) for line in posts.read_text().splitlines()] if posts.exists() else []
        for body in bodies:
            body.pop('ts_ct')
        return result, json.loads(json.dumps(bodies).replace(str(root), 'ROOT'))

    def test_existing_kinds_post_the_same_body_through_both_hooks(self):
        for kind in self.KINDS:
            with self.subTest(kind=kind):
                live, live_bodies = self.milestone(LIVE_HOOK, kind)
                candidate, candidate_bodies = self.milestone(CANDIDATE_HOOK, kind)
                self.assertEqual((live.returncode, candidate.returncode), (0, 0))
                self.assertEqual(json.loads(live.stdout)['state'], 'WEBHOOK_ACCEPTED')
                self.assertEqual(json.loads(candidate.stdout)['state'], 'WEBHOOK_ACCEPTED')
                self.assertEqual(len(live_bodies), 1)
                self.assertEqual(candidate_bodies, live_bodies)
                self.assertEqual(live_bodies[0]['event_kind'], kind)

    def test_only_the_candidate_accepts_urgent(self):
        live, live_bodies = self.milestone(LIVE_HOOK, 'urgent')
        self.assertEqual((live.returncode, live.stdout, live_bodies), (2, '', []))  # argparse rejects the kind
        self.assertIn("invalid choice: 'urgent'", live.stderr)
        candidate, bodies = self.milestone(CANDIDATE_HOOK, 'urgent')
        self.assertEqual(candidate.returncode, 0)
        self.assertEqual(json.loads(candidate.stdout)['state'], 'WEBHOOK_ACCEPTED')
        self.assertEqual([(b['event_kind'], b['outcome'], b['reason'], b['notice_occurrence']) for b in bodies],
                         [('urgent', 'URGENT', 'urgent', 'generation-1-URGENT')])


class StallTests(unittest.TestCase):
    """A stall or delivery replan of any owner is recorded locally: the hook is never invoked."""

    def setUp(self):
        temporary = ROOT / 'tests/.tmp'
        temporary.mkdir(exist_ok=True)
        import tempfile
        self.temp = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.record = self.directory / 'hook-called'
        hook = self.directory / 'hook'
        hook.write_text('#!/usr/bin/env python3\nopen(%r, "a").write("called\\n")\nprint("{}")\n' % str(self.record))
        hook.chmod(0o700)
        self.state = watchdog.State(self.directory / 'state')
        self.addCleanup(self.state.close)
        self.events = []
        self.engine = watchdog.Watchdog(self.state, lambda action, **facts: self.events.append(dict(facts, action=action)))
        self.transport = watchdog.Transport({'hook_cli': str(hook)}, self.directory / 'state', {})

    def at(self, delta):
        return {'wall': 1800000000.0 + delta, 'mono': 1000.0 + delta, 'boot': 'public-fixture-boot'}

    def test_t3_and_lane_stalls_and_replans_stay_local_for_every_owner(self):
        pack = self.directory / 'pack'
        pack.mkdir()
        def rows(delta):
            wall = self.at(delta)['wall']
            lane = {'kind': 'lane', 'host': 'fd', 'source': 'registry', 'run': 'run-v1', 'lanedir': str(pack),
                    'known': True, 'eligible': True, 'observed_at': wall, 'milestone_at': None, 'milestone_token': None,
                    'log': {'bytes': 1, 'mtime': self.at(0)['wall'], 'inode': 1}}
            t3 = {'key': 't3:fd:thread', 'kind': 't3', 'host': 'fd', 'thread_id': 'thread', 'project_id': 'p1', 'run': 'run-1',
                  'known': True, 'eligible': True, 'observed_at': wall, 'activity': [], 'thread_updated_at': self.at(0)['wall']}
            return [dict(lane, key='lane:fd:sats', lane='sats', recipient='Sats'),
                    dict(lane, key='lane:fd:lightning', lane='lightning', recipient='Lightning'), t3]
        counts = [self.engine.tick(rows(delta), self.transport, now=self.at(delta)) for delta in (0, 900, 901, 902, 1900)]
        self.assertEqual(counts, [0, 0, 3, 0, 0])
        self.assertFalse(self.record.exists())
        attempts = [e for e in self.events if e['action'] == 'wake-attempt']
        self.assertEqual({(e['transport'], e['reason'], e['accepted']) for e in attempts}, {('local', 'local-only', False)})
        plan = {'kind': 'lane', 'required_action': 'revised_plan_or_replace', 'key': 'delivery:x', 'request_id': 'r'}
        self.assertEqual(self.transport(plan)['reason'], 'local-only')
        self.assertFalse(self.record.exists())


class FirstRunTests(Generations):
    """State the installed round-5 watchdog wrote (tests/preimage/r5, 8144383d) is baselined on the first open:
    nothing in it sends START or a terminal event, an open blocker stays that generation's one BLOCKED, and only
    what happens after the upgrade reaches Sats."""

    def round5(self, client, receipts=None):
        spec = importlib.util.spec_from_file_location('round5_asks', ROOT / 'tests/preimage/r5/sats_stall_asks.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sent = []

        def send(plan):
            sent.append(plan['thread_id'])
            receipt = (receipts or {}).get(plan['thread_id'])
            return receipt or {'accepted': True, 'http_status': 200, 'sats_receipt': 'DELIVERED', 'recipient_run_id': UUID}
        state = module.AskState(self.directory)
        try:
            module.tick_host(client, 'fd', state, lambda action, **f: None, send, scope=SCOPE, now=T0 + 3600,
                             evidence_dir=self.directory / 'asks')
        finally:
            state.close()
        return sorted(sent)

    def tables(self):
        connection = self.db()
        try:
            return {table: connection.execute('SELECT * FROM %s ORDER BY 1' % table).fetchall() for table in ('asks', 'threads')}
        finally:
            connection.close()

    def test_round5_state_is_baselined_without_spam(self):
        threads = {
            'ta': thread('ta', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60))),
            'tb': thread('tb', build(('user_message', 'brief', T0), ('assistant_message', 'All done.', T0 + 60)),
                         settled=True, settled_at=T0 + 100),
            'tc': thread('tc', build(('user_message', 'brief', T0), ('assistant_message', 'working', T0 + 60)), status='running'),
            'td': thread('td', build(('user_message', 'brief', T0), ('assistant_message', 'Should I delete them?', T0 + 60))),
            'te': thread('te', build(('user_message', 'brief', T0), ('assistant_message', ASK.replace('t1', 'te'), T0 + 60))),
        }
        client = FakeT3(PROJECTS, threads)
        failed = {'accepted': False, 'http_status': 502, 'reason': 'transport-exception'}
        self.assertEqual(self.round5(client, receipts={'te': failed}), ['ta', 'td', 'te'])
        before = self.tables()
        # First open: additive migration only. Existing rows are byte-identical; every thread has a baseline.
        state = asks.AskState(self.directory)
        try:
            self.assertEqual(sorted(n for n, _ in state.db.execute('SELECT thread, generation FROM generations')),
                             ['fd:ta', 'fd:tb', 'fd:tc', 'fd:td', 'fd:te'])
            self.assertEqual([(e['thread_id'], e['state'], e['status']) for e in state.events('fd:')], [('ta', 'BLOCKED', 'baseline')])
            self.assertEqual(state.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        finally:
            state.close()
        self.assertEqual(self.tables(), before)
        asks.AskState(self.directory).close()  # a second open changes nothing
        self.assertEqual(len(self.generations('ta')), 1)
        # Unchanged threads: nothing. te's pending NEEDS-VICTOR ask is decided once as its baseline BLOCKED.
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.sent_events(), [('te', 'generation-0-BLOCKED', 'blocker')])
        self.assertEqual(self.tick(client, now=T0 + 3700)[0], 0)
        # ta blocks again in a re-wake: its baseline BLOCKED holds. tb settles again with no new work: no DONE.
        self.add(threads['ta'], 'assistant_message', 'Still waiting.\n' + ASK, T0 + 4000, 'run:thread:ta:ordinal:2')
        threads['tb']['meta'].update(settledAt=iso(T0 + 4000), updatedAt=iso(T0 + 4000))
        self.assertEqual(self.tick(client, now=LATER)[0], 0)
        # tc's in-flight work finishes after the upgrade: one DONE, no START. Answers to ta and td are new work.
        self.add(threads['tc'], 'assistant_message', 'DONE. All checks pass.', T0 + 5000, 'run:thread:tc:ordinal:2')
        threads['tc']['meta'].update(status='completed', settled=True, settledAt=iso(T0 + 5100), updatedAt=iso(T0 + 5100))
        self.add(threads['ta'], 'user_message', 'Victor: use the old key', T0 + 5000, 'run:thread:ta:ordinal:3')
        self.add(threads['td'], 'user_message', 'Victor: yes, delete them', T0 + 5000, 'run:thread:td:ordinal:2')
        self.tick(client, now=LATER + 100)
        self.assertEqual(sorted(self.sent_events()[1:]), [('ta', 'generation-1-START', 'start'), ('tc', 'generation-0-DONE', 'done'),
                                                          ('td', 'generation-1-START', 'start')])
        self.assertEqual(self.tick(client, now=LATER + 200)[0], 0)

    def test_thread_created_before_the_upgrade_is_history_when_first_seen(self):
        import time
        asks.AskState(self.directory).close()  # the upgrade: migration time recorded now
        older = thread('to', build(('user_message', 'brief', T0), ('assistant_message', 'All done.', T0 + 60),
                                   ('user_message', 'one more thing', T0 + 70), ('assistant_message', 'Done too.', T0 + 80)),
                       settled=True, settled_at=T0 + 100)
        older['meta']['createdAt'] = iso(T0)  # e.g. a project added to the ask scope after the upgrade
        newer = thread('tn', build(('user_message', 'brief', T0)), status='running')
        newer['meta']['createdAt'] = iso(time.time() + 60)
        client = FakeT3(PROJECTS, {'to': older, 'tn': newer})
        self.assertEqual(self.tick(client)[0], 1)
        self.assertEqual(self.sent_events(), [('tn', 'generation-1-START', 'start')])
        self.assertEqual([(n, g['origin']) for n, g in self.generations('to')], [(0, 'baseline')])


if __name__ == '__main__':
    unittest.main()
