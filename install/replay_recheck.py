#!/usr/bin/env python3
"""Recheck each replay entry of the reviewed requeue triage against its thread, read-only, right before replay.

    replay_recheck.py MANIFEST MCP_CALL SCRATCH    prints one JSON object {replay, answered, unverified}; exit 0

An entry replays only while its thread has no answer after the ask it carries (the entry's answer_check: host,
thread_id, ask_position). An answer is the watchdog's: sats_stall_asks.answers(), so a delegated-task completion,
a server or provider wake and a system notice leave the ask open (the live base cb8a6cc0's rule). Answered, or
unreadable, it is archived instead (SOL-7). The check keys on the
user-answer position, never on settled state: a9acdeb1 is settled only because the 19:39 sweep settled it over
an unanswered Victor ask (notice-delay-rca-20261023, TRIAGE.md), so settled says nothing about an answer.

The thread is read with t3_thread_read through the reviewed mcp_call.py MCP_CALL, loaded as a module with its PACK
pointed at SCRATCH: the lane's mcp_call copy pattern, so its result file lands in the install record and never in
the live pack. SCRATCH must be a new, real directory, and the result file is read only as a regular file.
NOTICE_PACKAGE_THREAD_READER, for the rehearsal and tests only, names a program that answers the same read
(argv: host, arguments JSON) from a fixture.
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

PAGES = 10
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/sats-stall-watchdog/src'))
from sats_stall_asks import answers  # noqa: E402 - the candidate watchdog's answer rule, one definition


def mcp_reader(mcp_call, scratch):
    def read(host, arguments):
        fixture = os.environ.get('NOTICE_PACKAGE_THREAD_READER')
        if fixture:
            out = subprocess.run([fixture, host, json.dumps(arguments)], capture_output=True, text=True, timeout=60, check=True)
            return json.loads(out.stdout)
        spec = importlib.util.spec_from_file_location('mcp_call_recheck', mcp_call)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PACK = str(scratch)
        result = scratch / 'mcp-last-result.json'
        if result.exists() or result.is_symlink():
            result.unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            module.main(['--host', host, 'call', 't3_thread_read', json.dumps(arguments)])
        if not stat.S_ISREG(os.lstat(result).st_mode):
            raise ValueError('result is not a regular file')
        reply = json.loads(result.read_text())
        if reply.get('isError'):
            raise ValueError('t3_thread_read returned an error')
        return json.loads(reply['content'][0]['text'])
    return read


def answered(read, check):
    """True when an answer (answers()) follows the ask's position in its thread."""
    after = check['ask_position']
    for _ in range(PAGES):
        page = read(check['host'], {'threadId': check['thread_id'], 'view': 'messages', 'afterPosition': after,
                                    'limit': 50, 'maxCharsPerItem': 1, 'runLimit': 1})
        if (page.get('thread') or {}).get('threadId') != check['thread_id']:
            raise ValueError('the read named another thread')
        items = page.get('items') or []
        if any(answers(i) and i.get('position', -1) > check['ask_position'] for i in items):
            return True
        if not page.get('hasMore') or not items:
            return False
        after = items[-1]['position']
    raise ValueError('more than %d pages after the ask' % PAGES)


def main(argv):
    manifest, mcp_call, scratch = json.loads(Path(argv[0]).read_text()), Path(argv[1]), Path(argv[2])
    if mcp_call.is_symlink() or not mcp_call.is_file():
        raise SystemExit('%s: not a regular file' % mcp_call)
    scratch.mkdir(mode=0o700)  # new and real: an existing path or link fails here
    read = mcp_reader(mcp_call, scratch)
    report = {'replay': [], 'answered': [], 'unverified': []}
    for entry in manifest['entries']:
        if entry['decision'] != 'replay':
            continue
        check = entry.get('answer_check')
        try:
            if not check:
                raise ValueError('no answer_check in the triage')
            report['answered' if answered(read, check) else 'replay'].append(entry['file'])
        except (Exception, SystemExit) as error:  # noqa: BLE001 - any failure archives the entry instead
            report['unverified'].append({'file': entry['file'], 'reason': (type(error).__name__ + ': ' + str(error))[:160]})
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
