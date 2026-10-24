"""Bounded, model-free MCP metadata reads. No raw responses enter logs or state."""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from sats_stall_collector import timestamp

ACTIVE = {'preparing', 'queued', 'starting', 'running', 'waiting'}
TERMINAL = {'idle', 'completed', 'interrupted', 'failed', 'cancelled', 'rolled_back',
            'done', 'settled', 'archived', 'blocked'}
ID = re.compile(r'^[A-Za-z0-9:_%.-]{1,200}$')


class Gap(Exception):
    """Only a fixed safe reason is exposed, never an underlying exception."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Gap('mcp-redirect-refused')


class MCP:
    def __init__(self, base, token_file, timeout=5, call_budget=48, seconds=40):
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.path not in {'', '/'} or parsed.query or parsed.fragment:
            raise Gap('mcp-base-invalid')
        self.url = base.rstrip('/') + '/mcp'
        self.token_file = Path(token_file).expanduser()
        self.timeout, self.calls = timeout, call_budget
        self.deadline = time.monotonic() + seconds
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-06-18'}
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.http_status = None

    def rpc(self, method, params, notification=False):
        if self.calls <= 0 or time.monotonic() >= self.deadline:
            raise Gap('mcp-budget')
        self.calls -= 1
        headers = dict(self.headers)
        # Only existing token files are read; bearer exists in memory only.
        try:
            with self.token_file.open('r') as handle:
                token = handle.read(4097).strip()
        except OSError:
            raise Gap('mcp-token-unavailable') from None
        if not token or len(token) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in token):
            raise Gap('mcp-token-invalid')
        headers['Authorization'] = 'Bearer ' + token
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params}
        if not notification:
            payload['id'] = 1
        try:
            request = urllib.request.Request(self.url, data=json.dumps(payload).encode(), headers=headers, method='POST')
            with self.opener.open(request, timeout=min(self.timeout, max(.1, self.deadline-time.monotonic()))) as response:
                self.http_status = response.status
                raw = response.read(2_000_001)
                session = response.headers.get('Mcp-Session-Id')
                if method == 'initialize' and session:
                    if not re.fullmatch(r'[A-Za-z0-9_-]{1,250}', session):
                        raise Gap('mcp-session-invalid')
                    self.headers['Mcp-Session-Id'] = session
        except (OSError, ValueError, urllib.error.URLError):
            raise Gap('mcp-transport-unavailable') from None
        finally:
            headers.clear()
            token = None
        if len(raw) > 2_000_000:
            raise Gap('mcp-response-budget')
        if notification:
            return {}
        try:
            body = raw.decode('utf-8')
            if not body.lstrip().startswith('{'):
                rows = [x[5:].strip() for x in body.splitlines() if x.startswith('data:')]
                body = rows[-1]
            reply = json.loads(body)
            if not isinstance(reply, dict) or reply.get('error') or 'result' not in reply:
                raise Gap('mcp-rpc-error')
            return reply['result']
        except (ValueError, IndexError, KeyError, UnicodeError):
            raise Gap('mcp-response-invalid') from None

    def initialize(self):
        self.rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'sats-stall-watchdog', 'version': '1'}})
        self.rpc('notifications/initialized', {}, notification=True)

    def call(self, name, arguments):
        result = self.rpc('tools/call', {'name': name, 'arguments': arguments})
        if not isinstance(result, dict) or result.get('isError') is True:
            raise Gap('mcp-tool-error')
        if isinstance(result.get('structuredContent'), dict):
            return result['structuredContent']
        for content in result.get('content', []):
            if content.get('type') == 'text':
                try:
                    row = json.loads(content['text'])
                    if isinstance(row, dict):
                        return row
                except (ValueError, KeyError):
                    continue
        raise Gap('mcp-tool-shape')


def pages(client, name, field, arguments, max_pages=12):
    cursor, visited = 0, set()
    for _ in range(max_pages):
        if cursor in visited:
            raise Gap('mcp-cursor-cycle')
        visited.add(cursor)
        result = client.call(name, dict(arguments, cursor=cursor, limit=100))
        rows = result.get(field)
        if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
            raise Gap('mcp-list-shape')
        yield rows
        nxt = result.get('nextCursor')
        if nxt is None:
            return
        if type(nxt) is not int or nxt < 0:
            raise Gap('mcp-cursor-invalid')
        cursor = nxt
    raise Gap('mcp-page-budget')


def eligibility(thread, require_pending=True):
    if thread.get('archived') is True or thread.get('settled') is True or thread.get('snoozed') is True or thread.get('status') in TERMINAL:
        return 'skip'
    # Missing parent information cannot establish top-level ownership.
    if 'parentThreadId' not in thread:
        return 'unknown'
    if thread['parentThreadId'] is not None or thread.get('relationshipToParent') == 'subagent':
        return 'skip'
    count = thread.get('pendingRequestCount')
    if require_pending and (type(count) is not int or count < 0):
        return 'unknown'
    if (type(count) is int and count > 0) or thread.get('pendingApproval') is True:
        return 'blocked'
    return 'active' if thread.get('status') in ACTIVE else 'unknown'


def metadata(listed, response, host, observed_at):
    """Metadata only. Item text, titles, tool args and outputs are never retained.

    Only independent timeline evidence counts; generic thread.updatedAt and
    run status churn can be caused by our own steering request.
    """
    thread = response.get('thread')
    thread_id = listed.get('threadId')
    if not ID.fullmatch(str(thread_id or '')) or not isinstance(thread, dict) or thread.get('threadId') != thread_id:
        raise Gap('mcp-thread-identity')
    decision = eligibility(dict(listed, **thread))
    if decision != 'active':
        return {'key': 't3:' + host + ':' + thread_id, 'kind': 't3', 'host': host, 'thread_id': thread_id, 'eligible': False, 'known': decision != 'unknown', 'reason': decision}
    run = thread.get('activeRunId') or thread.get('latestRunId')
    if not ID.fullmatch(str(run or '')):
        raise Gap('mcp-run-missing')
    items = response.get('items')
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise Gap('mcp-activity-shape')
    activity = []
    for item in items:
        # user/steering/request events include watchdog sends; no heartbeat.
        typ = item.get('type', '')
        if typ not in {'assistant_message', 'tool_call', 'tool_result', 'reasoning', 'assistant_delta', 'plan', 'proposed_plan', 'command_execution', 'file_change', 'mcp_tool_call', 'web_search', 'reasoning_summary'}:
            continue
        if item.get('visibility') == 'inherited':
            continue
        at = next((timestamp(item.get(k)) for k in ('updatedAt', 'completedAt', 'createdAt', 'timestamp', 'at') if timestamp(item.get(k)) is not None), None)
        ident = item.get('itemId') or item.get('id')
        if at is None or at > observed_at + 5 or not ID.fullmatch(str(ident or '')):
            raise Gap('mcp-activity-timestamp')
        activity.append({'id': ident, 'at': at, 'run': item.get('runId'), 'type': typ, 'status': item.get('status')})
    updated = timestamp(thread.get('updatedAt'))
    if updated is None or updated > observed_at + 5:
        raise Gap('mcp-thread-timestamp')
    return {'key': 't3:' + host + ':' + thread_id, 'kind': 't3', 'host': host,
            'thread_id': thread_id, 'run': run, 'known': True, 'eligible': True,
            'activity': activity, 'thread_updated_at': updated, 'observed_at': observed_at,
            'pending': 0, 'status': thread['status']}


def scope_allowed(project_id, thread_id, scope_projects=None, owner_bindings=None, require_owner_binding=False):
    if (not isinstance(scope_projects, list) or
            not all(isinstance(p, str) and ID.fullmatch(p) for p in scope_projects) or
            project_id not in scope_projects):
        return False
    if not require_owner_binding:
        return True
    binding = owner_bindings.get(thread_id) if isinstance(owner_bindings, dict) else None
    return (isinstance(binding, dict) and binding.get('scope') == 'victor' and
            isinstance(binding.get('recipient'), str) and binding['recipient'] in {'Sats', 'sats'})


def collect(client, host, max_pages=12, max_reads=20, scope_projects=None, read_offset=0, arrival_clock=None,
            owner_bindings=None, require_owner_binding=False):
    """Only explicit project IDs authorize thread reads; absent scope is unbound."""
    observations, gaps = [], []
    candidates = []
    allowed_projects = (set(scope_projects) if isinstance(scope_projects, list)
                        and all(isinstance(p, str) and ID.fullmatch(p) for p in scope_projects)
                        else set())
    unbound_projects = 0
    client.next_read_offset = read_offset
    try:
        client.initialize()
        project_ids = []
        for page in pages(client, 't3_project_list', 'projects', {}, max_pages):
            for project in page:
                project_id = project.get('id')
                if not ID.fullmatch(str(project_id or '')):
                    raise Gap('mcp-project-identity')
                if project_id in allowed_projects:
                    project_ids.append(project_id)
                else:
                    unbound_projects += 1
        seen = set()
        for project_id in project_ids:
            for page in pages(client, 't3_thread_list', 'threads', {'projectId': project_id, 'includeSubagents': False}, max_pages):
                for thread in page:
                    tid = thread.get('threadId')
                    if not ID.fullmatch(str(tid or '')):
                        raise Gap('mcp-thread-identity')
                    if tid in seen:
                        continue
                    seen.add(tid)
                    if not scope_allowed(project_id, tid, scope_projects, owner_bindings, require_owner_binding):
                        gaps.append({'host': host, 'reason': 'mcp-owner-scope-unbound'})
                        continue
                    decision = eligibility(thread, require_pending=False)
                    if decision != 'active':
                        if decision == 'unknown':
                            gaps.append({'host': host, 'reason': 'mcp-owner-status-unknown'})
                        continue
                    count = thread.get('itemCount')
                    if type(count) is not int or count < 0:
                        gaps.append({'host': host, 'reason': 'mcp-item-count-unknown'})
                        continue
                    candidates.append(dict(thread, project_id=project_id))
    except Gap as error:
        gaps.append({'host': host, 'reason': str(error)})
    if unbound_projects:
        gaps.append({'host': host, 'reason': 'mcp-project-unbound', 'count': unbound_projects})
    if candidates:
        offset = read_offset % len(candidates)
        ordered = candidates[offset:] + candidates[:offset]
        reads = 0
        for thread in ordered[:max_reads]:
            args = {'threadId': thread['threadId'], 'view': 'activity', 'limit': 20, 'runLimit': 3, 'maxCharsPerItem': 1}
            if thread['itemCount'] > 20:
                args['afterPosition'] = thread['itemCount'] - 21
            reads += 1
            try:
                response = client.call('t3_thread_read', args)
                arrived = arrival_clock() if arrival_clock is not None else None
                observed_at = arrived['wall'] if arrived is not None else time.time()
                row = metadata(thread, response, host, observed_at)
                row['project_id'] = thread['project_id']
                if arrived is not None:
                    row['_arrival_clock'] = arrived
                observations.append(row)
            except Gap as error:
                gaps.append({'host': host, 'reason': str(error)})
                if str(error) == 'mcp-budget':
                    break
        client.next_read_offset = (offset + reads) % len(candidates)
        if len(candidates) > reads:
            gaps.append({'host': host, 'reason': 'mcp-read-budget'})
    return observations, gaps
