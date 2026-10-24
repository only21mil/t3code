"""Real Watchdog -> Transport caller checks: a stall or delivery replan is recorded locally and never reaches the
hook, whose only transport is the Sats webhook (Victor GO 3:18 PM CT 2026-10-20: Sats hears only START, BLOCKED,
DONE and URGENT)."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import sats_stall_collector as collector
import sats_stall_mcp as mcp


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


WATCHDOG_PATH = Path(os.environ.get('WATCHDOG_SOURCE', ROOT / 'src/sats_stall_watchdog.py'))
watchdog = load(WATCHDOG_PATH, 'watchdog_under_test')


def at(delta):
    return {'wall': 1800000000.0 + delta, 'mono': 1000.0 + delta, 'boot': 'public-fixture-boot'}


class CallerTests(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / 'tests/.tmp'
        temporary.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.pack = self.directory / 'public-lane'
        self.pack.mkdir()
        (self.pack / 'lane.log').write_text('public fixture is deliberately quiet\n')
        self.registry = self.directory / 'bindings.json'
        self.registry.write_text('[]\n')
        self.registry.chmod(0o600)
        self.env = {'WATCHDOG_TEST_ROOT': str(self.directory), 'WATCHDOG_TEST_STATUS': '200',
                    'PYTHONDONTWRITEBYTECODE': '1', 'SATS_NOTICE_BINDING': 'unrelated-parent-binding',
                    'SATS_TEST': '1', 'SATS_STEP': 'unrelated-parent-step'}
        env_patch = patch.dict(os.environ, self.env)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.state_dir = self.directory / 'watchdog-state'
        self.state = watchdog.State(self.state_dir)
        self.addCleanup(lambda: self.state.close())
        self.events = []
        self.engine = watchdog.Watchdog(self.state, lambda action, **facts: self.events.append(dict(action=action, **facts)))
        self.transport = watchdog.Transport({'hook_cli': str(ROOT / 'tests/inert_hook.py')}, self.state_dir, {})
        self.owner = 'Sats'

    def observation(self, delta, **changes):
        row = {'key': 'lane:fd:public-fixture', 'kind': 'lane', 'host': 'fd', 'source': 'registry',
               'lane': 'public-fixture', 'run': 'public-fixture-run-v1', 'recipient': self.owner,
               'lanedir': str(self.pack), 'known': True, 'eligible': True, 'observed_at': at(delta)['wall'],
               'milestone_at': None, 'milestone_token': None,
               'log': {'bytes': 36, 'mtime': at(0)['wall'], 'inode': 123}}
        return dict(row, **changes)

    def tick(self, delta, **changes):
        return self.engine.tick([self.observation(delta, **changes)], self.transport, now=at(delta))

    def posts(self):
        path = self.directory / 'posts.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def fire(self):
        self.assertEqual([self.tick(delta) for delta in (0, 900, 901)], [0, 0, 1])
        self.assertEqual(self.posts(), [])
        return self.state.get('lane:fd:public-fixture')['reservation']

    def consumer(self):
        # Load the unchanged consumer against its frozen notifier dependency,
        # never whatever root may subsequently install during integration.
        loader = importlib.machinery.SourceFileLoader
        def frozen(name, path):
            if name == 'p5b_notifier':
                path = str(ROOT / 'tests/preimage/sats-completion-notify')
            return loader(name, path)
        with patch('importlib.machinery.SourceFileLoader', side_effect=frozen):
            return load(ROOT / 'tests/preimage/lightning_consumer.py', 'fixture_consumer')

    def test_stall_tldr_and_explicit_priority_relay_at_real_caller(self):
        reservation = self.fire()
        self.assertEqual((reservation['state'], reservation['receipt']['transport'], reservation['receipt']['reason'],
                          reservation['receipt']['accepted']), ('attempted', 'local', 'local-only', False))
        attempt = next(e for e in self.events if e['action'] == 'wake-attempt')
        self.assertEqual((attempt['transport'], attempt['reason']), ('local', 'local-only'))
        self.assertFalse((self.directory / 'hook-state').exists())  # the hook never ran

    def test_strict_boundary_latch_persists_across_restart_and_cooldown(self):
        saved = self.fire()['request_id']
        self.state.close()
        self.state = watchdog.State(self.state_dir)
        self.engine = watchdog.Watchdog(self.state)
        self.assertEqual([self.tick(delta) for delta in (902, 1802, 2703)], [0, 0, 0])
        self.assertEqual(self.posts(), [])
        self.assertEqual(self.state.get('lane:fd:public-fixture')['reservation']['request_id'], saved)
        self.assertEqual(self.state.db.execute('SELECT count(*) FROM wake_receipts').fetchone()[0], 1)

    def test_hook_enrollment_and_consumer_prepare_wake_exact_sats(self):
        self.fire()
        # No hook call, so no enrollment and nothing for the consumer to deliver.
        self.assertEqual(json.loads(self.registry.read_text()), [])
        self.assertFalse(self.registry.with_name('bindings.json.enrollment.jsonl').exists())
        self.assertEqual(self.consumer().load_bindings(self.registry), {})

    def test_bound_non_sats_owner_is_not_rebound_to_sats(self):
        self.owner = 'Lightning'
        binding = {'lane': 'public-fixture', 'run': 'public-fixture-run-v1', 'recipient': 'Lightning', 'priority': True}
        self.registry.write_text(json.dumps([binding]))
        # A Lightning-owned lane's stall would also ride the Sats webhook, so it stays local too.
        self.assertEqual(self.fire()['receipt']['reason'], 'local-only')
        self.assertEqual(json.loads(self.registry.read_text()), [binding])

    def test_no_stall_self_heartbeat_in_pack_or_collector(self):
        before = {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in self.pack.iterdir()}
        self.fire()
        self.assertEqual({p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in self.pack.iterdir()}, before)
        self.assertFalse((self.pack / 'MILESTONES.log').exists())
        self.assertFalse((self.directory / 'hook-state/stalled.log').exists())
        receipt = self.state.get('lane:fd:public-fixture')['reservation']['receipt']
        self.assertFalse(receipt['accepted'])
        self.assertEqual(receipt['native_delivery'], 'unverified')
        self.assertEqual(receipt['downstream_wake'], 'unverified')

    def test_unknown_delivery_retains_latch(self):
        os.environ['WATCHDOG_TEST_STATUS'] = '503'
        self.assertEqual([self.tick(delta) for delta in (0, 900, 901, 902, 1802, 2703)], [0, 0, 1, 0, 0, 0])
        self.assertEqual(self.posts(), [])  # one local record per episode, never a hook attempt
        receipt = self.state.get('lane:fd:public-fixture')['reservation']['receipt']
        self.assertFalse(receipt['accepted'])
        self.assertEqual(receipt['native_delivery'], 'unverified')

    def test_real_hook_retry_preserves_immutable_occurrence(self):
        saved = self.fire()['request_id']
        receipt = self.transport(dict(self.observation(902), request_id=saved))
        self.assertEqual((receipt['accepted'], receipt['reason']), (False, 'local-only'))
        self.assertEqual(self.posts(), [])

    def test_real_progress_rearms_a_new_stall_episode(self):
        self.fire()
        log = {'bytes': 37, 'mtime': at(902)['wall'], 'inode': 123}
        self.assertEqual(self.tick(902, log=log), 0)
        self.assertEqual(self.tick(1802, log=log), 0)
        self.assertEqual(self.tick(1803, log=log), 1)
        self.assertEqual(self.state.db.execute('SELECT count(DISTINCT request_id) FROM wake_receipts').fetchone()[0], 2)
        self.assertEqual(self.posts(), [])

    def test_real_collector_excludes_terminal_pending_approval_and_child(self):
        def register(**changes):
            row = {'lane': 'public-fixture', 'lanedir': str(self.pack), 'run': 'public-fixture-run-v1',
                   'recipient': 'Sats', 'status': 'active', 'unit': None, 'started_at': at(0)['wall']}
            (self.pack / 'LANE.json').write_text(json.dumps(dict(row, **changes)))
        config = {'roots': [str(self.pack)], 'systemd': False, 'native_sessions': []}
        register()
        self.assertEqual(len(collector.discover(config)['lanes']), 1)
        for change in ({'status': 'terminal'}, {'status': 'done'}, {'status': 'blocked'},
                       {'pending_approval': True}, {'parent': 'public-root'}):
            with self.subTest(change=change):
                register(**change)
                self.assertEqual(collector.discover(config)['lanes'], [])
        self.assertEqual(self.posts(), [])

    def test_terminal_milestone_excludes_stale_active_registration(self):
        (self.pack / 'LANE.json').write_text(json.dumps({'lane': 'public-fixture', 'lanedir': str(self.pack),
            'run': 'public-fixture-run-v1', 'recipient': 'Sats', 'status': 'active'}))
        (self.pack / 'MILESTONES.log').write_text(json.dumps({'kind': 'done', 'at': at(0)['wall'], 'run': 'public-fixture-run-v1'}) + '\n')
        self.assertEqual(collector.discover({'roots': [str(self.pack)], 'systemd': False, 'native_sessions': []})['lanes'], [])

    def test_t3_preflight_excludes_terminal_approval_and_wrong_run(self):
        class Client:
            calls = 0
            def __init__(self, thread):
                self.thread = thread
            def call(self, *args):
                return {'thread': self.thread}
        thread = {'threadId': 'public-thread', 'projectId': 'public-project', 'status': 'running',
                  'parentThreadId': None, 'pendingRequestCount': 0, 'activeRunId': 'public-fixture-run-v1'}
        plan = dict(self.observation(901), kind='t3', thread_id='public-thread', project_id='public-project', request_id='public-request')
        for change in ({'status': 'done'}, {'pendingApproval': True}, {'pendingRequestCount': 1},
                       {'parentThreadId': 'public-parent'}, {'activeRunId': 'different-run'}):
            transport = watchdog.Transport({'hook_cli': str(ROOT / 'tests/inert_hook.py')}, self.state_dir, {'fd': Client(dict(thread, **change))})
            with self.subTest(change=change), patch.object(watchdog, 't3_scope', return_value={}), patch.object(mcp, 'scope_allowed', return_value=True):
                result = transport(plan)  # a T3 stall stays local whatever the thread's state: no preflight read
                self.assertEqual(result['reason'], 'local-only')
                self.assertFalse(result['accepted'])
        self.assertEqual(self.posts(), [])

    def test_shared_host_private_scope_is_not_widened(self):
        # No transcript/native scan can happen without an explicit Sats grant.
        result = collector.discover({'roots': [str(self.pack)], 'systemd': False,
            'public_metadata_only': True, 'allowed_recipients': ['Family']})
        self.assertEqual(result['lanes'], [])
        self.assertEqual(result['gaps'], [{'reason': 'positive-victor-scope-required'}])


class FixtureIntegrityTests(unittest.TestCase):
    def test_all_preimages_and_unchanged_dependencies_match_manifest(self):
        for record in json.loads((ROOT / 'tests/INPUTS.json').read_text()):
            path = ROOT / record['frozen_path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record['sha256'], str(path))


if __name__ == '__main__':
    unittest.main()
