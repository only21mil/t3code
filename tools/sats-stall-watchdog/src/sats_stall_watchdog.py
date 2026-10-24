"""One durable local record per proven stall episode, and T3 generation events to Sats, using only stdlib metadata reads."""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import sqlite3
import subprocess
import sys
import time

import sats_stall_asks as asks
import sats_stall_collector as collector
from sats_stall_mcp import MCP, Gap, collect as collect_t3

THRESHOLD = 900
READ_LIMIT = 2_000_000
OPTIONS_LIMIT = 1_000_000
# The config may narrow this set, never widen it or redirect a paired token.
AUTHORIZED_HOSTS = {
    'fd': ({'local'}, 'http://100.94.71.50:3774'),
    'mbp': ({'victors-macbook-pro', 'mbp'}, 'http://100.65.3.65:3774'),
    'yoga': ({'yoga-direct-pow'}, 'http://100.78.114.65:3774'),
    'mini': ({'mac-mini', 'm4mini@100.64.195.11'}, 'http://100.64.195.11:3774'),
    'm3mbp': ({'m3mbp', 'mason@100.122.145.42'}, 'http://100.122.145.42:3774'),
    # Victor GO 17:02 CT 2026-10-18 (t3-decision-delivery-fix): Victor's F13 Pro, account only21mil.
    'f13pro': ({'f13pro', 'victor-f13', 'only21mil-f13pro'}, 'http://100.75.206.109:3774'),
}
SHARED_HOSTS = {'mini', 'm3mbp'}


class PreflightDeferred(dict):
    """Invocation-local proof, never constructible from a hook JSON receipt."""


class NativePreflightDeferred(PreflightDeferred):
    """Retain the native preflight's unavailable-only retry contract."""


def safe_id(value):
    return isinstance(value, str) and 0 < len(value) <= 200 and not any(ord(c) < 32 for c in value)


def clock():
    try:
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        # Unknown reboot identity means persisted elapsed time is never trusted.
        boot = None
    return {'wall': time.time(), 'mono': time.monotonic(), 'boot': boot}


