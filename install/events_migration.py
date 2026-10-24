#!/usr/bin/env python3
"""Apply, roll back or rehearse the notice-package-20261023 item-6 events migration on an asks.sqlite3.

    events_migration.py --lib DIR up DB          per-ask key (sats_stall_asks.upgrade_events), one transaction
    events_migration.py --lib DIR down DB        old key (sats_stall_asks.downgrade_events), one transaction
    events_migration.py --lib DIR rehearse DB    up then down on a COPY, each step verified; refuses the live file

DIR holds the sats_stall_asks.py whose functions run, so install, rollback and rehearsal share one implementation.
Each step runs under BEGIN IMMEDIATE with the watchdog's own pragmas (journal TRUNCATE, synchronous FULL) and
never VACUUMs or checkpoints. Output is one JSON object; exit 0 only when every check passed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

LIVE = Path.home() / '.local/state/sats-stall-watchdog/asks.sqlite3'


def snapshot(db):
    """Everything the migration may touch: schema rows, events rows in rowid order, row counts, integrity."""
    tables = [name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    events = db.execute('SELECT rowid, id, thread, generation, state, data FROM events ORDER BY rowid').fetchall()
    return {'schema': db.execute('SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name').fetchall(),
            'events_sha256': hashlib.sha256(json.dumps(events).encode()).hexdigest(), 'events': len(events),
            'counts': {name: db.execute('SELECT count(*) FROM "%s"' % name).fetchone()[0] for name in tables},
            'migrations': [r[0] for r in db.execute('SELECT name FROM migrations ORDER BY name')],
            'integrity': db.execute('PRAGMA integrity_check').fetchone()[0]}


def read(path):
    db = connect(path)
    try:
        return snapshot(db)
    finally:
        db.close()


def connect(path):
    db = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    db.execute('PRAGMA journal_mode=TRUNCATE')
    db.execute('PRAGMA synchronous=FULL')
    return db


def step(asks, path, direction):
    db = connect(path)
    try:
        before = snapshot(db)
        db.execute('BEGIN IMMEDIATE')
        try:
            applied = asks.events_per_ask(db) != (direction == 'up')
            if applied:
                (asks.upgrade_events if direction == 'up' else asks.downgrade_events)(db, time.time())
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK')
            raise
        after = snapshot(db)
        parked = after['counts'].get('events_parked', 0) - before['counts'].get('events_parked', 0)
        sql = next(row[3] for row in after['schema'] if row[1] == 'events')
        checks = {'integrity_ok': after['integrity'] == 'ok',
                  'schema': sql == (asks.EVENTS_V2 if direction == 'up' else asks.EVENTS_V1),
                  'rows_kept': after['events'] + parked == before['events'],
                  'other_tables_unchanged': {k: v for k, v in after['counts'].items() if k not in ('events', 'events_parked', 'migrations')}
                  == {k: v for k, v in before['counts'].items() if k not in ('events', 'events_parked', 'migrations')}}
        if direction == 'up':
            checks['events_rows_identical'] = after['events_sha256'] == before['events_sha256'] or not applied
        return {'direction': direction, 'applied': applied, 'parked': parked, 'before': before, 'after': after,
                'checks': checks, 'ok': all(checks.values())}
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--lib', required=True)
    parser.add_argument('command', choices=('up', 'down', 'rehearse'))
    parser.add_argument('db')
    args = parser.parse_args(argv)
    sys.path.insert(0, str(Path(args.lib).resolve()))
    import sats_stall_asks as asks
    path = Path(args.db)
    if path.is_symlink() or not path.is_file():
        raise SystemExit('%s: not a regular file' % path)
    report = {'db': str(path.resolve()), 'module': asks.__file__,
              'module_sha256': hashlib.sha256(Path(asks.__file__).read_bytes()).hexdigest()}
    if args.command == 'rehearse':
        if path.resolve() == LIVE.resolve() or (LIVE.exists() and os.path.samefile(path, LIVE)):
            raise SystemExit('rehearse runs on a copy, never on the live asks.sqlite3')
        original = read(path)
        up = step(asks, path, 'up')
        down = step(asks, path, 'down')
        restored = read(path)
        report.update(up={k: up[k] for k in ('applied', 'parked', 'checks', 'ok')},
                      down={k: down[k] for k in ('applied', 'parked', 'checks', 'ok')},
                      original={k: original[k] for k in ('events', 'events_sha256', 'counts', 'migrations', 'integrity')},
                      after_up={k: up['after'][k] for k in ('events', 'events_sha256', 'counts', 'migrations', 'integrity')},
                      restored={k: restored[k] for k in ('events', 'events_sha256', 'counts', 'migrations', 'integrity')},
                      round_trip_identical=restored == original)
        report['ok'] = up['ok'] and down['ok'] and report['round_trip_identical']
    else:
        result = step(asks, path, args.command)
        report.update({k: result[k] for k in ('direction', 'applied', 'parked', 'checks', 'ok')},
                      before={k: result['before'][k] for k in ('events', 'events_sha256', 'counts', 'migrations')},
                      after={k: result['after'][k] for k in ('events', 'events_sha256', 'counts', 'migrations')})
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
