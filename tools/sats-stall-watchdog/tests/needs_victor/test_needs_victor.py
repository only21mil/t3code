"""NEEDS-VICTOR miss fixture matrix, adapted from evidence-needs-victor.md's read-only replay.

Usage: python3 -B -I test_needs_victor.py <path to sats_stall_asks.py>

In-memory AskState, in-memory MCP fixture, captured transport, no evidence writes, no hook, no network.
Inputs: fixture-run29.json (the stored run-29 report, sha256 3f9fd433...) and deps/ (installed F-D
sats_stall_mcp.py and sats_stall_collector.py). Prints one PASS or FAIL line per case; exit 1 on any FAIL.

Copied into notice-package-20261023 (repair round 2) from the blocked-threads-rca-20261023 lane on MBP,
needs-victor/test_needs_victor.py sha256 253b1c2f..., which gave cb8a6cc0 19/19. Two changes: deps are this
suite's src/ (the same sats_stall_mcp.py 5b83c242 and sats_stall_collector.py 1a5acf4a), and
restated-ask-sends-nothing-new compares occurrences without the candidate's per-ask suffix ("-ask-<32 hex>"), so a
generation's first BLOCKED reads generation-3-BLOCKED in either module. The unmodified copy gives the candidate
18/19 on that suffix alone.
"""
import datetime
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
spec = importlib.util.spec_from_file_location('sats_stall_asks', sys.argv[1])
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
a.write_evidence = lambda *args: None

fixture = json.loads((HERE / 'fixture-run29.json').read_text())
TID = 'mcp:5a44357c-47a0-4250-a7fc-d5b9a1bb9738'
PID = 'mcp:cfc2be8a-d10d-41c7-8718-a85e64dbf39f'
RUN = 'run:thread:mcp%3A5a44357c-47a0-4250-a7fc-d5b9a1bb9738:ordinal:'
NOW = datetime.datetime(2026, 10, 24, 2, 51, tzinfo=datetime.timezone.utc).timestamp()

report = dict(fixture['assistant_run29'], position=1138, itemId=fixture['assistant_run29']['id'])
native = fixture['native_completion']
# The projection row of the 21:47:42 delegated completion, as the evidence replay fed it.
completion_projection = {'type': 'user_message', 'status': 'completed', 'position': 1139, 'itemId': native['id'],
                         'messageId': native['id'], 'runId': native['runId'], 'updatedAt': native['updatedAt'],
                         'createdBy': native['createdBy'], 'creationSource': native['creationSource'],
                         'delegatedCompletion': native['delegatedCompletion']}
# The MCP timeline shape (OrchestratorMcpService item: createdBy/creationSource, no delegatedCompletion), e.g. a wake.
server_wake = {k: v for k, v in completion_projection.items() if k != 'delegatedCompletion'}


def user_reply(position, created_by, source, run_ordinal=31):
    message_id = 'message:fixture-reply-%d' % position
    return {'type': 'user_message', 'status': 'completed', 'position': position, 'itemId': message_id,
            'messageId': message_id, 'runId': RUN + str(run_ordinal), 'updatedAt': '2026-10-24T03:32:02.570Z',
            'createdBy': created_by, 'creationSource': source}


def second_report(position=1157, ordinal=30, restated=False):
    """A later turn report: a distinct ask (T09), or a restatement of run 29's T01 line."""
    message_id = 'message:fixture-run%d-report' % ordinal
    line = ('T01 route pick /home/victor/work/t3-upstream-standing-20261023/section-a/prep/T01/ROUTE-separate-issue-v2.md'
            if restated else 'T09 merge order /home/victor/work/t3-upstream-standing-20261023/section-a/prep/T09/ORDER.md')
    text = 'Turn report.\n\n- NEEDS-VICTOR %s %s\n' % (TID, line)
    return {'type': 'assistant_message', 'status': 'completed', 'position': position, 'itemId': message_id,
            'messageId': message_id, 'runId': RUN + str(ordinal), 'updatedAt': '2026-10-24T02:50:16.710Z',
            'text': text, 'textTruncated': False}


class Capture:
    def __init__(self):
        self.plans = []

    def thread_notice(self, ask, kinds=None):
        return None

    def __call__(self, plan):
        self.plans.append(plan)
        return {'accepted': True, 'http_status': 200}


class Fixture:
    def __init__(self, meta, items):
        self.meta, self.items = meta, items

    def initialize(self):
        pass

    def call(self, name, args):
        if name == 't3_project_list':
            return {'projects': [{'id': PID, 'workspaceRoot': '/home/victor/work/t3-upstream-standing-20261023'}]}
        if name == 't3_thread_list':
            return {'threads': [self.meta]}
        assert name == 't3_thread_read' and args['threadId'] == TID
        after = args.get('afterPosition', -1)
        return {'thread': self.meta, 'items': [i for i in self.items if i['position'] > after], 'hasMore': False}


