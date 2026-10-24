"""Dependency-free, read-only lane metadata collector, also sent over SSH stdin.

Only explicitly scoped roots are inspected. Native process executable, parent,
open-session-file and start metadata bind liveness; argv is never returned.
No credentials, private-family transcripts or writes.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
import math
import stat
from collections import deque

KINDS = {'start', 'step', 'blocker', 'decision', 'done', 'stalled'}
TERMINAL = {'done', 'completed', 'settled', 'archived', 'cancelled', 'failed', 'blocked'}
RUN_RE = re.compile(r'([0-9]{9,11})-([0-9]{9})')
INVOCATION_RE = re.compile(r'[0-9a-f]{32}')
STREAM_RE = re.compile(r'(?:producer|review)(?:\.[A-Za-z0-9_-]+)*\.(?:stdout|stderr)')
STREAM_ENTRIES = 256
RESOURCE_COUNTERS = ('CPUUsageNSec', 'IOReadBytes', 'IOWriteBytes')
SESSION_RE = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
NATIVE_LIMIT = 524288
CURSOR_LIMIT = 262144


def checked_cursor(value):
    """Reject unusable stored/remote continuations before any traversal."""
    if value is None:
        return None, []
    try:
        if len(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()) > CURSOR_LIMIT:
            return None, [{'reason': 'registry-cursor-oversize'}]
        if not isinstance(value, dict) or set(value) != {'frontier', 'known'}:
            raise ValueError('cursor shape')
        if not isinstance(value['frontier'], list) or not isinstance(value['known'], list):
            raise ValueError('cursor lists')
        def path_ok(path):
            return (isinstance(path, str) and 0 < len(path) <= 4096 and
                    '\0' not in path and Path(path).is_absolute())
        if not all(path_ok(path) for path in value['known']):
            raise ValueError('cursor known')
        for node in value['frontier']:
            if (not isinstance(node, dict) or set(node) != {'path', 'depth', 'offset'} or
                    not path_ok(node['path']) or
                    any(type(node[k]) is not int or not 0 <= node[k] < 2**63 for k in ('depth', 'offset'))):
                raise ValueError('cursor node')
        return value, []
    except (ValueError, TypeError, OverflowError):
        return None, [{'reason': 'registry-cursor-malformed'}]


def bounded_cursor(frontier, known, gaps):
    # Reserve half for each class so a large owner cache cannot starve traversal.
    result = {'frontier': [], 'known': []}
    for key, values in (('frontier', frontier), ('known', known)):
        used = 0
        for value in values:
            size = len(json.dumps(value, separators=(',', ':')).encode()) + 1
            if used + size > (CURSOR_LIMIT - 64) // 2:
                gaps.append({'reason': 'registry-cursor-truncated'})
                break
            result[key].append(value)
            used += size
    return result


def binding_field(value):
    return (isinstance(value, str) and 0 < len(value) <= 200 and bool(value.strip())
            and not any(ord(c) < 32 or ord(c) == 127 or c in '\u0085\u2028\u2029' for c in value))


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def owner_bindings(config):
    """Only the runtime caller supplies the trusted P5b registry path."""
    path = config.get('owner_bindings_file')
    if path is None:
        return None, 'owner-bindings-not-configured'
    if not isinstance(path, str) or not Path(path).is_absolute():
        return None, 'owner-bindings-malformed'
    try:
        raw, _ = read_regular(Path(path), 1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError('oversize bindings')
        rows = json.loads(raw, object_pairs_hook=unique_fields)
        if not isinstance(rows, list):
            raise ValueError('bindings shape')
        index = {}
        for row in rows:
            if (not isinstance(row, dict) or
                    not all(binding_field(row.get(k)) for k in ('lane', 'run', 'recipient')) or
                    type(row.get('priority')) is not bool or
                    (row.get('owner_thread_id') is not None and not binding_field(row['owner_thread_id']))):
                raise ValueError('binding fields')
            index.setdefault((row['lane'], row['run']), []).append(row)
        return index, None
    except OSError:
        return None, 'owner-bindings-unavailable'
    except (ValueError, TypeError):
        return None, 'owner-bindings-malformed'


def callback_lane(value):
    """Read systemctl show's exact executable/argv tuple, never a unit name."""
    if not isinstance(value, str):
        return None
    blocks = re.findall(r'\{[^{}]*\}', value)
    if not blocks or re.sub(r'\{[^{}]*\}', '', value).strip():
        return None
    callbacks = []
    for block in blocks:
        path = re.search(r'(?:\{|;)\s*path=([^;]+);', block)
        argv = re.search(r';\s*argv\[\]=([^;]+);', block)
        if not path or not argv:
            return None
        executable = path[1].strip()
        if Path(executable).name != 'sats-completion-notify':
            continue
        try:
            args = shlex.split(argv[1].strip())
        except ValueError:
            return None
        if (not Path(executable).is_absolute() or len(args) != 3 or
                args[:2] != [executable, 'exit'] or not binding_field(args[2])):
            return None
        callbacks.append(args[2])
    return callbacks[0] if len(callbacks) == 1 else None


def native_run_key(lane, raw_run, invocation):
    safe = re.sub(r'[^A-Za-z0-9._-]', '_', lane)[:60]
    digest = hashlib.sha256(lane.encode()).hexdigest()[:10]
    tail = 'run-' + raw_run if isinstance(raw_run, str) and RUN_RE.fullmatch(raw_run) else 'run-bad-' + invocation
    return '%s-%s-%s' % (safe, digest, tail)


def systemd_started_at(props):
    """Accept known wall timestamp formats; unknown timezones remain cold."""
    for key in ('ExecMainStartTimestamp', 'ActiveEnterTimestamp'):
        value = props.get(key, '')
        at = timestamp(value)
        if at is None:
            match = re.fullmatch(r'[A-Za-z]{3} (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,6})?) (UTC|GMT|CDT|CST)', value)
            if match:
                offset = {'UTC': '+00:00', 'GMT': '+00:00', 'CDT': '-05:00', 'CST': '-06:00'}[match[2]]
                at = timestamp(match[1].replace(' ', 'T') + offset)
        if at is not None and at <= time.time():
            return at
    return None


def timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if math.isfinite(value) and 0 < value < 10**11 else None
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def below(path, roots):
    """Check scope without traversing symlinks, even within approved roots."""
    try:
        p = Path(os.path.abspath(path))
        root = next((r for r in roots if p == r or r in p.parents), None)
        if root is None:
            return False
        current = root
        for part in ('', *p.relative_to(root).parts):
            current = current / part
            try:
                if stat.S_ISLNK(current.lstat().st_mode):
                    return False
            except FileNotFoundError:
                break
        return True
    except (OSError, RuntimeError):
        return False


