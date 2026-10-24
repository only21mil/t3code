"""The live suite's end-to-end hook checks through the notice-package-20261023 notifier (preimage/candidate-20261023,
a byte copy of the candidate's notify/sats-completion-notify), and item 6 through the real hook identity: two asks
of one generation are two POSTs with their own occurrence and event id, and a repeated ask is none."""
from pathlib import Path
import unittest

import test_generations as generations
from test_asks import ASK, FakeT3, PROJECTS, T0, build, label, thread

ROOT = generations.ROOT
LATER = generations.LATER
HOOK = 'candidate-20261023/sats-completion-notify'


class InertNoticePackageHook(generations.InertCandidateHook):
    HOOK = HOOK

    def test_two_asks_are_two_hook_notices_and_a_repeat_is_none(self):
        t1 = thread('t1', build(('user_message', 'brief', T0), ('assistant_message', ASK, T0 + 60),
                                ('assistant_message', 'NEEDS-VICTOR t1 also rotate the key /y', T0 + 70)))
        client = FakeT3(PROJECTS, {'t1': t1})
        self.send = self.hook
        self.tick(client)
        self.add(t1, 'assistant_message', 'Still waiting.\n' + ASK, T0 + 400, 'run:thread:t1:ordinal:3')
        self.tick(client, now=LATER)
        blocked = [p for p in self.posts() if p['event_kind'] == 'blocker']
        self.assertEqual(len(blocked), 2)
        self.assertEqual({label(p['notice_occurrence']) for p in blocked}, {'generation-1-BLOCKED'})
        self.assertEqual(len({p['notice_occurrence'] for p in blocked}), 2)
        self.assertEqual(len({p['event_id'] for p in blocked}), 2)
        self.assertEqual(sorted(e['status'] for e in self.events() if e['state'] == 'BLOCKED'), ['sent', 'sent'])


class PreimageSyncTests(unittest.TestCase):
    def test_preimage_is_the_candidate_notifier(self):
        candidate = ROOT.parents[1] / 'notify/sats-completion-notify'
        if not candidate.exists():
            self.skipTest('no candidate notifier beside this tree')
        self.assertEqual((ROOT / 'tests/preimage' / HOOK).read_bytes(), candidate.read_bytes())


if __name__ == '__main__':
    unittest.main()