def meta(status, active, updated='2026-10-24T02:47:31.988Z', count=1139):
    return {'threadId': TID, 'projectId': PID, 'title': '[grokbot] T3 Code Nightly Upstream PRs',
            'createdAt': '2026-10-24T00:34:24.260Z', 'updatedAt': updated, 'status': status,
            'activeRunId': active, 'latestRunId': active or RUN + '29', 'settled': False, 'settledAt': None,
            'archived': False, 'parentThreadId': None, 'itemCount': count}


def fresh_state(prior_blocked=False):
    s = a.AskState()
    s.db.execute('update migrations set at=0')
    s.db.commit()
    with s.transaction():
        s.put_generation('fd:' + TID, 3, {'host': 'fd', 'thread_id': TID, 'origin': 'message:dd405df6-e8d3-4e90-ad43-c8ec11c4cc83',
                                           'position': 734, 'at': 1792806675.317, 'last_assistant': 794,
                                           'last_assistant_at': 1792807108.289, 'last_marked': False})
        s.claim(a.event('fd', TID, 3, 'START', 734, 1792806675.317, status='sent'))
        if prior_blocked:
            # A generation-3 BLOCKED already sent for an earlier report of this standing generation.
            s.claim(a.event('fd', TID, 3, 'BLOCKED', 1100, 1792809000, status='sent'))
    return s


def tick(state, m, items, send, now=NOW, **limits):
    rows = []
    a.tick_host(Fixture(m, items), 'fd', state, lambda action, **v: rows.append(dict(action=action, **v)),
                send, {'ids': [PID]}, now, evidence_dir='/not-written', **limits)
    return rows


def blockers(send):
    return [p for p in send.plans if p['kind'] == 'blocker']


results = []


def check(label, ok, detail):
    results.append(ok)
    print('%s %s %s' % ('PASS' if ok else 'FAIL', label, detail))


def run_case(label, status, active, items, prior_blocked=False):
    s, send = fresh_state(prior_blocked), Capture()
    tick(s, meta(status, active), items, send)
    asks = [(v.get('generation'), v.get('state'), v.get('event')) for _, v in s.rows('asks', 'ask-')]
    found = blockers(send)
    return s, send, found, asks


# 1. own-run-active still defers.
s, send, found, asks = run_case('own-run-active', 'running', RUN + '29', [report])
check('own-run-active', not found and asks == [(3, 'pending', 'BLOCKED')], 'blocker_sent=%s asks=%s' % (bool(found), asks))
s.close()

# 2-4. the evidence lane's positive controls still reach notice.
for label, status, active in [('later-run-active', 'running', RUN + '30'), ('completed-unsettled', 'completed', None),
                              ('idle-unsettled', 'idle', None)]:
    s, send, found, asks = run_case(label, status, active, [report])
    check(label, len(found) == 1, 'occurrences=%s' % [p['occurrence'] for p in found])
    s.close()

# 5. catchup-native-completion: the run-29 report followed by the 21:47:42 delegated completion reaches notice.
for label, follower in [('catchup-native-completion', completion_projection), ('catchup-server-wake-mcp-shape', server_wake)]:
    s, send, found, asks = run_case(label, 'running', RUN + '30', [report, follower])
    check(label, len(found) == 1 and asks == [(3, 'bound', 'BLOCKED')],
          'blocker_sent=%s asks=%s occurrences=%s' % (bool(found), asks, [p['occurrence'] for p in found]))
    s.close()

# 6. a second distinct report in the same generation after a sent BLOCKED reaches notice with its own occurrence.
s, send, found, asks = run_case('later-run-already-blocked', 'running', RUN + '30', [report], prior_blocked=True)
check('later-run-already-blocked', len(found) == 1 and found[0]['occurrence'] != 'generation-3-BLOCKED',
      'occurrences=%s' % [p['occurrence'] for p in found])
s.close()

s, send = fresh_state(), Capture()
tick(s, meta('running', RUN + '30'), [report], send)
first = [p['occurrence'] for p in blockers(send)]
later = meta('running', RUN + '31', updated='2026-10-24T02:55:00.000Z', count=1158)
tick(s, later, [report, second_report()], send, now=NOW + 300)
both = [p['occurrence'] for p in blockers(send)]
check('second-report-same-generation', len(first) == 1 and len(both) == 2 and both[0] != both[1],
      'occurrences=%s' % both)
