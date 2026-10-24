#!/usr/bin/env python3
"""Run the frozen real hook CLI with only its external transport replaced.

All state is confined to tests/.tmp. No credential, network or subprocess call
is permitted. Independent local enrollment still uses the real frozen helper.
WATCHDOG_TEST_HOOK names another frozen hook under preimage/ (the live copy);
WATCHDOG_TEST_RUN_ID is the recipient run id an accepted POST names.
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


FIXTURES = Path(__file__).resolve().parent / 'preimage'


def load_hook():
    path = (FIXTURES / os.environ.get('WATCHDOG_TEST_HOOK', 'sats-completion-notify')).resolve()
    path.relative_to(FIXTURES)
    loader = importlib.machinery.SourceFileLoader('inert_real_notifier', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    hook = importlib.util.module_from_spec(spec)
    loader.exec_module(hook)
    return hook


def forbidden(*args, **kwargs):
    raise AssertionError('credential/network/process access forbidden in hook fixture')


def main():
    directory = Path(os.environ['WATCHDOG_TEST_ROOT']).resolve()
    directory.relative_to(Path(__file__).resolve().parent / '.tmp')
    hook = load_hook()
    hook.configure_state(str(directory / 'hook-state'))
    hook.OWNER_BINDINGS_REGISTRY = directory / 'bindings.json'
    hook.OWNER_BINDINGS_HELPER = FIXTURES / 'p5b-owner-bindings-refresh'
    hook.webhook = lambda **kwargs: ('inert://fixture', 'public-fixture', 'fixture')
    hook.time.sleep = lambda seconds: None
    hook.WEBHOOK_SPACING = 0  # the live hook's per-URL spacing; absent from the older preimage

    def post(url, key, body, event_id, **kwargs):
        payload = json.loads(body)
        assert key == 'public-fixture'
        assert event_id == payload['event_id']
        with (directory / 'posts.jsonl').open('a') as output:
            output.write(json.dumps(payload, sort_keys=True) + '\n')
        if os.environ.get('WATCHDOG_TEST_RUN_ID') and isinstance(kwargs.get('diagnostics'), dict):
            kwargs['diagnostics']['recipient_run_id'] = os.environ['WATCHDOG_TEST_RUN_ID']
        return int(os.environ.get('WATCHDOG_TEST_STATUS', '200'))

    hook._post = post
    socket.socket = forbidden
    subprocess.Popen = forbidden
    return hook.main()


if __name__ == '__main__':
    sys.exit(main())