class State:
    """SQLite FULL commit before transport. TRUNCATE retains the journal file.

    The SQL write lock protects reservations across simultaneous timers/CLI
    invocations. An independent delivery lock prevents a delayed older send
    from overlapping a newly observed run of the same owner.
    """
    def __init__(self, directory=None):
        self.directory = Path(directory).expanduser().resolve() if directory else None
        self.cursor_gaps = {}
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(self.directory / 'state.sqlite3') if self.directory else ':memory:', timeout=5)
        self.db.execute('PRAGMA journal_mode=TRUNCATE')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS owners (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS wake_receipts (request_id TEXT PRIMARY KEY, key TEXT NOT NULL, data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS scan_offsets (host TEXT PRIMARY KEY, value INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS discovery_cursors (host TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.commit()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    @contextmanager
    def delivery_lock(self, key):
        if self.directory is None:
            yield True
            return
        path = self.directory / ('owner-' + hashlib.sha256(key.encode()).hexdigest() + '.lock')
        with path.open('a') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def get(self, key):
        row = self.db.execute('SELECT data FROM owners WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO owners VALUES (?,?)', (key, json.dumps(value, separators=(',', ':'), allow_nan=False)))

    def keys(self):
        return [row[0] for row in self.db.execute('SELECT key FROM owners')]

    def receipt(self, request_id, key, value):
        self.db.execute('INSERT OR REPLACE INTO wake_receipts VALUES (?,?,?)', (request_id, key, json.dumps(value, separators=(',', ':'), allow_nan=False)))

    def close(self):
        self.db.close()

    def offsets(self):
        return dict(self.db.execute('SELECT host,value FROM scan_offsets'))

    def discovery_cursor(self, host):
        row = self.db.execute('SELECT CASE WHEN length(CAST(data AS BLOB)) <= ? THEN data ELSE NULL END FROM discovery_cursors WHERE host=?',
                              (collector.CURSOR_LIMIT, host)).fetchone()
        if not row:
            return None
        if row[0] is None:
            value, gaps = None, [{'reason': 'registry-cursor-oversize'}]
        else:
            try:
                value, gaps = collector.checked_cursor(json.loads(row[0]))
            except (ValueError, TypeError):
                value, gaps = None, [{'reason': 'registry-cursor-malformed'}]
        if gaps:
            self.cursor_gaps[host] = gaps
            self.save_discovery_cursor(host, None)
        return value

    def save_discovery_cursor(self, host, value):
        value, gaps = collector.checked_cursor(value)
        with self.transaction():
            if value is None:
                self.db.execute('DELETE FROM discovery_cursors WHERE host=?', (host,))
            else:
                self.db.execute('INSERT OR REPLACE INTO discovery_cursors VALUES (?,?)',
                                (host, json.dumps(value, separators=(',', ':'), allow_nan=False)))
        return gaps

    def save_offsets(self, clients):
        with self.transaction():
            for host, client in clients.items():
                value = getattr(client, 'next_read_offset', None)
                if type(value) is int and value >= 0:
                    self.db.execute('INSERT OR REPLACE INTO scan_offsets VALUES (?,?)', (host, value))


class Events:
    def __init__(self, path=None, stdout=False):
        self.path, self.stdout = Path(path) if path else None, stdout

    def __call__(self, action, **facts):
        # Call sites supply metadata and fixed reason codes only, never errors,
        # message contents, headers, environment, token paths or raw receipts.
        row = dict(at=time.time(), action=action, **facts)
        line = json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n'
        if self.path:
            with self.path.open('a', encoding='utf-8') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
        if self.stdout:
            print(line, end='', flush=True)


def valid_observation(obs, now):
    if not safe_id(obs.get('key')) or not safe_id(obs.get('run')):
        return False
    observed_at = obs.get('observed_at')
    if type(observed_at) not in {float, int} or not math.isfinite(observed_at) or abs(observed_at - now['wall']) > 30:
        return False
    if obs['kind'] == 'lane':
        if not all(safe_id(obs.get(k)) for k in ('lane', 'recipient')):
            return False
        ms = obs.get('milestone_at')
        if ms is not None and (type(ms) not in {float, int} or not math.isfinite(ms) or ms > observed_at + 5):
            return False
        log = obs.get('log')
        if log is not None and (type(log.get('bytes')) is not int or log['bytes'] < 0 or type(log.get('mtime')) not in {float, int} or not math.isfinite(log['mtime']) or log['mtime'] > observed_at + 5):
            return False
        resources = obs.get('resources')
        if resources is not None:
            if (not isinstance(resources, dict) or resources.get('unit') != obs.get('unit') or
                    resources.get('invocation_id') != obs.get('invocation_id') or
                    not collector.INVOCATION_RE.fullmatch(str(resources.get('invocation_id', ''))) or
                    not isinstance(resources.get('counters'), dict)):
                return False
            at = resources.get('observed_at')
            if type(at) not in {int, float} or not math.isfinite(at) or abs(at - now['wall']) > 30:
                return False
            for key in collector.RESOURCE_COUNTERS:
                value = resources['counters'].get(key)
                if value is not None and (type(value) is not int or not 0 <= value < 2**64 - 1):
                    return False
        native = obs.get('native_resources')
        if native is not None:
            if (obs.get('source') != 'native' or not isinstance(native, dict) or
                    native.get('generation') != obs.get('native_generation') or
                    not re.fullmatch(r'[0-9a-f]{16}', str(native.get('generation', ''))) or
                    not isinstance(native.get('counters'), dict)):
                return False
            at, value = native.get('observed_at'), native['counters'].get('cpu_ticks')
            if (type(at) not in {int, float} or not math.isfinite(at) or abs(at - now['wall']) > 30 or
                    type(value) is not int or not 0 <= value < 2**64 - 1):
                return False
    return True


def evidence(obs):
    if obs['kind'] == 'lane':
        return {k: obs.get(k) for k in ('milestone_at', 'milestone_token', 'milestone_mtime', 'log', 'resources', 'native_resources')}
    return {'activity': obs.get('activity', []), 'thread_updated_at': obs.get('thread_updated_at')}


def progress(old, obs):
    previous, current = old['evidence'], evidence(obs)
    if obs['kind'] == 'lane':
        p, c = previous.get('log'), current.get('log')
        # Rotation/truncation loses continuity; it cannot prove productive work.
        uncertain = bool(p is not None and (c is None or p.get('inode') != c.get('inode') or c['bytes'] < p['bytes']))
        growth = p is not None and c is not None and p.get('inode') == c.get('inode') and c['bytes'] > p['bytes']
        ms = current.get('milestone_at')
        old_ms = previous.get('milestone_at')
        milestone = ms is not None and current.get('milestone_token') != previous.get('milestone_token') and (old_ms is None or ms > old_ms)
        # A disappearing evidence file also restarts the conservative baseline.
        uncertain |= previous.get('milestone_token') is not None and current.get('milestone_token') is None
        p, c = previous.get('resources'), current.get('resources')
        resource_growth, resource_gap, resource_reset = False, False, False
        if p is not None or c is not None:
            if p is None or c is None or any(p.get(k) != c.get(k) for k in ('unit', 'invocation_id')):
                resource_gap = True
                resource_reset = True
            else:
                for key in collector.RESOURCE_COUNTERS:
                    prior, value = p['counters'].get(key), c['counters'].get(key)
                    if prior is None and value is None:
                        continue
                    if prior is None or value is None:
                        resource_gap = True
                    elif value < prior:
                        resource_gap = resource_reset = True
                    elif value > prior:
                        resource_growth = True
        # A reset cannot clear a prior wake reservation. An optional counter
        # becoming unavailable does not negate another counter's proven work.
        p, c = previous.get('native_resources'), current.get('native_resources')
        native_growth, native_gap = False, False
        if p is not None or c is not None:
            if p is None or c is None or p.get('generation') != c.get('generation'):
                native_gap = True
            else:
                prior, value = p['counters']['cpu_ticks'], c['counters']['cpu_ticks']
                native_growth, native_gap = value > prior, value < prior
        return bool(growth or milestone or (resource_growth and not resource_reset) or native_growth), bool(uncertain or resource_gap or native_gap)
    prior = {x['id']: x for x in previous.get('activity', [])}
    changed = [x for x in current.get('activity', []) if x['id'] not in prior or x['at'] > prior[x['id']]['at']]
    # Pending wake metadata and request/user events are excluded by the adapter.
    # Genuine assistant/tool activity after reservation is allowed to rearm.
    reservation = old.get('reservation')
    cutoff = reservation['at'] if reservation else -1
    return any(x['at'] > cutoff for x in changed), False


def baseline(obs, now, episode=0, reservation=None, not_before=0):
    return {'run': obs['run'], 'episode': episode, 'quiet_since': now['mono'],
            'last_clock': now, 'continuous': True, 'evidence': evidence(obs),
            'reservation': reservation, 'not_before': not_before}


def uninterrupted(old, now):
    last = old['last_clock']
    if now.get('boot') is None or last.get('boot') != now['boot'] or now['mono'] < last['mono'] or now['wall'] < last['wall']:
        return False
    return abs((now['wall'] - last['wall']) - (now['mono'] - last['mono'])) <= 5


def delivery_key(obs):
    return 'delivery:' + hashlib.sha256((obs['key'] + '|' + str(obs.get('lanedir', ''))).encode()).hexdigest()


def persist_delivery_gate(obs, gate):
    if obs.get('lanedir') and not obs.get('remote'):
        directory = Path(obs['lanedir'])
        target = directory / 'REPLAN-REQUIRED.json'
        temporary = directory / ('.REPLAN-REQUIRED.' + str(os.getpid()) + '.' + str(time.time_ns()))
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps(gate) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        fd_directory = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd_directory)
        finally:
            os.close(fd_directory)


class Watchdog:
    def __init__(self, state, emit=None, threshold=THRESHOLD, cooldown=THRESHOLD):
        if any(type(value) not in {int, float} or not math.isfinite(value) or value < THRESHOLD for value in (threshold, cooldown)):
            raise ValueError('stall and cooldown floors are 900 seconds')
        self.state, self.emit = state, emit or (lambda *a, **k: None)
        self.threshold, self.cooldown = threshold, cooldown

    def delivery_check(self, obs, now):
        """An overdue outcome is independent of ordinary liveness evidence."""
        plan = obs.get('delivery')
        if not plan:
            return None
        key = delivery_key(obs)
        with self.state.transaction():
            old = self.state.get(key)
            effects = plan['effects']
            revised = old and plan['revision'] > old['revision']
            if revised and old.get('required') and not (plan.get('cause') and plan.get('revised_path') and plan['set_point'] > now['wall']):
                revised = False
            if old is None or revised:
                prior_effects = old['effects'] if old else []
                old = {'run': obs['run'], 'revision': plan['revision'], 'effects': prior_effects,
                       'set_point': plan['set_point'], 'required': False,
                       'reservation': None, 'episode': 0, 'continuous': True}
            advanced = bool(set(effects) - set(old['effects']))
            old['satisfied'] = old.get('satisfied', False) or advanced
            old['effects'] = effects
            if old.get('required'):
                self.state.put(key, old)
                persist_delivery_gate(obs, {'state': 'REPLAN_REQUIRED', 'revision': old['revision'],
                    'required_action': 'revised_plan_or_replace', 'request_id': old['reservation']['request_id']})
                return None
            if now['wall'] <= old['set_point'] or old['satisfied']:
                old['last_result'] = 'VERIFIED' if old['satisfied'] else 'BEFORE_SET_POINT'
                self.state.put(key, old)
                self.emit('delivery-check', key=key, state=old['last_result'])
                return None
            request_id = 'sats-delivery-' + hashlib.sha256(
                (key + '|' + obs['run'] + '|' + str(old['revision'])).encode()).hexdigest()[:40]
            old.update(required=True, reservation={'request_id': request_id, 'at': now['wall'],
                'run': obs['run'], 'state': 'reserved', 'receipt': None})
            self.state.put(key, old)
            self.state.receipt(request_id, key, old['reservation'])
        gate = {'state': 'REPLAN_REQUIRED', 'revision': old['revision'],
                'required_action': 'revised_plan_or_replace', 'request_id': request_id}
        persist_delivery_gate(obs, gate)
        self.emit('delivery-replan-required', key=key, **gate)
        return dict(obs, key=key, request_id=request_id, event_kind='decision',
                    required_action='revised_plan_or_replace', quiet_seconds=0)

    def consider(self, obs, now):
        key = obs['key']
        if obs.get('known') and obs.get('eligible') and valid_observation(obs, now):
            delivery = self.delivery_check(obs, now)
            if delivery is not None:
                return delivery
            pending = self.state.get(delivery_key(obs))
            if pending and pending.get('required'):
                return None
        with self.state.transaction():
            old = self.state.get(key)
            if not obs.get('known', False) or not obs.get('eligible', False) or not valid_observation(obs, now):
                if old:
                    old['continuous'] = False
                    self.state.put(key, old)
                self.emit('defer', key=key, reason='unknown-ineligible-or-clock')
                return None
            if old is None:
                self.state.put(key, baseline(obs, now))
                self.emit('baseline', key=key, reason='cold-full-window')
                return None
            # A send may queue/start a new run of its own. A run change after
            # reservation needs independent activity or a known distinct runId
            # not returned by our wake. Ambiguous new runs retain the wake latch.
            genuine, uncertain = progress(old, obs)
            changed_run = obs['run'] != old['run']
            reservation = old.get('reservation')
            receipt_run = (reservation.get('receipt') or {}).get('run_id') if reservation else None
            own_run = reservation and receipt_run == obs['run']
            new_run = changed_run and (obs['kind'] == 'lane' or not reservation or (not own_run and (genuine or receipt_run is not None)))
            if new_run or genuine:
                not_before = old.get('not_before', 0)
                new = baseline(obs, now, old['episode'] + 1, not_before=not_before)
                self.state.put(key, new)
                self.emit('rearm', key=key, reason='new-run' if new_run else 'independent-progress')
                return None
            if uncertain or not old.get('continuous') or not uninterrupted(old, now):
                old = baseline(obs, now, old['episode'], reservation, old.get('not_before', 0))
                self.state.put(key, old)
                self.emit('baseline', key=key, reason='evidence-or-clock-gap')
                return None
            old['last_clock'], old['evidence'] = now, evidence(obs)
            age = now['mono'] - old['quiet_since']
            if reservation:
                self.state.put(key, old)
                self.emit('suppressed', key=key, reason='episode-already-reserved')
                return None
            if age <= self.threshold or now['wall'] < old.get('not_before', 0):
                self.state.put(key, old)
                self.emit('observed', key=key, quiet_seconds=round(age, 3))
                return None
            identity = '%s|%s|%s|%.6f|%s' % (key, old['run'], old['episode'], old['quiet_since'], now['boot'])
            request_id = 'sats-stall-' + hashlib.sha256(identity.encode()).hexdigest()[:40]
            reservation = {'request_id': request_id, 'at': now['wall'], 'run': old['run'], 'state': 'reserved', 'receipt': None}
            old['reservation'] = reservation
            old['not_before'] = now['wall'] + self.cooldown
            self.state.put(key, old)
            self.state.receipt(request_id, key, reservation)
        # This point is after durable COMMIT, including when transport crashes.
        self.emit('reserved', key=key, request_id=request_id, quiet_seconds=round(age, 3))
        return dict(obs, request_id=request_id, quiet_seconds=age)

    def tick(self, observations, transport, now=None):
        seen, count = set(), 0
        for obs in observations:
            key = obs.get('key')
            if not safe_id(key) or key in seen:
                self.emit('gap', reason='owner-identity-duplicate-or-invalid')
                continue
            seen.add(key)
            with self.state.delivery_lock(key) as acquired:
                if not acquired:
                    self.emit('defer', key=key, reason='owner-delivery-in-flight')
                    continue
                # Explicit injected clocks retain their test/API contract.
                # Collected rows carry the local clock at their own arrival,
                # unaffected by a later slow host or another owner's delivery.
                evaluated = now if now is not None else obs.get('_arrival_clock') or clock()
                plan = self.consider(obs, evaluated)
                if plan is None:
                    continue
                count += 1
                try:
                    receipt = transport(plan)
                except Exception:
                    receipt = {'transport': 'unknown', 'http_status': None, 'accepted': False, 'native_delivery': 'unverified', 'reason': 'transport-exception'}
                # Whitelist receipts even from hook CLI responses.
                clean = clean_receipt(receipt)
                retry = (isinstance(receipt, PreflightDeferred) and not clean['accepted'] and
                         ((plan['kind'] == 't3' and clean.get('reason') in {'owner-state-changed', 'mcp-send-error'}) or
                          (isinstance(receipt, NativePreflightDeferred) and plan.get('source') == 'native' and
                           clean.get('reason') == 'native-preflight-unavailable')))
                if retry:
                    clean['not_sent'] = True
                with self.state.transaction():
                    old = self.state.get(plan['key'])
                    reservation = old['reservation']
                    if reservation and reservation['request_id'] == plan['request_id']:
                        reservation.update(state='not-sent' if retry else 'attempted', receipt=clean)
                        if retry:
                            # Only an invocation-local preflight marker proves
                            # no hook was invoked. Preserve run/episode/quiet
                            # identity for the next still-stalled tick. Unknown
                            # send outcomes retain the latch.
                            old['reservation'] = None
                            old['not_before'] = evaluated['wall']
                            if plan['key'].startswith('delivery:'):
                                old['required'] = False
                        self.state.put(plan['key'], old)
                        self.state.receipt(plan['request_id'], plan['key'], reservation)
                self.emit('wake-attempt', key=key, request_id=plan['request_id'], **clean)
        with self.state.transaction():
            for key in self.state.keys():
                if key.startswith('delivery:'):
                    continue
                if key not in seen:
                    old = self.state.get(key)
                    old['continuous'] = False
                    self.state.put(key, old)
        return count


def clean_receipt(receipt):
    if not isinstance(receipt, dict):
        receipt = {}
    status = receipt.get('http_status')
    status = status if type(status) is int and 100 <= status <= 599 else None
    result = {'transport': receipt.get('transport') if receipt.get('transport') in {'hook', 't3', 'local', 'unknown'} else 'unknown',
              'http_status': status, 'accepted': receipt.get('accepted') is True,
              'downstream_wake': 'unverified',
              'native_delivery': 'verified' if (receipt.get('native_delivery') is True or receipt.get('native_delivery') == 'verified') and safe_id(receipt.get('owner_receipt_id')) else 'unverified'}
    for key in ('event_id', 'run_id', 'request_id', 'owner_receipt_id'):
        if safe_id(receipt.get(key)):
            result[key] = receipt[key]
    if receipt.get('reason') in {'transport-exception', 'hook-unavailable', 'hook-invalid-receipt', 'hook-timeout', 'hook-rejected', 'mcp-send-error', 'owner-state-changed', 'native-preflight-unavailable', 'local-only'}:
        result['reason'] = receipt['reason']
    return result


def run_read(args, source=None, timeout=8, allow_nonzero=False, env=None):
    """Bound stdin, stdout and waiting without sending any process signals."""
    if source is not None and len(source) > READ_LIMIT:
        raise Gap('read-helper-input-budget')
    child = subprocess.Popen(args, stdin=subprocess.PIPE if source is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    deadline, output, offset = time.monotonic() + timeout, bytearray(), 0
    try:
        with selectors.DefaultSelector() as selector:
            os.set_blocking(child.stdout.fileno(), False)
            selector.register(child.stdout, selectors.EVENT_READ)
            if source:
                os.set_blocking(child.stdin.fileno(), False)
                selector.register(child.stdin, selectors.EVENT_WRITE)
            elif child.stdin:
                child.stdin.close()
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise Gap('read-helper-timeout')
                for key, _ in selector.select(remaining):
                    if key.fileobj is child.stdin:
                        try:
                            offset += os.write(child.stdin.fileno(), source[offset:offset+65536])
                        except BrokenPipeError:
                            offset = len(source)
                        if offset == len(source):
                            selector.unregister(child.stdin)
                            child.stdin.close()
                    else:
                        chunk = os.read(child.stdout.fileno(), min(65536, READ_LIMIT + 1 - len(output)))
                        if not chunk:
                            selector.unregister(child.stdout)
                            child.stdout.close()
                        else:
                            output.extend(chunk)
                            if len(output) > READ_LIMIT:
                                raise Gap('read-helper-output-budget')
        child.wait(timeout=max(0, deadline-time.monotonic()))
    except subprocess.TimeoutExpired:
        raise Gap('read-helper-timeout') from None
    finally:
        if child.stdin:
            child.stdin.close()
        if child.stdout:
            child.stdout.close()
    if child.returncode and not allow_nonzero:
        raise Gap('read-helper-failed')
    return bytes(output)


def remote_discover(alias, options, source=None):
    """Both collector code and config travel as encoded Python over stdin."""
    try:
        raw = json.dumps(options, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError):
        raise Gap('remote-options-malformed') from None
    if len(raw) > OPTIONS_LIMIT:
        raise Gap('remote-options-oversize')
    source = Path(collector.__file__).read_bytes() if source is None else source
    script = (b'import base64,json\nexec(compile(base64.b64decode(' +
              repr(base64.b64encode(source)).encode() + b"), '<collector>', 'exec'), " +
              b"{'__name__':'__main__','_collector_options':json.loads(base64.b64decode(" +
              repr(base64.b64encode(raw)).encode() + b'))})\n')
    args = ['ssh', '-T', '-oBatchMode=yes', '-oStrictHostKeyChecking=yes', '-oUpdateHostKeys=no',
            '-oConnectTimeout=4', '-oServerAliveInterval=3', '-oServerAliveCountMax=1', '--', alias, 'python3 -']
    raw = run_read(args, script, timeout=12)
    if len(raw) > READ_LIMIT:
        raise Gap('read-helper-output-budget')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        raise Gap('remote-metadata-malformed') from None
    if (not isinstance(result, dict) or not isinstance(result.get('lanes'), list) or
            not isinstance(result.get('gaps'), list) or
            not all(isinstance(x, dict) for key in ('lanes', 'gaps') for x in result[key]) or
            not isinstance(result.get('coverage', []), list) or
            not all(isinstance(x, dict) for x in result.get('coverage', []))):
        raise Gap('remote-metadata-shape')
    if 'registry_cursor' in result:
        _, gaps = collector.checked_cursor(result['registry_cursor'])
        if gaps:
            raise Gap(gaps[0]['reason'])
    return result


def roster(path):
    hosts = []
    seen = set()
    for line in Path(path).expanduser().read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        words = line.split()
        if len(words) != 5 or not re.fullmatch(r'[a-z0-9_-]+', words[0]) or not re.fullmatch(r'[A-Za-z0-9_@.-]+', words[1]) or words[0] in seen:
            raise Gap('host-roster-invalid')
        seen.add(words[0])
        hosts.append(dict(zip(('name', 'alias', 't3url', 'cap', 'roles'), words)))
    return hosts


def authorized_roster(config, emit):
    requested = config.get('allowed_hosts', list(AUTHORIZED_HOSTS))
    if not isinstance(requested, list) or not all(isinstance(name, str) for name in requested):
        raise Gap('host-allowlist-invalid')
    allowed = set(requested) & AUTHORIZED_HOSTS.keys()
    result = []
    for host in roster(config['hosts_file']):
        name = host['name']
        if name not in allowed:
            emit('gap', host=name, reason='host-not-authorized')
            continue
        aliases, url = AUTHORIZED_HOSTS[name]
        if host['alias'] not in aliases or host['t3url'] not in {url, '-'}:
            emit('gap', host=name, reason='host-target-not-authorized')
            continue
        result.append(host)
    return result


def collector_options(config, host):
    name = host['name']
    options = dict(config.get('collector', {}), **config.get('collector_by_host', {}).get(name, {}))
    # A shared home never inherits the default trusted-home transcript access.
    if name == 'm3mbp':
        options.update(allowed_home_names=['mason'], systemd=False,
                       public_metadata_only=True, public_process_metadata_only=True,
                       native_sessions=[])
    if name in SHARED_HOSTS:
        options['allowed_recipients'] = ['Sats', 'sats']
        options['public_process_metadata_only'] = True
        options['native_sessions'] = [dict(spec) for spec in options.get('native_sessions', [])]
        for spec in options['native_sessions']:
            spec.pop('trusted_home_owner', None)
    if name != 'fd' or host['alias'] != 'local':
        options.pop('owner_bindings_file', None)
    return options


def t3_scope(config, host):
    return dict(scope_projects=config.get('t3_projects', {}).get(host),
                owner_bindings=config.get('t3_owner_bindings', {}).get(host),
                require_owner_binding=host in SHARED_HOSTS)


def collect_fleet(config, emit, clients=None, offsets=None, state=None):
    observations, clients = [], clients if clients is not None else {}
    try:
        hosts = authorized_roster(config, emit)
    except (OSError, KeyError, Gap):
        emit('gap', reason='host-roster-unavailable')
        return observations, clients
    source = Path(collector.__file__).read_bytes()
    started = time.monotonic()
    for host in hosts:
        name, alias = host['name'], host['alias']
        options = collector_options(config, host)
        if state is not None:
            options['registry_cursor'] = state.discovery_cursor(name)
            for gap in state.cursor_gaps.pop(name, []):
                emit('gap', host=name, **gap)
        if time.monotonic() - started > config.get('tick_budget_seconds', 240):
            emit('gap', host=name, reason='fleet-time-budget')
            continue
        if options.get('metadata_transport') == 't3-only':
            # Muse has no inbound transport. A separately attested local
            # native monitor may cover sessions; this timer still owns T3.
            result = {'lanes': [], 'gaps': [{'reason': 'native-local-monitor-unverified'}]}
        elif alias == 'local':
            result = collector.discover(options, arrival_clock=clock)
        else:
            try:
                result = remote_discover(alias, options, source)
            except Gap as error:
                reason = str(error)
                explicit = {'read-helper-output-budget', 'read-helper-input-budget', 'remote-options-oversize', 'remote-options-malformed',
                            'remote-metadata-malformed', 'remote-metadata-shape', 'registry-cursor-malformed', 'registry-cursor-oversize'}
                if reason in explicit:
                    if state is not None:
                        state.save_discovery_cursor(name, None)
                emit('gap', host=name, reason=reason if reason in explicit else 'ssh-metadata-unavailable')
                clients.pop(name, None)
                continue
            except (ValueError, OSError):
                emit('gap', host=name, reason='ssh-metadata-unavailable')
                clients.pop(name, None)
                continue
        arrived = clock()
        if state is not None and 'registry_cursor' in result:
            for gap in state.save_discovery_cursor(name, result['registry_cursor']):
                emit('gap', host=name, **gap)
        for summary in result.get('coverage', []):
            if not isinstance(summary, dict) or summary.get('kind') not in {'registry', 'codex', 'claude'}:
                continue
            # Only fixed metric names and typed counters enter the fleet log.
            metrics = {k: v for k, v in summary.items() if k in {
                'configured_roots', 'live_processes', 'bound_files', 'eligible',
                'terminal', 'approval', 'child', 't3', 'unknown', 'read_failed',
                'entries_seen', 'registered', 'cached_probes', 'truncated', 'cache_truncated'}
                       and type(v) in {int, bool} and (type(v) is bool or v >= 0)}
            emit('coverage', host=name, kind=summary['kind'], **metrics)
        for gap in result.get('gaps', []):
            reason = gap.get('reason')
            emit('gap', host=name, reason=reason if isinstance(reason, str) and re.fullmatch(r'[a-z-]{1,80}', reason) else 'collector-gap')
        for row in result.get('lanes', []):
            if not isinstance(row, dict) or not safe_id(row.get('lane')):
                emit('gap', host=name, reason='lane-metadata-shape')
                continue
            # Remote metadata cannot supply local monotonic/boot evidence.
            row_clock = row.get('_arrival_clock', arrived) if alias == 'local' else arrived
            obs = dict(row, key='lane:' + name + ':' + row['lane'], kind='lane', host=name, remote=alias != 'local', known=True, eligible=True,
                       _arrival_clock=row_clock)
            observations.append(obs)
        if not config.get('t3_enabled', True) or host['t3url'] == '-':
            continue
        remaining = config.get('tick_budget_seconds', 240) - (time.monotonic() - started)
        if remaining <= 0:
            emit('gap', host=name, reason='fleet-time-budget')
            continue
        try:
            t3config = config.get('t3', {})
            client = MCP(host['t3url'], Path(config['token_dir']).expanduser() / ('victor-' + name + '-nightly.token'),
                         timeout=t3config.get('timeout_seconds', 5), call_budget=t3config.get('max_calls', 48), seconds=min(remaining, t3config.get('max_seconds', 40)))
            clients[name] = client
            rows, gaps = collect_t3(client, name, max_pages=t3config.get('max_pages', 12), max_reads=t3config.get('max_reads', 20), **t3_scope(config, name), read_offset=(offsets or {}).get(name, 0), arrival_clock=clock)
            for t3_row in rows:
                bound = [row for row in observations if row.get('host') == name and
                         row.get('owner_thread_id') == t3_row.get('thread_id') and row.get('delivery')]
                if len(bound) == 1:
                    owner = bound[0]
                    t3_row.update(delivery=owner['delivery'], lanedir=owner['lanedir'], remote=owner.get('remote', False))
                    owner['delivery'] = None
                elif t3_row.get('eligible'):
                    emit('gap', host=name, reason='t3-delivery-plan-unbound')
            observations.extend(rows)
            for gap in gaps:
                emit('gap', **gap)
        except (Gap, KeyError, OSError):
            emit('gap', host=name, reason='mcp-environment-unavailable')
    return observations, clients


class Transport:
    """Stall and delivery-check plans stay local (Victor GO 3:18 PM CT 2026-10-20: Sats hears only START,
    BLOCKED, DONE and URGENT, and a stall or replan is none of them).

    The hook posts every milestone, whatever its recipient, to the one Sats webhook (sats-completion-notify
    webhook()), so no owner wake goes out from here. The durable reservation, its cooldown, the
    REPLAN-REQUIRED gate and the watchdog.jsonl record remain."""
    def __init__(self, config, directory, clients):
        self.config, self.directory, self.clients = config, Path(directory).resolve(), clients

    def __call__(self, plan):
        return {'transport': 'local', 'accepted': False, 'native_delivery': False, 'reason': 'local-only'}


RECIPIENT_RUN_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.ASCII)


def delivered(proof):
    """True for a hook acceptance proof that names the Sats run it started: a 2xx other than 299 with a recipient run id."""
    status, run_id = proof.get('http_status'), proof.get('recipient_run_id')
    return (type(status) is int and 200 <= status < 300 and status != 299
            and isinstance(run_id, str) and RECIPIENT_RUN_RE.fullmatch(run_id) is not None)


class AskTransport:
    """Deliver one T3 generation event to Sats as a start, blocker, done or urgent milestone through the hook.

    The run is the generation and the occurrence its event state, so the hook identity is thread +
    generation + state: a retry after an uncertain result reuses the hook's event and acceptance proof."""
    def __init__(self, config, directory):
        self.config, self.directory = config, Path(directory).resolve()

    def thread_notice(self, ask, kinds=('blocker', 'decision')):
        """'delivered', 'pending' or None: the thread's own terminal notice for this ask's turn.

        The thread posts it under sats-pm-visible-swarm § T3 terminal notice: lane t3-<threadId, each character
        outside [A-Za-z0-9_.-] as '-'>, run = threadId, kind blocker or decision (done for a DONE event),
        occurrence = the turn's run id, which is this ask message's runId. The key is the hook's _emit_milestone identity hash. Delivered needs
        the hook's recipient proof: an accepted acceptance record that names the Sats run id. Pending is a notice
        the hook still owns: a requeue entry, or an occurrence lock another process holds. Anything else, a 2xx
        without a recipient run id included, is None, and the ask pass sends one notice for the turn.

        The answer is read holding the hook's own occurrence lock for both kinds, opened and taken exactly as
        _emit_milestone and retry_milestone take it (milestones/<key>.lock, O_RDWR|O_CREAT|O_NOFOLLOW, 0600,
        LOCK_EX), but never waiting for it. Every hook transition for an occurrence happens under that lock:
        the acceptance proof is written and a requeue entry created inside it, and the drainer removes an
        entry only after retry_milestone has written the proof. So a locked read that finds neither proof nor
        entry is final for a turn that has ended, and the lock is released before the ask pass sends."""
        directory, keys = self.notice_keys(ask, kinds)
        held, busy = [], False
        try:
            for key in keys:
                try:
                    fd = os.open(directory / 'milestones' / (key + '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
                except OSError:
                    continue  # the hook opens this path the same way, so it cannot hold a notice here either
                held.append(fd)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    busy = True  # a hook process holds it: the notice is in flight
            for key in keys:
                try:
                    if delivered(json.loads((directory / 'milestones' / (key + '.acceptance.json')).read_text())):
                        return 'delivered'
                except (OSError, ValueError, AttributeError):
                    pass
            if busy or any((directory / 'requeue' / (key + '.json')).exists() for key in keys):
                return 'pending'
            return None
        finally:
            for fd in held:
                os.close(fd)

    def notice_keys(self, ask, kinds):
        """The hook state directory and the hook's _emit_milestone identity hash of the thread's notice of each kind."""
        lane = 't3-' + re.sub(r'[^A-Za-z0-9_.-]', '-', ask['thread_id'])
        directory = Path(self.config.get('hook_state_dir', '~/.local/state/sats-completion')).expanduser()
        return directory, [hashlib.sha256(json.dumps([lane, ask['thread_id'], kind, ask['run']], separators=(',', ':')).encode()).hexdigest()
                           for kind in kinds]

    def notice_message(self, ask, kinds=('blocker', 'decision')):
        """The message of the thread's own delivered notice for this ask's turn, else None: milestone_message of the
        hook's frozen payload (milestones/<key>.json) for the first kind whose acceptance proof delivered. The ask
        pass reads it after thread_notice() returned 'delivered', so it decides which of the turn's asks that notice
        carried (sats_stall_asks.notice_covers). The hook writes the payload once, under the occurrence lock,
        before its first post."""
        directory, keys = self.notice_keys(ask, kinds)
        for key in keys:
            try:
                if not delivered(json.loads((directory / 'milestones' / (key + '.acceptance.json')).read_text())):
                    continue
                message = json.loads((directory / 'milestones' / (key + '.json')).read_text()).get('milestone_message')
            except (OSError, ValueError, AttributeError):
                continue
            if isinstance(message, str):
                return message
        return None

    def __call__(self, plan):
        lane = 't3-' + plan['host'] + '-' + hashlib.sha256(plan['thread_id'].encode()).hexdigest()[:32]
        lanedir = self.directory / 'ask-receipts' / hashlib.sha256(('t3:' + plan['host'] + ':' + plan['thread_id']).encode()).hexdigest()
        lanedir.mkdir(parents=True, exist_ok=True, mode=0o700)
        args = [str(Path(self.config['hook_cli']).expanduser()), 'milestone', '--lane', lane, '--lanedir', str(lanedir),
                '--run', plan['run'], '--kind', plan['kind'], '--message', plan['message'], '--path', plan['evidence'],
                '--recipient', 'Sats', '--occurrence', plan['occurrence'], '--owner-thread-id', plan['thread_id']]
        try:
            hook_env = {key: value for key, value in os.environ.items() if not key.startswith('SATS_')}
            receipt = json.loads(run_read(args, timeout=40, allow_nonzero=True, env=hook_env))
            if not isinstance(receipt, dict):
                raise ValueError
            status = receipt.get('http_status')
            fields = {k: receipt[k] for k in ('event_id', 'http_status', 'sats_receipt', 'recipient_run_id', 'delivery_failure')
                      if k in receipt and (receipt[k] is None or type(receipt[k]) is int or safe_id(receipt[k]))}
            return dict(fields, transport='hook', accepted=type(status) is int and 200 <= status < 300 and status != 299)
        except Gap as error:
            return {'transport': 'hook', 'accepted': False, 'reason': 'hook-timeout' if str(error) == 'read-helper-timeout' else 'hook-rejected'}
        except OSError:
            return {'transport': 'hook', 'accepted': False, 'reason': 'hook-unavailable'}
        except (ValueError, TypeError, AttributeError):
            return {'transport': 'hook', 'accepted': False, 'reason': 'hook-invalid-receipt'}


def run_asks(config, directory, emit, dry_run, started):
    """One open-ask pass over every authorized host with an ask scope. Returns notices attempted."""
    budget = config.get('tick_budget_seconds', 240)
    scopes, settings = config.get('t3_ask_scope', {}), config.get('t3_asks', {})
    try:
        hosts = authorized_roster(config, lambda *a, **k: None)
    except (OSError, KeyError, Gap):
        emit('gap', reason='host-roster-unavailable')
        return 0
    seed = {}
    if config.get('t3_ask_seed_file'):
        try:
            seed = json.loads(Path(config['t3_ask_seed_file']).expanduser().read_text()).get('threads', {})
        except (OSError, ValueError, AttributeError):
            emit('gap', reason='ask-seed-unavailable')
    state = asks.AskState(None if dry_run else directory)
    send = None if dry_run else AskTransport(config, directory)
    total = 0
    try:
        for host in hosts:
            name = host['name']
            if host['t3url'] == '-' or name not in scopes:
                continue
            remaining = budget - (time.monotonic() - started)
            if remaining < 60:
                emit('gap', host=name, reason='ask-time-budget')
                continue
            try:
                client = MCP(host['t3url'], Path(config['token_dir']).expanduser() / ('victor-' + name + '-nightly.token'),
                             timeout=settings.get('timeout_seconds', 8), call_budget=settings.get('max_calls', 80),
                             seconds=min(remaining - 50, settings.get('max_seconds', 45)))
                total += asks.tick_host(client, name, state, emit, send, scopes[name], time.time(),
                                        max_notices=settings.get('max_notices', 10), evidence_dir=directory / 'asks',
                                        max_reads=settings.get('max_reads', 25), deadline=started + budget - 45,
                                        seed=seed.get(name) if isinstance(seed, dict) else None)
            except Exception:
                # The stall pass already completed; an ask failure never changes its result.
                emit('gap', host=name, reason='ask-scan-failed')
    finally:
        state.close()
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['tick', 'check-in'])
    parser.add_argument('--lanedir', help='exact local registered pack for one outcome check-in')
    parser.add_argument('--config', default=str(Path(__file__).parent / 'config' / 'watchdog.json'))
    parser.add_argument('--state-dir')
    parser.add_argument('--dry-run', action='store_true', help='read metadata only; no hook/send/state/log writes')
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        with Path(args.config).expanduser().open() as handle:
            config = json.load(handle)
        directory = Path(args.state_dir or config['state_dir']).expanduser().resolve()
        if args.command == 'check-in':
            if not args.lanedir:
                raise ValueError('lanedir required')
            pack = Path(args.lanedir).resolve()
            roots = [Path.home() / 'work']
            if not collector.below(pack, roots):
                raise ValueError('pack outside scope')
            row = collector.registry_row(pack)
            if not row or row.get('status') != 'active' or row.get('pending_approval'):
                raise ValueError('active registration required')
            delivery = collector.delivery_metadata(pack, roots)
            if delivery is None:
                raise ValueError('delivery plan required')
            now = clock()
            obs = dict(row, kind='lane', key='lane:fd:' + row['lane'], delivery=delivery,
                       known=True, eligible=True, observed_at=now['wall'])
            state = State(None if args.dry_run else directory)
            engine = Watchdog(state)
            if args.dry_run:
                obs = dict(obs, remote=True)
            engine.delivery_check(obs, now)
            saved = state.get(delivery_key(obs))
            required = saved.get('required', False)
            print(json.dumps({'state': 'REPLAN_REQUIRED' if required else saved['last_result'],
                'required_action': 'revised_plan_or_replace' if required else None,
                'question': 'what is deployed or verified since last check?', 'unit': delivery['unit']}))
            state.close()
            return 1 if required else 0
        emit = Events(stdout=True) if args.dry_run else Events(directory / 'watchdog.jsonl', stdout=True)
        if not args.dry_run and config.get('enabled') is not True:
            print(json.dumps({'action': 'disabled', 'reason': 'candidate-awaits-opus-review'}))
            return 0
        started = time.monotonic()
        state = State(None if args.dry_run else directory)
        rows, clients = collect_fleet(config, emit, offsets=state.offsets(), state=state)
        state.save_offsets(clients)
        watchdog = Watchdog(state, emit, threshold=config.get('stall_seconds', 900), cooldown=config.get('cooldown_seconds', 900))
        count = watchdog.tick(rows, Transport(config, directory, clients) if not args.dry_run else lambda plan: (_ for _ in ()).throw(RuntimeError('dry-run transport forbidden')))
        notices = run_asks(config, directory, emit, args.dry_run, started) if config.get('t3_enabled', True) else 0
        emit('tick-complete', dry_run=args.dry_run, observed_owners=len(rows), wake_attempts=count, ask_notices=notices)
        state.close()
        return 0
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        print(json.dumps({'action': 'gap', 'reason': 'watchdog-config-or-state-unavailable'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