def stat_file(path):
    try:
        s = path.lstat()
        if not stat.S_ISREG(s.st_mode):
            raise OSError('not regular')
        return {'bytes': s.st_size, 'mtime': s.st_mtime, 'inode': s.st_ino}
    except FileNotFoundError:
        return None


def read_regular(path, limit, tail=False):
    """No symlinks, devices or FIFO reads, including concurrent replacement."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise OSError('not regular')
        start = max(0, info.st_size - limit) if tail else 0
        handle.seek(start)
        return handle.read(limit), start


def registry_row(parent):
    registry = parent / 'LANE.json'
    try:
        raw, _ = read_regular(registry, 16385)
    except FileNotFoundError:
        return None
    if len(raw) > 16384:
        raise ValueError('registry oversize')
    row = json.loads(raw)
    if not isinstance(row, dict):
        raise ValueError('registry shape')
    result = {k: row.get(k) for k in ('lane', 'lanedir', 'run', 'recipient', 'status', 'unit', 'parent', 'parentThreadId', 'owner', 'pending_approval', 'started_at', 'owner_thread_id')}
    result['source'] = 'registry'
    return result


def delivery_metadata(directory, roots):
    """Return outcome receipts, never their contents or activity counters."""
    path = directory / 'DELIVERY.json'
    if not path.exists():
        return None
    if not below(path, [directory]):
        raise ValueError('delivery path outside scope')
    plan = json.loads(path.read_bytes())
    if (not isinstance(plan, dict) or type(plan.get('revision')) is not int or plan['revision'] < 1 or
            type(plan.get('set_point')) not in {int, float} or not math.isfinite(plan['set_point']) or
            any(not isinstance(plan.get(k), str) or not plan[k].strip() for k in ('unit', 'owner', 'pilot'))):
        raise ValueError('delivery plan shape')
    effects = []
    for key in ('cause', 'revised_path'):
        if key in plan and (not isinstance(plan[key], str) or not plan[key].strip()):
            raise ValueError('delivery replan shape')
    receipts = plan.get('evidence', [])
    if not isinstance(receipts, list):
        raise ValueError('delivery evidence list required')
    for item in receipts:
        if (not isinstance(item, dict) or item.get('kind') not in {'deployed', 'verified'} or
                not isinstance(item.get('path'), str) or not item['path'].strip()):
            raise ValueError('delivery evidence shape')
        evidence_path = directory / item['path']
        if not below(evidence_path, [directory]):
            raise ValueError('delivery evidence outside scope')
        if not stat.S_ISREG(evidence_path.stat().st_mode):
            raise ValueError('regular delivery evidence required')
        hasher = hashlib.sha256()
        with evidence_path.open('rb') as handle:
            while chunk := handle.read(1024 * 1024):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        if digest != item.get('sha256'):
            raise ValueError('delivery evidence changed')
        effects.append(item['kind'] + ':' + digest)
    return {k: plan[k] for k in ('revision', 'set_point', 'unit', 'owner', 'pilot')} | {
        'effects': sorted(set(effects)), 'cause': plan.get('cause'), 'revised_path': plan.get('revised_path')}


def progress_log(directory, lane):
    """Read only regular-file metadata for launch, producer and review streams.

    Enumeration stays pack-local and bounded. An incomplete enumeration is a
    collection gap, never proof that unexamined streams have stopped growing.
    """
    files = []
    names = {'lane.log', lane + '.stdout', lane + '.stderr',
             'producer.stdout', 'producer.stderr', 'review.stdout', 'review.stderr'}
    # Pin the directory and use non-following stat calls. No stream is opened.
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with os.scandir(fd) as entries:
            for count, entry in enumerate(entries):
                if count >= STREAM_ENTRIES:
                    raise OSError('progress-stream-budget')
                if STREAM_RE.fullmatch(entry.name):
                    names.add(entry.name)
        for name in sorted(names):
            if Path(name).name != name:
                raise OSError('non-local-stream')
            try:
                s = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(s.st_mode):
                raise OSError('not regular')
            files.append((name, {'bytes': s.st_size, 'mtime': s.st_mtime, 'inode': s.st_ino}))
    finally:
        os.close(fd)
    if not files:
        return None
    if len(files) == 1:
        return files[0][1]
    identity = json.dumps([(name, meta['inode']) for name, meta in files])
    return {'bytes': sum(meta['bytes'] for _, meta in files),
            'mtime': max(meta['mtime'] for _, meta in files),
            'inode': int(hashlib.sha256(identity.encode()).hexdigest()[:16], 16)}


def own_cgroups():
    """Exclude the collecting process and ancestors from resource progress."""
    try:
        lines = Path('/proc/self/cgroup').read_text().splitlines()
        groups = [line.split(':', 2)[2] for line in lines if len(line.split(':', 2)) == 3]
        return groups if groups and all(g.startswith('/') for g in groups) else None
    except OSError:
        return None


def resource_metadata(props, unit, groups):
    """Only a current, separate lane unit can supply productive counters.

    systemd uses UINT64_MAX for unavailable accounting on some versions.
    Missing, not-set and unsupported values remain unknown, including zero
    accounting capabilities on hosts where these properties do not exist.
    """
    invocation = props.get('InvocationID', '')
    group = props.get('ControlGroup', '')
    if (props.get('Id') != unit or not INVOCATION_RE.fullmatch(invocation) or
            not group.startswith('/') or groups is None or
            any(own == group or own.startswith(group.rstrip('/') + '/') for own in groups)):
        return None
    counters = {}
    for key in RESOURCE_COUNTERS:
        value = props.get(key, '')
        number = int(value) if re.fullmatch(r'[0-9]{1,20}', value) else None
        counters[key] = number if number is not None and number < 2**64 - 1 else None
    return dict(unit=unit, invocation_id=invocation, counters=counters, observed_at=time.time())


def milestone(path, run, lane=None, started_at=None):
    """Parse only a bounded tail. Discard all message/path text after extracting proof.

    Hook format is timestamp kind=... run=...; JSON lines are accepted too.
    A stalled event's timestamp, bytes and mtime are deliberately not heartbeats.
    """
    meta = stat_file(path)
    if meta is None:
        return {'at': None, 'token': None, 'mtime': None, 'terminal': False}
    data, start = read_regular(path, 65536, tail=True)
    lines = data.decode('utf-8', 'replace').splitlines()
    if start:
        lines = lines[1:]
    last = None
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if isinstance(row, dict):
            kind = row.get('kind')
            at = timestamp(row.get('at', row.get('timestamp', row.get('ts'))))
            event_run = row.get('run')
        else:
            match = re.search(r'(?:^|\s)kind=(start|step|blocker|decision|done|stalled)(?:\s|$)', line)
            kind = match.group(1) if match else None
            at = timestamp(line.split(' ', 1)[0])
            match_run = re.search(r'(?:^|\s)run=([^\s]+)', line)
            event_run = match_run.group(1) if match_run else None
            if kind is None:
                # Frozen hook candidate uses timestamp lane kind message path.
                fields = line.split(' ', 3)
                if len(fields) >= 3 and fields[1] == lane and fields[2] in KINDS:
                    kind = fields[2]
        if kind not in KINDS or kind == 'stalled' or at is None:
            continue
        if event_run is not None and str(event_run) != str(run):
            continue
        if event_run is None and (started_at is None or at < started_at):
            continue
        last = {'at': at, 'token': hashlib.sha256(line.encode()).hexdigest(),
                'mtime': meta['mtime'], 'terminal': kind == 'done'}
    return last or {'at': None, 'token': None, 'mtime': None, 'terminal': False}


def command(args, timeout=4):
    """Bound read subprocesses without subprocess.run's automatic SIGKILL timeout.

    A timed-out helper is left alone and reported as a collection gap.
    No signals are sent, including to our own helpers.
    """
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if p.stdout:
            p.stdout.close()
        raise OSError('read-timeout') from None
    if p.returncode or len(out) > 2_000_000:
        raise OSError('read-failed')
    return out.decode('utf-8', 'replace')


def systemd_lanes(reader=command, config=None):
    listed = reader(['systemctl', '--user', 'list-units', '--all', '--type=service',
                     '--plain', '--no-legend', '--no-pager', 'sats-lane-*.service'])
    units = []
    for line in listed.splitlines():
        unit = next((word for word in line.split() if word.startswith('sats-lane-') and word.endswith('.service')), None)
        if unit:
            units.append(unit)
    lanes, gaps = [], []
    bindings, binding_gap = owner_bindings(config or {})
    groups = own_cgroups()
    for unit in units[:100]:
        try:
            raw = reader(['systemctl', '--user', 'show', unit, '--no-pager',
                          '--property=ActiveState,SubState,Environment,WorkingDirectory,InvocationID,Id,ExecStopPost,ExecMainStartTimestamp,ActiveEnterTimestamp,ControlGroup,CPUUsageNSec,IOReadBytes,IOWriteBytes'])
            props = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
            if props.get('ActiveState') != 'active' or props.get('SubState') not in {'running', 'start'}:
                continue
            if props.get('Id', unit) != unit:
                gaps.append({'reason': 'systemd-unit-identity-mismatch'})
                continue
            env = dict(part.split('=', 1) for part in shlex.split(props.get('Environment', '')) if '=' in part)
            binding = json.loads(env.get('SATS_NOTICE_BINDING', '{}'))
            if not isinstance(binding, dict):
                raise ValueError('native binding shape')
            lane = env.get('SATS_LANE')
            run = env.get('SATS_RUN') or props.get('InvocationID')
            recipient = env.get('SATS_RECIPIENT')
            # Never infer a seat from lane names, process arguments or account names.
            derived_run = '%s-%s-run-%s' % (re.sub(r'[^A-Za-z0-9._-]', '_', str(lane))[:60], hashlib.sha256(str(lane).encode()).hexdigest()[:10], run)
            if binding.get('lane') == lane and binding.get('run') in {run, 'run-' + str(run), derived_run} and binding.get('priority') is True:
                recipient = binding.get('recipient')
                lanes.append({'lane': lane, 'run': run, 'recipient': recipient,
                              'lanedir': env.get('SATS_PACK') or props.get('WorkingDirectory'),
                              'owner_thread_id': binding.get('owner_thread_id'),
                              'unit': unit, 'invocation_id': props.get('InvocationID'),
                              'resources': resource_metadata(props, unit, groups),
                              'status': 'active', 'source': 'systemd'})
                continue
            if 'SATS_NOTICE_BINDING' in env:
                gaps.append({'reason': 'native-owner-binding-mismatch'})
                continue
            lane = callback_lane(props.get('ExecStopPost'))
            invocation = props.get('InvocationID', '')
            directory = props.get('WorkingDirectory')
            if (lane is None or not INVOCATION_RE.fullmatch(invocation) or
                    not isinstance(directory, str) or not directory or not Path(directory).is_absolute() or
                    ('SATS_LANE' in env and env['SATS_LANE'] != lane) or
                    ('SATS_PACK' in env and env['SATS_PACK'] != directory)):
                gaps.append({'reason': 'legacy-unit-metadata-rejected'})
                continue
            if bindings is None:
                gaps.append({'reason': binding_gap})
                continue
            raw_run = env.get('SATS_RUN')
            key = native_run_key(lane, raw_run, invocation)
            matches = bindings.get((lane, key), [])
            if not matches:
                gaps.append({'reason': 'trusted-current-binding-missing'})
                continue
            owners = {(row['recipient'], row.get('owner_thread_id')) for row in matches}
            if len(owners) != 1:
                gaps.append({'reason': 'conflicting-owner-binding'})
                continue
            if not all(row['priority'] is True for row in matches):
                gaps.append({'reason': 'trusted-current-binding-not-priority'})
                continue
            recipient, thread = owners.pop()
            # Explicit hook binding_key preserves fallback derived keys unchanged.
            # A valid native SATS_RUN must instead remain raw for that hook.
            run = raw_run if isinstance(raw_run, str) and RUN_RE.fullmatch(raw_run) else key
            lanes.append({'lane': lane, 'run': run, 'recipient': recipient,
                          'lanedir': directory, 'owner_thread_id': thread,
                          'unit': unit, 'invocation_id': invocation, 'binding_run': key,
                          'resources': resource_metadata(props, unit, groups),
                          'legacy_binding': True, 'started_at': systemd_started_at(props),
                          'status': 'active', 'source': 'systemd'})
        except (OSError, ValueError, TypeError):
            gaps.append({'reason': 'systemd-show-failed'})
    if len(units) > 100:
        gaps.append({'reason': 'systemd-unit-budget'})
    return lanes, gaps


def executable_name(executable):
    return Path(executable.removesuffix(' (deleted)')).name


def process_kind(executable, args=()):
    name = executable_name(executable)
    if name in {'codex', 'claude'}:
        return name
    if name == 'claude.exe' and re.search(
            r'/@anthropic-ai/(?:claude-code|\.claude-code-[A-Za-z0-9_-]+)/bin/claude\.exe$',
            executable.removesuffix(' (deleted)')):
        return 'claude'
    # Claude's npm distribution runs under node; other node programs are not
    # agents merely because an argument mentions Claude.
    if name in {'node', 'bun'} and len(args) > 1:
        script = args[1]
        if script.endswith('/@anthropic-ai/claude-code/cli.js'):
            return 'claude'
    return None


def likely_agent_executable(executable):
    name = executable_name(executable)
    # This observed Codex helper has no independent session ownership.
    if name == 'codex-code-mode-host':
        return False
    return bool(re.match(r'^(?:codex|claude)(?:$|[._-])', name) or
                '/@anthropic-ai/claude-code/' in executable or
                '/@anthropic-ai/.claude-code-' in executable or
                '/@openai/codex/' in executable or '/claude/versions/' in executable)


def approval_bypass(args):
    # Flag-like prompts and option values are not permission-mode evidence.
    # Unknown CLI syntax is deferred rather than guessed from argv text.
    values = {'--model', '--effort', '--resume', '--session-id', '--system-prompt',
              '--append-system-prompt', '--settings', '--output-format', '--input-format',
              '--agent', '--agents', '--max-turns', '--fallback-model'}
    flags = {'--verbose', '--print', '-p', '--continue', '-c'}
    start = 2 if args and executable_name(args[0]) in {'node', 'bun'} else 1
    bypass, i = False, start
    while i < len(args):
        arg = args[i]
        if arg == '--':
            return bypass
        if arg == '--dangerously-skip-permissions':
            bypass = True
        elif arg == '--permission-mode':
            if i + 1 >= len(args):
                return False
            i += 1
            bypass = args[i] == 'bypassPermissions'
        elif arg.startswith('--permission-mode='):
            bypass = arg.partition('=')[2] == 'bypassPermissions'
        elif arg in values:
            if i + 1 >= len(args):
                return False
            i += 1
        elif arg in flags or any(arg.startswith(option + '=') for option in values):
            pass
        else:
            return False
        i += 1
    return bypass


def process_cpu(snapshot, pid, reader, linux):
    """Own-UID tree CPU, including waited children, without collector activity."""
    tree, pending = set(), [pid]
    children = {}
    for item in snapshot.values():
        children.setdefault(item['ppid'], []).append(item['pid'])
    while pending:
        current = pending.pop()
        if current in tree:
            return None
        tree.add(current)
        pending.extend(children.get(current, []))
    # A collector launched as a native tool must not create its own heartbeat.
    if os.getpid() in tree:
        return None
    total = 0
    for current in tree:
        if linux:
            value = snapshot[current].get('cpu_ticks')
            if value is None:
                return None
            total += value
        else:
            raw = reader(['ps', '-p', str(current), '-o', 'time=']).strip()
            match = re.fullmatch(r'(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)', raw)
            if not match:
                return None
            total += int((int(match[1] or 0) * 86400 + int(match[2] or 0) * 3600 +
                          int(match[3]) * 60 + float(match[4])) * 100)
    return total


def native_processes(config, reader=command):
    """Current own-UID process metadata. Open file identity is primary proof.

    Linux /proc and macOS ps/lsof are read only. No signal, shell invocation,
    process environment or raw command output leaves this function.
    """
    processes, gaps, snapshot = [], [], {}
    limit = int(config.get('native_process_budget', 4096))
    if Path('/proc/self/stat').exists():
        try:
            with os.scandir('/proc') as entries:
                for entry in entries:
                    if not entry.name.isdecimal():
                        continue
                    try:
                        uid = entry.stat(follow_symlinks=False).st_uid
                    except FileNotFoundError:
                        continue
                    except OSError:
                        gaps.append({'reason': 'native-process-read-failed'})
                        continue
                    if uid != os.getuid():
                        continue
                    if len(snapshot) >= limit:
                        gaps.append({'reason': 'native-process-budget'})
                        break
                    try:
                        base = Path(entry.path)
                        raw, _ = read_regular(base / 'stat', 8192)
                        fields = raw.decode().rsplit(')', 1)[1].split()
                        if fields[0] in {'Z', 'X'}:
                            continue
                        executable = os.readlink(base / 'exe')
                        args = []
                        if not config.get('public_process_metadata_only') and (process_kind(executable) or executable_name(executable) in {'node', 'bun'}):
                            raw, _ = read_regular(base / 'cmdline', 65536)
                            args = raw.decode('utf-8', 'replace').rstrip('\0').split('\0')
                        kind = process_kind(executable, args)
                        ids = []
                        for i, arg in enumerate(args[:-1]):
                            if arg in {'--resume', '--session-id', 'resume'} and SESSION_RE.fullmatch(args[i+1]):
                                ids.append(args[i+1])
                        snapshot[int(entry.name)] = {
                            'kind': kind, 'pid': int(entry.name), 'ppid': int(fields[1]),
                            'generation': entry.name + ':' + fields[19],
                            'cwd': os.readlink(base / 'cwd'), 'executable': executable,
                            'session_ids': ids, 'base': base,
                            'approval_bypass': kind == 'claude' and approval_bypass(args),
                            'cpu_ticks': sum(int(fields[i]) for i in (11, 12, 13, 14))}
                    except (OSError, ValueError, IndexError):
                        gaps.append({'reason': 'native-process-read-failed'})
        except OSError:
            return [], [{'reason': 'native-process-unavailable'}]
    else:
        try:
            raw = reader(['ps', '-axo', 'pid=,ppid=,uid=,comm='])
            for line in raw.splitlines():
                words = line.strip().split(None, 3)
                if len(words) != 4 or int(words[2]) != os.getuid():
                    continue
                if len(snapshot) >= limit:
                    gaps.append({'reason': 'native-process-budget'})
                    break
                pid, parent = int(words[0]), int(words[1])
                executable = words[3]
                kind = process_kind(executable)
                ids = []
                bypass = False
                if not config.get('public_process_metadata_only') and (kind or executable_name(executable) in {'node', 'bun'}):
                    # Read privately, reduce immediately to executable identity
                    # and validated session ids. Never emit argv or errors.
                    try:
                        args = shlex.split(reader(['ps', '-p', str(pid), '-o', 'args=']))
                        kind = process_kind(executable, args)
                        bypass = kind == 'claude' and approval_bypass(args)
                        ids = [args[i+1] for i, x in enumerate(args[:-1])
                               if x in {'--resume', '--session-id', 'resume'} and SESSION_RE.fullmatch(args[i+1])]
                    except (OSError, ValueError):
                        gaps.append({'reason': 'native-process-argv-unavailable'})
                snapshot[pid] = {'kind': kind, 'pid': pid, 'ppid': parent,
                                 'executable': executable, 'session_ids': ids,
                                 'approval_bypass': bypass}
        except (OSError, ValueError):
            return [], [{'reason': 'native-process-unavailable'}]
    work_roots = [Path(os.path.abspath(os.path.expanduser(r))) for r in config.get('roots', ['~/work'])]
    for pid, record in snapshot.items():
        if record['kind'] is None:
            if likely_agent_executable(record['executable']):
                gaps.append({'reason': 'native-agent-executable-unrecognized'})
            continue
        files, ancestor_lane, ancestor_agent, t3_owned = [], False, False, False
        try:
            if 'base' in record:
                raw, _ = read_regular(record['base'] / 'cgroup', 16384)
                groups = [line.split(':', 2)[-1] for line in raw.decode().splitlines()]
                ancestor_lane = any(group.endswith('/' + unit) or '/' + unit + '/' in group
                                    for group in groups for unit in config.get('_owning_units', []))
                ancestor_lane |= any(re.fullmatch(r'sats-lane-[^/]+\.service', part)
                                     for group in groups for part in group.split('/'))
                with os.scandir(record['base'] / 'fd') as entries:
                    for i, entry in enumerate(entries):
                        if i >= 4096:
                            raise OSError('fd budget')
                        try:
                            target = os.readlink(entry.path)
                            if target.endswith('.jsonl'):
                                files.append(target)
                        except FileNotFoundError:
                            continue
            else:
                generation = reader(['ps', '-p', str(pid), '-o', 'lstart=']).strip()
                if not generation:
                    raise OSError('missing start')
                record['generation'] = str(pid) + ':' + hashlib.sha256(generation.encode()).hexdigest()[:16]
                raw = reader(['lsof', '-a', '-p', str(pid), '-Fn'])
                files = [line[1:] for line in raw.splitlines() if line.startswith('n/') and line.endswith('.jsonl')]
                cwd = reader(['lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'])
                record['cwd'] = next((x[1:] for x in cwd.splitlines() if x.startswith('n/')), '')
            current, visited = record, set()
            for depth in range(64):
                if current['pid'] in visited:
                    raise OSError('ancestor cycle')
                visited.add(current['pid'])
                if depth and current['kind']:
                    ancestor_agent = True
                executable = current.get('executable', '')
                if Path(executable).name.startswith('t3') or '/t3-code/' in executable:
                    t3_owned = True
                cwd = current.get('cwd', '')
                if isinstance(cwd, str) and below(cwd, work_roots):
                    directory = Path(cwd)
                    while below(directory, work_roots):
                        row = registry_row(directory)
                        if row is not None:
                            # Even malformed/missing recipients cannot turn a
                            # registered child into an independent native owner.
                            ancestor_lane = True
                            break
                        directory = directory.parent
                current = snapshot.get(current['ppid'])
                if current is None:
                    break
            # A process can exit or be replaced while fd/ancestor reads run.
            if 'base' in record:
                raw, _ = read_regular(record['base'] / 'stat', 8192)
                fields = raw.decode().rsplit(')', 1)[1].split()
                if fields[0] in {'Z', 'X'} or record['generation'] != str(pid) + ':' + fields[19]:
                    gaps.append({'reason': 'native-process-generation-changed'})
                    continue
            elif reader(['ps', '-p', str(pid), '-o', 'lstart=']).strip() != generation:
                gaps.append({'reason': 'native-process-generation-changed'})
                continue
            try:
                cpu = process_cpu(snapshot, pid, reader, 'base' in record)
            except (OSError, ValueError, KeyError):
                cpu = None
            if cpu is None:
                gaps.append({'reason': 'native-resource-unavailable'})
            processes.append({k: record[k] for k in ('kind', 'pid', 'generation', 'session_ids', 'approval_bypass')})
            processes[-1].update(session_files=sorted(set(files)), ancestor_lane=ancestor_lane,
                                 parent_session_id='ancestor' if ancestor_agent else None, t3_owned=t3_owned,
                                 cpu_ticks=cpu)
        except (OSError, ValueError, KeyError):
            gaps.append({'reason': 'native-live-binding-read-failed'})
    return processes, gaps


def native_schema(path, kind, bypass=False):
    """Project known JSONL schemas to ids, timestamps and state only.

    Message, tool, thinking, signature and result text is discarded. A bounded
    head obtains Codex's source/identity, a bounded tail obtains current state.
    Partial or unknown state is never interpreted as running.
    """
    head, _ = read_regular(path, 65536)
    tail, start = read_regular(path, NATIVE_LIMIT, tail=True)
    chunks = [tail] if not start else [head, tail]
    meta = {'session_id': None, 'turn_id': None, 'state': 'unknown',
            'child': False, 't3_owned': False, 'activity_at': None}
    pending = set()
    never = False
    for n, chunk in enumerate(chunks):
        lines = chunk.splitlines()
        if n and start:
            lines = lines[1:]
            # Events omitted between head and tail cannot prove current policy,
            # current turn, or resolution of an outstanding human question.
            meta.update(turn_id=None, state='unknown')
            pending.clear()
            never = False
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            at = timestamp(row.get('timestamp'))
            typ = row.get('type')
            if kind == 'codex':
                payload = row.get('payload', {})
                if not isinstance(payload, dict):
                    continue
                if typ == 'session_meta':
                    sid = payload.get('id')
                    if not isinstance(sid, str) or not SESSION_RE.fullmatch(sid):
                        raise ValueError('session identity')
                    meta['session_id'] = sid
                    source = payload.get('source')
                    meta['child'] |= isinstance(source, dict) or bool(payload.get('parent_thread_id'))
                    meta['t3_owned'] |= payload.get('originator') in {'T3 Code', 't3', 't3_code'}
                turn = payload.get('turn_id')
                if typ in {'turn_context', 'event_msg'} and isinstance(turn, str) and SESSION_RE.fullmatch(turn):
                    if turn != meta['turn_id']:
                        never = False
                        pending.clear()
                    meta['turn_id'] = turn
                event = payload.get('type') if typ == 'event_msg' else None
                if event == 'task_started':
                    meta['state'] = 'active'
                    pending.clear()
                    never = False
                elif event in {'task_complete', 'turn_aborted', 'shutdown_complete'}:
                    meta['state'] = 'terminal'
                if typ == 'turn_context':
                    never = (isinstance(turn, str) and SESSION_RE.fullmatch(turn) is not None and
                             payload.get('approval_policy') == 'never')
                if typ == 'response_item' and payload.get('type') in {'function_call', 'custom_tool_call'} and payload.get('name') in {
                        'request_user_input', 'mcp__functions__request_user_input', 'functions.request_user_input'}:
                    pending.add(payload.get('call_id'))
                if typ == 'response_item' and payload.get('type') in {'function_call_output', 'custom_tool_call_output'}:
                    pending.discard(payload.get('call_id'))
                if typ in {'turn_context', 'event_msg', 'response_item'} and at is not None:
                    meta['activity_at'] = max(meta['activity_at'] or 0, at)
            else:
                sid = row.get('sessionId', row.get('session_id'))
                if isinstance(sid, str) and SESSION_RE.fullmatch(sid):
                    if meta['session_id'] not in {None, sid}:
                        raise ValueError('mixed sessions')
                    meta['session_id'] = sid
                meta['child'] |= row.get('isSidechain') is True or bool(row.get('agentId')) or bool(row.get('parentSessionId'))
                meta['t3_owned'] |= row.get('originator') in {'T3 Code', 't3', 't3_code'}
                message = row.get('message', {})
                if not isinstance(message, dict):
                    message = {}
                content = message.get('content', [])
                blocks = content if isinstance(content, list) else []
                tool_result = any(isinstance(x, dict) and x.get('type') == 'tool_result' for x in blocks)
                text = [content] if isinstance(content, str) else [
                    x.get('text') for x in blocks if isinstance(x, dict) and x.get('type') == 'text']
                interrupted = any(x in {'[Request interrupted by user]', '[Request interrupted by user for tool use]'}
                                  for x in text if isinstance(x, str))
                if typ == 'user' and not tool_result:
                    turn = row.get('uuid')
                    if isinstance(turn, str) and SESSION_RE.fullmatch(turn):
                        meta['turn_id'], meta['state'] = turn, 'unknown'
                        pending.clear()
                    if interrupted:
                        meta['state'] = 'terminal'
                if typ == 'assistant':
                    if meta['turn_id'] is not None and meta['state'] != 'terminal':
                        meta['state'] = 'active' if bypass is True else 'unknown'
                    if message.get('stop_reason') in {'end_turn', 'stop_sequence', 'max_tokens'}:
                        meta['state'] = 'terminal'
                    for block in blocks:
                        if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('name') in {'AskUserQuestion', 'ExitPlanMode'}:
                            pending.add(block.get('id'))
                if typ == 'user':
                    for block in blocks:
                        if isinstance(block, dict) and block.get('type') == 'tool_result':
                            pending.discard(block.get('tool_use_id'))
                            if meta['turn_id'] is not None and meta['state'] != 'terminal':
                                meta['state'] = 'active' if bypass is True else 'unknown'
                if typ == 'result':
                    meta['state'] = 'terminal'
                if typ in {'user', 'assistant', 'result'} and at is not None:
                    meta['activity_at'] = max(meta['activity_at'] or 0, at)
    if pending and meta['state'] != 'terminal':
        meta['state'] = 'approval'
    elif kind == 'codex' and meta['state'] == 'active' and not never:
        # Exec/apply approval requests are not persisted in Codex rollouts.
        # Liveness alone never distinguishes a tool from a permission dialog.
        meta['state'] = 'unknown'
    return meta


def native_sessions(config, arrival_clock=None):
    specs = config.get('native_sessions', [])
    if not specs:
        return [], [], []
    home = Path.home().resolve()
    roots, gaps, summaries = [], [], []
    for spec in specs:
        kind = spec.get('kind')
        root = Path(os.path.abspath(os.path.expanduser(spec.get('root', ''))))
        relative = root.relative_to(home).parts if home in root.parents else ()
        if (kind not in {'codex', 'claude'} or not relative or
                not re.fullmatch(r'\.' + kind + r'(?:-[A-Za-z0-9_-]+)?', relative[0]) or
                relative[1:] != (('sessions',) if kind == 'codex' else ('projects',)) or
                not below(root, [home]) or spec.get('scope') != 'victor'):
            gaps.append({'reason': 'native-root-scope-rejected'})
            continue
        summary = dict(kind=kind, configured_roots=1, live_processes=0, bound_files=0,
                       eligible=0, terminal=0, approval=0, child=0, t3=0,
                       unknown=0, read_failed=0, truncated=False)
        summaries.append(summary)
        roots.append((spec, root, summary))
    processes, process_gaps = native_processes(config)
    gaps.extend(process_gaps)
    result, identities = [], set()
    for spec, root, summary in roots:
        other_roots = [r for s, r, _ in roots if s['kind'] == spec['kind'] and r != root]
        matching = [p for p in processes if p.get('kind') == spec['kind'] and
                    not (any(below(x, other_roots) for x in p.get('session_files', []) if isinstance(x, str))
                         and not any(below(x, [root]) for x in p.get('session_files', []) if isinstance(x, str)))]
        summary['live_processes'] = len(matching)
        for process in matching:
            paths = [Path(x) for x in process.get('session_files', []) if isinstance(x, str) and below(x, [root])]
            if process.get('parent_session_id') or process.get('ancestor_lane'):
                summary['child'] += 1
                continue
            if process.get('t3_owned'):
                summary['t3'] += 1
                continue
            if not paths and process.get('session_ids'):
                # Claude closes its JSONL between writes. Its explicit resume
                # or session-id flag is an exact current binding, unlike mtime.
                ids = set(process['session_ids'])
                visited = 0
                for parent, dirs, files in os.walk(root, followlinks=False):
                    dirs[:] = [d for d in dirs if d not in {'subagents', 'workflows'} and below(Path(parent) / d, [root])]
                    visited += 1
                    if visited > 2000:
                        summary['truncated'] = True
                        gaps.append({'reason': 'native-session-budget'})
                        break
                    for name in files:
                        sid = SESSION_RE.search(name)
                        if name.endswith('.jsonl') and sid is not None and sid[0] in ids and below(Path(parent) / name, [root]):
                            paths.append(Path(parent) / name)
            # No file-mtime/last-event guess and no historical transcript sweep.
            # Unknown open-file/session binding is an explicit coverage gap.
            if not paths:
                summary['unknown'] += 1
                gaps.append({'reason': 'native-live-session-binding-unknown'})
                continue
            for path in paths[:32]:
                summary['bound_files'] += 1
                try:
                    owner = spec.get('trusted_home_owner')
                    if owner != 'Sats':
                        # Shared/family homes need a root-supplied exact public
                        # binding BEFORE opening any transcript. No blanket read.
                        sid_match = SESSION_RE.search(path.name)
                        sid = sid_match[0] if sid_match else None
                        binding = spec.get('bindings', {}).get(sid, {})
                        if binding.get('scope') != 'victor' or binding.get('recipient') != 'Sats':
                            summary['unknown'] += 1
                            gaps.append({'reason': 'native-positive-scope-binding-missing'})
                            continue
                        owner = 'Sats'
                    meta = native_schema(path, spec['kind'], bypass=process.get('approval_bypass') is True)
                    sid, turn = meta['session_id'], meta['turn_id']
                    filename_id = SESSION_RE.search(path.name)
                    if not sid or filename_id is None or filename_id[0] != sid:
                        raise ValueError('native file binding')
                    if meta['child'] or '/subagents/' in str(path):
                        summary['child'] += 1
                        continue
                    if meta['t3_owned']:
                        summary['t3'] += 1
                        continue
                    if meta['state'] in {'terminal', 'approval'}:
                        summary[meta['state']] += 1
                        continue
                    generation = process.get('generation')
                    if meta['state'] != 'active' or turn is None or not binding_field(generation) or meta['activity_at'] is None:
                        summary['unknown'] += 1
                        gaps.append({'reason': 'native-state-unknown'})
                        continue
                    identity = spec['kind'], sid
                    if identity in identities:
                        summary['unknown'] += 1
                        gaps.append({'reason': 'native-session-binding-conflict'})
                        result = [r for r in result if (r['native_kind'], r['session_id']) != identity]
                        continue
                    identities.add(identity)
                    arrived = arrival_clock() if arrival_clock is not None else None
                    observed = arrived['wall'] if arrived is not None else time.time()
                    digest = hashlib.sha256(generation.encode()).hexdigest()[:16]
                    cpu = process.get('cpu_ticks')
                    resources = dict(generation=digest, counters={'cpu_ticks': cpu}, observed_at=observed) if type(cpu) is int and cpu >= 0 else None
                    result.append(dict(lane='native-' + spec['kind'] + '-' + sid, run='native-' + sid + '-' + turn + '-' + digest,
                                       recipient=owner, status='active', source='native', lanedir=str(root),
                                       session_id=sid, turn_id=turn, native_kind=spec['kind'],
                                       native_generation=digest, native_activity_at=meta['activity_at'],
                                       native_resources=resources,
                                       log=stat_file(path), observed_at=observed,
                                       **({'_arrival_clock': arrived} if arrived is not None else {})))
                    summary['eligible'] += 1
                except (OSError, ValueError, TypeError):
                    summary['read_failed'] += 1
                    gaps.append({'reason': 'native-session-read-failed'})
            if len(paths) > 32:
                summary['truncated'] = True
                gaps.append({'reason': 'native-session-budget'})
    combined = {}
    for summary in summaries:
        target = combined.setdefault(summary['kind'], {'kind': summary['kind']})
        for key, value in summary.items():
            if key == 'kind':
                continue
            target[key] = (target.get(key, False) or value) if type(value) is bool else target.get(key, 0) + value
    return result, gaps, list(combined.values())


def registry_scan(config, roots, rows, gaps):
    """Root-persisted continuation; cached registrations get a read each tick.

    Returning the remaining frontier keeps remote collection read only. A
    bounded metadata cache avoids resetting an established owner's quiet window
    every time its directory is outside the current round-robin batch.
    """
    max_entries = max(1, int(config.get('max_entries', 2000)))
    max_depth = int(config.get('max_depth', 4))
    cursor, cursor_gaps = checked_cursor(config.get('registry_cursor'))
    gaps.extend(cursor_gaps)
    cursor = cursor or {}
    frontier = cursor.get('frontier') or [{'path': str(r), 'depth': 0, 'offset': 0} for r in roots]
    stack = deque(frontier)
    known = set(cursor.get('known', []))
    known.update(r['lanedir'] for r in rows if isinstance(r.get('lanedir'), str))
    probed, seen = set(), 0
    def probe(parent):
        if parent in probed or not below(parent, roots):
            return
        probed.add(parent)
        try:
            row = registry_row(parent)
            if row is not None:
                rows.append(row)
                known.add(str(parent))
            else:
                known.discard(str(parent))
        except (OSError, ValueError, TypeError):
            gaps.append({'reason': 'registry-read-failed'})
    for directory in sorted(known):
        probe(Path(directory))
    started = time.monotonic()
    while stack and seen < max_entries and time.monotonic() - started < 3:
        node = stack.popleft()
        parent = Path(node.get('path', ''))
        depth, offset = node.get('depth', -1), node.get('offset', 0)
        if not below(parent, roots) or type(depth) is not int or not 0 <= depth <= max_depth or type(offset) is not int or offset < 0:
            gaps.append({'reason': 'registry-cursor-rejected'})
            continue
        probe(parent)
        if depth >= max_depth:
            continue
        try:
            with os.scandir(parent) as entries:
                for i, entry in enumerate(entries):
                    if i < offset:
                        continue
                    if seen >= max_entries or time.monotonic() - started >= 3:
                        stack.appendleft({'path': str(parent), 'depth': depth, 'offset': i})
                        break
                    seen += 1
                    if entry.name.startswith('.') or entry.name in {'node_modules', 'venv', '__pycache__', 'Obsidian', '.git'}:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        child = Path(entry.path)
                        probe(child)
                        # Depth-first continuation stores one resume position
                        # per level, rather than an ever-growing breadth queue.
                        stack.appendleft({'path': str(parent), 'depth': depth, 'offset': i + 1})
                        stack.appendleft({'path': str(child), 'depth': depth + 1, 'offset': 0})
                        break
        except FileNotFoundError:
            continue
        except (OSError, ValueError, TypeError):
            gaps.append({'reason': 'registry-read-failed'})
    if stack:
        gaps.append({'reason': 'registry-discovery-budget'})
    cap = max(1, min(512, int(config.get('registry_cache_limit', 512))))
    if len(known) > cap:
        gaps.append({'reason': 'registry-cache-budget'})
    continuation = bounded_cursor(stack, sorted(known)[:cap], gaps)
    return continuation, dict(kind='registry', entries_seen=seen, registered=len(known),
                              cached_probes=len(probed), truncated=bool(stack), cache_truncated=len(known) > len(continuation['known']))


def discover(config, reader=command, arrival_clock=None):
    now = time.time()
    home = Path.home().resolve()
    roots = [Path(os.path.expanduser(r)).resolve() for r in config.get('roots', ['~/work'])]
    # Runtime OS user/home is explicit scope evidence. Do not scan another home.
    if home.name not in config.get('allowed_home_names', ['victor', 'sats']):
        return {'observed_at': now, 'lanes': [], 'gaps': [{'reason': 'home-scope-rejected'}]}
    if config.get('public_metadata_only') is True:
        # Only explicit Sats registrations, public milestones and file stats.
        # Never inherit native transcript or process-argv scans on a shared home.
        allowed = config.get('allowed_recipients')
        if (not isinstance(allowed, list) or not allowed or
                not all(isinstance(name, str) and name in {'Sats', 'sats'} for name in allowed)):
            return {'observed_at': now, 'lanes': [],
                    'gaps': [{'reason': 'positive-victor-scope-required'}]}
        config = dict(config, systemd=False, native_sessions=[], public_process_metadata_only=True)
    if any(not (r == home / 'work' or home / 'work' in r.parents) for r in roots):
        return {'observed_at': now, 'lanes': [], 'gaps': [{'reason': 'root-scope-rejected'}]}
    rows, gaps = [], []
    if config.get('systemd', True):
        try:
            units, unit_gaps = systemd_lanes(reader, config)
            rows.extend(units)
            gaps.extend(unit_gaps)
        except (OSError, ValueError):
            gaps.append({'reason': 'systemd-unavailable'})
    continuation, registry_coverage = registry_scan(config, roots, rows, gaps)
    # Registry explicitly terminal always wins over an active systemd snapshot.
    registered, conflicts = {}, set()
    for row in rows:
        if row.get('source') != 'registry':
            continue
        key = row.get('lane'), row.get('run')
        previous = registered.get(key)
        if previous and any(previous.get(k) != row.get(k) for k in ('recipient', 'lanedir', 'unit', 'owner_thread_id')):
            conflicts.add(key)
            continue
        # Explicit terminal/blocked wins over a stale active copy.
        if previous and previous.get('status') != 'active':
            continue
        registered[key] = row
    merged = {}
    for row in rows:
        if row.get('source') != 'systemd':
            continue
        key = row.get('lane'), row.get('run')
        previous = merged.get(key)
        if previous and (previous.get('legacy_binding') or row.get('legacy_binding')):
            if any(previous.get(k) != row.get(k) for k in ('unit', 'invocation_id', 'recipient', 'lanedir')):
                conflicts.add(key)
        merged[key] = row
    active_units = {r.get('unit'): r for r in rows if r.get('source') == 'systemd' and r.get('status') == 'active'}
    for key, row in registered.items():
        actual = merged.get(key)
        if actual and actual.get('legacy_binding') and row.get('status') == 'active':
            if any(actual.get(k) != row.get(k) for k in ('recipient', 'lanedir', 'unit', 'owner_thread_id')):
                conflicts.add(key)
        merged[key] = dict(merged.get(key, {}), **row)
    result = []
    for key, row in merged.items():
        if key in conflicts:
            gaps.append({'reason': 'conflicting-owner-registration'})
            continue
        if not isinstance(row.get('lanedir'), str) or not below(row['lanedir'], roots):
            gaps.append({'reason': 'lane-path-scope-rejected'})
            continue
        if row.get('status') != 'active' or row.get('pending_approval') is True:
            continue
        if config.get('allowed_recipients') is not None and row.get('recipient') not in config['allowed_recipients']:
            gaps.append({'reason': 'registered-owner-scope-rejected'})
            continue
        if row.get('source') == 'registry' and row.get('unit') and config.get('systemd', True):
            actual = active_units.get(row['unit'])
            if actual is None or actual.get('run') != row.get('run'):
                gaps.append({'reason': 'registered-unit-not-confirmed-active'})
                continue
        if (row.get('parent') or row.get('parentThreadId')) and row.get('owner') is not True:
            continue
        if not all(isinstance(row.get(k), str) and 0 < len(row[k]) <= 200 and row[k].strip() and not any(ord(c) < 32 for c in row[k]) for k in ('lane', 'run', 'recipient')):
            gaps.append({'reason': 'exact-owner-binding-missing'})
            continue
        directory = Path(os.path.abspath(row['lanedir']))
        try:
            if not below(directory / 'lane.log', roots) or not below(directory / 'MILESTONES.log', roots):
                raise OSError('scope')
            started_at = timestamp(row.get('started_at'))
            raw_run = re.fullmatch(r'([0-9]{9,11})-([0-9]{9})', row['run'])
            if raw_run:
                started_at = int(raw_run[1]) + int(raw_run[2]) / 1e9
            ms = milestone(directory / 'MILESTONES.log', row['run'], row['lane'], started_at)
            if ms['terminal']:
                continue
            if not all(below(directory / name, roots) for name in
                       (row['lane'] + '.stdout', row['lane'] + '.stderr')):
                raise OSError('scope')
            log = progress_log(directory, row['lane'])
            arrived = arrival_clock() if arrival_clock is not None else None
            observed_at = arrived['wall'] if arrived is not None else time.time()
            try:
                delivery = delivery_metadata(directory, roots)
            except (OSError, ValueError):
                delivery = None
                gaps.append({'reason': 'delivery-metadata-unavailable'})
            result.append(dict(row, lanedir=str(directory), milestone_at=ms['at'],
                               milestone_token=ms['token'], milestone_mtime=ms['mtime'],
                               log=log, observed_at=observed_at, delivery=delivery,
                               **({'_arrival_clock': arrived} if arrived is not None else {})))
        except (OSError, ValueError):
            gaps.append({'reason': 'lane-metadata-read-failed'})
    native_config = dict(config, _owning_units=[r['unit'] for r in rows
                                              if r.get('source') == 'systemd' and isinstance(r.get('unit'), str)])
    native, native_gaps, native_coverage = native_sessions(native_config, arrival_clock)
    result.extend(native)
    gaps.extend(native_gaps)
    return {'observed_at': time.time(), 'lanes': result, 'gaps': gaps,
            'registry_cursor': continuation, 'coverage': [registry_coverage, *native_coverage]}


if __name__ == '__main__':
    import sys
    try:
        options = globals().get('_collector_options')
        if options is None:
            options = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        print(json.dumps(discover(options), separators=(',', ':')))
    except Exception:
        print(json.dumps({'observed_at': time.time(), 'lanes': [], 'gaps': [{'reason': 'collector-failed'}]}))
        sys.exit(1)
