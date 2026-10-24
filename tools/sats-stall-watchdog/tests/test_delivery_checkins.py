import hashlib
import json
import unittest
from unittest.mock import patch
from pathlib import Path
import test_watchdog_route as fixtures
at, watchdog, collector = fixtures.at, fixtures.watchdog, fixtures.collector


class DeliveryCheckinTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CallerTests("runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.plan = {"revision": 1, "unit": "pilot-existing-path", "owner": "Sats",
                     "pilot": "one deployed end-to-end slice", "set_point": at(100)['wall'], "evidence": []}

    def metadata(self):
        f = self.fixture
        (f.pack / "DELIVERY.json").write_text(json.dumps(self.plan))
        return collector.delivery_metadata(f.pack, [f.directory])

    def tick(self, delta, **changes):
        changes['delivery'] = self.metadata()
        return self.fixture.tick(delta, **changes)

    def test_stale_outcome_forces_replan_despite_continuous_log_growth(self):
        self.assertEqual(self.tick(0), 0)
        self.assertEqual(self.tick(100, log={'bytes': 100, 'inode': 123, 'mtime': at(100)['wall']}), 0)
        self.assertEqual(self.tick(101, log={'bytes': 200, 'inode': 123, 'mtime': at(101)['wall']}), 1)
        # The replan gate is local: the gate file and the log record, never a Sats send.
        self.assertEqual(self.fixture.posts(), [])
        required = next(e for e in self.fixture.events if e['action'] == 'delivery-replan-required')
        self.assertEqual(required['required_action'], 'revised_plan_or_replace')
        gate = json.loads((self.fixture.pack / 'REPLAN-REQUIRED.json').read_text())
        self.assertEqual(gate['required_action'], 'revised_plan_or_replace')
        self.assertEqual(self.tick(200, log={'bytes': 400, 'inode': 123, 'mtime': at(200)['wall']}), 0)
        self.assertEqual(self.fixture.posts(), [])

    def test_gate_survives_restart_and_only_an_accountable_replan_releases_it(self):
        self.tick(0)
        self.assertEqual(self.tick(101), 1)
        f = self.fixture
        f.state.close()
        f.state = watchdog.State(f.state_dir)
        f.engine = watchdog.Watchdog(f.state)
        self.plan.update(set_point=at(1000)['wall'])
        self.assertEqual(self.tick(102), 0)
        self.plan.update(revision=2)
        self.assertEqual(self.tick(103), 0)
        key = watchdog.delivery_key(f.observation(0))
        self.assertTrue(f.state.get(key)['required'])
        self.plan.update(cause='integration dependency missed', revised_path='reuse adapter for the named pilot first')
        self.assertEqual(self.tick(104), 0)
        self.assertFalse(f.state.get(key)['required'])
        self.assertEqual(self.tick(1001), 1)
        self.assertEqual(f.posts(), [])
        self.assertEqual(f.state.db.execute("SELECT count(*) FROM wake_receipts WHERE request_id LIKE 'sats-delivery-%'").fetchone()[0], 2)

    def test_verified_side_effect_counts_and_tampered_proof_fails_closed(self):
        proof = self.fixture.pack / 'pilot-proof.txt'
        proof.write_text('Existing path deployed and smoke check passed.\n')
        self.plan['evidence'] = [{'kind': 'deployed', 'path': str(proof),
            'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()}]
        self.assertEqual(self.tick(101), 0)
        self.assertEqual(self.tick(102), 0)
        self.assertEqual(self.tick(500), 0)
        proof.write_text('Unverified replacement contents.\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.metadata()

    def test_verification_before_set_point_satisfies_the_current_commitment(self):
        proof = self.fixture.pack / 'early-proof.txt'
        proof.write_text('Pilot verified before its forecast.\n')
        self.plan['evidence'] = [{'kind': 'verified', 'path': str(proof),
            'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()}]
        self.assertEqual(self.tick(0), 0)
        self.assertEqual(self.tick(101), 0)
        self.assertEqual(self.tick(500), 0)
        self.assertEqual(self.fixture.posts(), [])

    def test_proof_is_streamed_and_confined_to_its_pack(self):
        proof = self.fixture.pack / 'large-proof.bin'
        with proof.open('wb') as stream:
            stream.seek(8 * 1024 * 1024)
            stream.write(b'fixture')
        with proof.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        self.plan['evidence'] = [{'kind': 'verified', 'path': str(proof), 'sha256': digest}]
        original = Path.read_bytes
        def guarded(path):
            if path == proof:
                raise AssertionError('proof loaded wholesale')
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            self.assertTrue(self.metadata()['effects'])
        outside = self.fixture.directory / 'outside-proof.txt'
        outside.write_text('Public negative control.\n')
        self.plan['evidence'] = [{'kind': 'verified', 'path': str(outside),
            'sha256': hashlib.sha256(outside.read_bytes()).hexdigest()}]
        with self.assertRaisesRegex(ValueError, 'outside scope'):
            self.metadata()

    def test_bad_delivery_data_does_not_hide_a_live_lane(self):
        f = self.fixture
        (f.pack / 'LANE.json').write_text(json.dumps({'lane': 'public-fixture',
            'lanedir': str(f.pack), 'run': 'public-fixture-run-v1', 'recipient': 'Sats',
            'status': 'active', 'unit': None, 'started_at': at(0)['wall']}))
        (f.pack / 'DELIVERY.json').write_text('{malformed')
        result = collector.discover({'roots': [str(f.pack)], 'systemd': False, 'native_sessions': []})
        self.assertEqual(len(result['lanes']), 1)
        self.assertIsNone(result['lanes'][0]['delivery'])
        self.assertIn({'reason': 'delivery-metadata-unavailable'}, result['gaps'])

    def test_t3_activity_cannot_satisfy_delivery_commitment(self):
        f = self.fixture
        captured = []
        def row(delta):
            return {'key': 't3:fd:fixture-owner', 'kind': 't3', 'host': 'fd',
                'thread_id': 'fixture-owner', 'run': 'fixture-run', 'known': True, 'eligible': True,
                'observed_at': at(delta)['wall'], 'activity': [{'id': str(delta), 'at': at(delta)['wall']}],
                'thread_updated_at': at(delta)['wall'], 'delivery': self.metadata(), 'remote': True}
        transport = lambda plan: captured.append(plan) or {'accepted': True}
        self.assertEqual(f.engine.tick([row(0)], transport, at(0)), 0)
        self.assertEqual(f.engine.tick([row(101)], transport, at(101)), 1)
        self.assertEqual(captured[0]['required_action'], 'revised_plan_or_replace')


if __name__ == '__main__':
    unittest.main()
