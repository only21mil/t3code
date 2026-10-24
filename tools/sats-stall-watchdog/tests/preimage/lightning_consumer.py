"""Durable P5b core and CLI for Lightning's model-backed SendToAgent consumer.

The existing consumer supplies trusted launch bindings and exact native target
IDs. The CLI reserves an attempt, then records the model's native tool result.
It calls no app tool, starts no model, and never sends a notice itself.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import importlib.machinery
import json
import os
from pathlib import Path
import re
import secrets
import sys
import time

# Use the installed producer's canonical pure helpers, including launcher start
# notices. Loading this module runs no hook or transport, guarded by __main__.
_loader = importlib.machinery.SourceFileLoader('p5b_notifier', str(Path.home()/'.local/bin/sats-completion-notify'))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
notice = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(notice)


def forward(payload, bindings, targets, state_dir, send, sleep=time.sleep):
    """Forward unchanged text to exactly one approved owner, with durable cap 3.

    `bindings` is keyed by (lane, derived_run_key), retaining earlier launches.
    `bindings` and `targets` come from the owner, never the webhook body. Sender
    authentication is the existing ingress's responsibility. Unbound legacy
    payloads remain with Lightning's existing consumer branch.
    """
    binding = bindings.get((payload.get('lane'), payload.get('run')))
    expected = notice.required_notice(payload, payload.get('event_kind'),
               payload.get('review_round'), payload.get('notice_occurrence'), binding=binding)
    if payload != expected:
        raise ValueError('prepared message/identity differs from owner binding')
    target = targets.get(binding['recipient'])
    if not isinstance(target, str) or not target:
        raise ValueError('approved native target missing')
    directory = Path(state_dir)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    event_id = expected['event_id']
    fd = os.open(directory/(event_id+'.lock'), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        body_file = directory/(event_id+'.payload.json')
        record_file = directory/(event_id+'.state.json')
        if body_file.exists():
            if json.loads(body_file.read_text()) != expected:
                raise ValueError('event identity reused for different bytes')
        else:
            notice.write_private(body_file, expected)
        record = json.loads(record_file.read_text()) if record_file.exists() else {
                  'event_id':event_id,'target':target,'attempts':0,'state':'FAILED','reported':False}
        if record['target'] != target:
            raise ValueError('native target changed during event')
        if record['state'] == 'DELIVERED':
            return record  # Pending receiver reply never justifies another send.
        for number in range(record['attempts']+1, 4):
            sleep(notice.RETRY_DELAYS[number-1])
            record.update(attempts=number,state='FAILED',http_status=None)
            notice.write_private(record_file,record)  # reservation survives uncertain call/crash
            try:
                status = send(target, expected['message'], binding['priority'])
            except Exception:
                status = 0  # never expose exception text, which may carry secrets
            record.update(http_status=status,state='DELIVERED' if notice.accepted_status(status) else 'FAILED')
            notice.write_private(record_file,record)
            if record['state']=='DELIVERED':
                return record
        return record
    finally:
        os.close(fd)


def read_failures(bindings, notifier_state, consumer_state):
    """Read retained failures for Lightning's existing consumer, without sends.

    The owner supplies trusted bindings and its two existing private state dirs.
    The owner invokes this at its normal consumer/reconciliation turns; it is
    not a watcher. Interrupted reservations count, including a third call with
    no result. Only exact bound notices carry identity fields. Invalid retained
    records return value-free diagnostics and cannot hide later failures.
    """
    failures = []
    for directory, step, pattern in [(Path(notifier_state)/'outbox', 'webhook', '*.json'),
                                     (Path(consumer_state), 'native', '*.payload.json')]:
        for body_file in sorted(directory.glob(pattern)):
            if step == 'webhook' and body_file.name.endswith('.acceptance.json'):
                continue
            stem = body_file.name[:-5] if step == 'webhook' else body_file.name[:-13]
            lock_file = directory/(stem+'.lock')
            if not lock_file.exists():
                continue  # No send reservation yet.
            fd = None
            try:
                fd = os.open(lock_file, os.O_RDONLY)
                fcntl.flock(fd, fcntl.LOCK_SH)
                if not body_file.exists():
                    continue  # Accepted webhook moved to sent while waiting.
                payload = json.loads(body_file.read_text())
                if not isinstance(payload, dict):
                    raise ValueError('invalid retained object')
                binding = bindings.get((payload.get('lane'), payload.get('run')))
                if binding is None:
                    continue
                try:
                    expected = notice.required_notice(payload, payload.get('event_kind'),
                        payload.get('review_round'), payload.get('notice_occurrence'), binding=binding)
                    if payload != expected:
                        raise ValueError('retained notice differs from owner binding')
                except (ValueError, TypeError, KeyError):
                    failures.append({'reader':'Lightning', 'delivery_step':step,
                        'state':'FAILED', 'disposition':'binding_mismatch'})
                    continue  # Do not expose payload values or abort reconciliation.
                if step == 'webhook':
                    acceptance = directory/(payload['event_id']+'.acceptance.json')
                    if acceptance.exists():
                        proof = json.loads(acceptance.read_text())
                        if notice.accepted_status(proof.get('http_status')) and proof.get('body_sha256') == hashlib.sha256(body_file.read_bytes()).hexdigest():
                            continue
                    ledger_file = directory/(stem+'.attempts.jsonl')
                    rows = [json.loads(x) for x in ledger_file.read_text().splitlines()] if ledger_file.exists() else []
                    used = sum(x.get('phase') == 'reserved' or 'phase' not in x for x in rows)
                    last = rows[-1] if rows and rows[-1].get('phase') != 'reserved' else {}
                    disposition = last.get('disposition', 'uncertain')
                    status = last.get('http_status')
                else:
                    record_file = directory/(stem+'.state.json')
                    if not record_file.exists():
                        continue
                    record = json.loads(record_file.read_text())
                    if record['state'] == 'DELIVERED':
                        continue
                    used = record['attempts']
                    status = record.get('http_status')
                    disposition = 'uncertain' if status is None or record.get('uncertain') else 'native_failed'
                if used:
                    failures.append({'event_id':payload['event_id'], 'lane':payload['lane'],
                        'run':payload['run'], 'recipient':binding['recipient'], 'reader':'Lightning',
                        'delivery_step':step, 'state':'FAILED', 'attempts':used,
                        'capped':used >= 3, 'http_status':status, 'disposition':disposition})
            except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
                failures.append({'reader':'Lightning', 'delivery_step':step,
                    'state':'FAILED', 'disposition':'record_invalid'})
            finally:
                if fd is not None:
                    os.close(fd)
    return failures


def load_bindings(path):
    """Owner-held file: one launch binding or a list retaining pending launches."""
    values = json.loads(Path(path).read_text())
    values = [values] if isinstance(values, dict) else values
    if not isinstance(values, list):
        raise ValueError('owner binding registry required')
    bindings = {}
    for binding in values:
        if not isinstance(binding, dict) or not notice.valid_binding(
                binding, binding.get('lane'), binding.get('run'), False):
            raise ValueError('invalid owner binding')
        key = (binding['lane'], binding['run'])
        if key in bindings:
            raise ValueError('duplicate owner binding')
        bindings[key] = binding
    return bindings


def validate_payload(payload, bindings):
    if not isinstance(payload, dict):
        raise ValueError('notice object required')
    binding = bindings.get((payload.get('lane'), payload.get('run')))
    expected = notice.required_notice(payload, payload.get('event_kind'),
        payload.get('review_round'), payload.get('notice_occurrence'), binding=binding)
    if expected != payload:
        raise ValueError('prepared message/identity differs from owner binding')
    return binding


def event_lock(state_dir, event_id):
    if not isinstance(event_id, str) or not re.fullmatch('[0-9a-f]{64}', event_id):
        raise ValueError('full event ID required')
    directory = Path(state_dir)
    # Owner initializes this exact directory after pre-live review. No guessed
    # existing integration path and no implicit mkdir in a read-only command.
    if not directory.is_dir():
        raise ValueError('owner consumer state missing')
    fd = os.open(directory/(event_id+'.lock'), os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def prepare_delivery(payload, bindings, target, state_dir):
    """Persist exact payload and reserve ONE native attempt before model sends.

    target is the model's owner-table lookup, never a payload field. The first
    reservation pins it. An unresolved reservation blocks concurrent sends and
    restart replay until its actual result or uncertainty is explicitly recorded.
    """
    binding = validate_payload(payload, bindings)
    if not isinstance(target, str) or not target.strip():
        raise ValueError('approved native target required')
    event_id = payload['event_id']
    directory = Path(state_dir)
    fd = event_lock(directory, event_id)
    try:
        body_file = directory/(event_id+'.payload.json')
        record_file = directory/(event_id+'.state.json')
        if body_file.exists():
            if json.loads(body_file.read_text()) != payload:
                raise ValueError('event identity reused with different bytes')
        else:
            notice.write_private(body_file, payload)
        record = json.loads(record_file.read_text()) if record_file.exists() else {
            'event_id':event_id, 'target':target, 'attempts':0,
            'state':'FAILED', 'reported':False}
        if record['target'] != target or record['event_id'] != event_id:
            raise ValueError('native target or identity changed')
        if record['state'] == 'DELIVERED':
            return {'event_id':event_id, 'state':'DELIVERED', 'send':False}
        if record.get('uncertain'):
            return {'event_id':event_id, 'state':'UNCERTAIN', 'send':False}
        if record.get('pending'):
            return {'event_id':event_id, 'state':'PENDING', 'send':False,
                    'attempt':record['attempts'], 'reservation':record['reservation']}
        if type(record['attempts']) is not int or not 0 <= record['attempts'] <= 3:
            raise ValueError('invalid attempt ledger')
        if record['attempts'] >= 3:
            return {'event_id':event_id, 'state':'CAPPED', 'send':False}
        attempt = record['attempts']+1
        reservation = secrets.token_hex(16)  # Non-secret attempt correlation ID.
        record.update(attempts=attempt, state='FAILED', http_status=None,
                      pending=True, reservation=reservation)
        notice.write_private(record_file, record)
        return {'event_id':event_id, 'state':'READY', 'send':True,
                'attempt':attempt, 'reservation':reservation,
                'target':target, 'recipient':binding['recipient'],
                'message':payload['message'], 'priority':binding['priority']}
    finally:
        os.close(fd)


def record_delivery(event_id, outcome, attempt, reservation, receipt, bindings, state_dir):
    """Record a model-observed native tool result for its reserved attempt.

    Receipt is a non-secret projection: tool, event_id, target, priority,
    success, and source_receipt, plus optional uncertain=true. The controller
    must authenticate the original tool receipt separately for E2E acceptance.
    """
    if outcome not in {'ok','fail'} or type(attempt) is not int:
        raise ValueError('invalid delivery result')
    directory = Path(state_dir)
    fd = event_lock(directory, event_id)
    try:
        body = json.loads((directory/(event_id+'.payload.json')).read_text())
        binding = validate_payload(body, bindings)
        if body['event_id'] != event_id:
            raise ValueError('event identity changed')
        record_file = directory/(event_id+'.state.json')
        record = json.loads(record_file.read_text())
        if record['event_id'] != event_id or record['attempts'] != attempt or record.get('reservation') != reservation:
            raise ValueError('stale or unknown attempt')
        if not isinstance(receipt, dict) or set(receipt)-{
                'tool','event_id','target','priority','success','source_receipt','uncertain'}:
            raise ValueError('invalid non-secret receipt projection')
        if (receipt.get('tool') != 'SendToAgent' or receipt.get('event_id') != event_id
                or receipt.get('target') != record['target']
                or receipt.get('priority') is not binding['priority']
                or receipt.get('success') is not (outcome == 'ok')
                or not isinstance(receipt.get('source_receipt'), str)
                or not receipt['source_receipt'].strip()
                or type(receipt.get('uncertain', False)) is not bool
                or outcome == 'ok' and receipt.get('uncertain', False)):
            raise ValueError('receipt differs from reserved native call')
        if not record.get('pending'):
            if record.get('receipt') == receipt and record.get('outcome') == outcome:
                return record  # Repeated recording is idempotent, never a send.
            raise ValueError('attempt result already recorded')
        notice.write_private(directory/(event_id+f'.attempt-{attempt}.receipt.json'), receipt)
        record.update(pending=False, outcome=outcome, receipt=receipt,
                      uncertain=receipt.get('uncertain', False),
                      state='DELIVERED' if outcome == 'ok' else 'FAILED',
                      http_status=200 if outcome == 'ok' else 0)
        notice.write_private(record_file, record)
        return record
    finally:
        os.close(fd)


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', required=True, help='Independent owner launch binding file')
    parser.add_argument('--consumer-state', required=True, help='Owner-selected durable state directory')
    commands = parser.add_subparsers(dest='command', required=True)
    read = commands.add_parser('read-failures', help='Read-only retained-failure JSON')
    read.add_argument('--notifier-state', required=True)
    prepare = commands.add_parser('prepare-delivery', help='Reserve once; JSON payload on stdin')
    prepare.add_argument('--target-id', required=True, help='Model lookup in approved owner target table')
    record = commands.add_parser('record-delivery', help='Record result; non-secret receipt projection on stdin')
    record.add_argument('event_id')
    record.add_argument('outcome', choices=['ok','fail'])
    record.add_argument('--attempt', type=int, required=True)
    record.add_argument('--reservation', required=True)
    args = parser.parse_args(argv)
    bindings = load_bindings(args.bindings)
    if args.command == 'read-failures':
        # Actually enumerate both directories; missing/inaccessible is not empty.
        for directory in [Path(args.notifier_state)/'outbox', Path(args.consumer_state)]:
            with os.scandir(directory) as entries:
                list(entries)
        output = {'reader':'Lightning', 'state_access':'observed',
                  'failures':read_failures(bindings, args.notifier_state, args.consumer_state)}
    elif args.command == 'prepare-delivery':
        output = prepare_delivery(json.load(sys.stdin), bindings, args.target_id, args.consumer_state)
    else:
        output = record_delivery(args.event_id, args.outcome, args.attempt,
            args.reservation, json.load(sys.stdin), bindings, args.consumer_state)
    print(json.dumps(output))
    return 0


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    os.umask(0o077)
    try:
        raise SystemExit(cli())
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        print(json.dumps({'reader':'Lightning','state':'BLOCKED','disposition':'command_invalid'}))
        raise SystemExit(2)