# A later turn that restates run 29's T01 ask (r5 re-wake rule) sends nothing new.
s2, send2 = fresh_state(), Capture()
tick(s2, meta('running', RUN + '30'), [report], send2)
tick(s2, later, [report, second_report(restated=True)], send2, now=NOW + 300)
restated = [re.sub(r'-ask-[0-9a-f]{32}$', '', p['occurrence']) for p in blockers(send2)]
check('restated-ask-sends-nothing-new', restated == ['generation-3-BLOCKED'], 'occurrences=%s' % restated)
s2.close()
# Idempotency: the same asks read again on later ticks send nothing more.
again = meta('running', RUN + '31', updated='2026-10-24T03:00:00.000Z', count=1159)
tick(s, again, [report, second_report()], send, now=NOW + 600)
s.db.execute("update threads set data=json_set(data, '$.position', 1100)")  # force a reread of both reports
s.db.commit()
tick(s, dict(again, updatedAt='2026-10-24T03:05:00.000Z'), [report, second_report()], send, now=NOW + 900)
check('same-ask-never-twice', [p['occurrence'] for p in blockers(send)] == both,
      'sends=%d' % len(blockers(send)))
s.close()

# 7. a genuine human answer still closes the ask, read in the same window or reconciled on a later tick.
for label, reply in [('human-answer-web', user_reply(1329, 'user', 'web')),
                     ('sats-relay-mcp (live item 1329 shape)', user_reply(1329, 'agent', 'mcp'))]:
    s, send, found, asks = run_case(label, 'running', RUN + '31', [report, reply])
    check(label, not found and not any(state == 'bound' for _, state, _ in asks), 'blocker_sent=%s asks=%s' % (bool(found), asks))
    s.close()

for label, follower, expect_sent in [('reconcile-pending-then-human', user_reply(1329, 'user', 'web'), False),
                                     ('reconcile-pending-then-server-wake', server_wake, True)]:
    s, send = fresh_state(), Capture()
    tick(s, meta('running', RUN + '29'), [report], send)  # own run active: stored pending
    # itemCount 1140 keeps both items inside the bounded first-read window (after = itemCount - 41).
    tick(s, meta('running', RUN + '31', updated='2026-10-24T03:32:03.000Z', count=1140), [report, follower], send, now=NOW + 300)
    asks = [v.get('state') for _, v in s.rows('asks', 'ask-')]
    check(label, bool(blockers(send)) == expect_sent, 'blocker_sent=%s asks=%s' % (bool(blockers(send)), asks))
    s.close()

# The pre-send reread (thread not read this tick: max_reads=0) for a pending ask (:717) and a claimed event (:775).
for label, follower, expect_sent in [('reread-ask-then-human', user_reply(1329, 'user', 'web'), False),
                                     ('reread-ask-then-server-wake', server_wake, True)]:
    s, send = fresh_state(), Capture()
    tick(s, meta('running', RUN + '29'), [report], send)
    tick(s, meta('running', RUN + '31', updated='2026-10-24T03:32:03.000Z', count=1140), [report, follower], send,
         now=NOW + 300, max_reads=0)
    asks = [v.get('state') for _, v in s.rows('asks', 'ask-')]
    check(label, bool(blockers(send)) == expect_sent, 'blocker_sent=%s asks=%s' % (bool(blockers(send)), asks))
    s.close()
for label, follower, expect_sent in [('reread-event-then-human', user_reply(1329, 'user', 'web'), False),
                                     ('reread-event-then-server-wake', server_wake, True)]:
    s, send = fresh_state(), Capture()
    tick(s, meta('running', RUN + '30'), [report], send, max_notices=0)  # bound and claimed, not sent
    claimed = [e['status'] for e in s.events('fd:' + TID) if e['state'] == 'BLOCKED']
    tick(s, meta('running', RUN + '31', updated='2026-10-24T03:32:03.000Z', count=1140), [report, follower], send,
         now=NOW + 300, max_reads=0)
    events = [e['status'] for e in s.events('fd:' + TID) if e['state'] == 'BLOCKED']
    check(label, claimed == ['pending'] and bool(blockers(send)) == expect_sent,
          'claimed=%s blocker_sent=%s events=%s' % (claimed, bool(blockers(send)), events))
    s.close()

# 8. START is unchanged: one START per new generation origin, generation-level occurrence.
s, send = fresh_state(), Capture()
tick(s, meta('running', RUN + '31'), [report, user_reply(1329, 'user', 'web')], send)
starts = [p['occurrence'] for p in send.plans if p['kind'] == 'start']
check('start-unchanged', starts == ['generation-4-START'], 'starts=%s' % starts)
s.close()

print('MATRIX', 'PASS' if all(results) else 'FAIL', '%d/%d' % (sum(results), len(results)), sys.argv[1].split('/')[-1])
sys.exit(0 if all(results) else 1)
