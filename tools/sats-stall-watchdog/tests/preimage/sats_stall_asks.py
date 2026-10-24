"""Open human asks in T3 threads: one decision or blocker notice per ask message.

T3 orchestrators ask Victor in final-message prose, so the stall detector,
which ignores terminal, settled and archived threads, never saw them
(t3-pending-decisions-sweep-20261018, Victor GO 17:02 CT 2026-10-18).

An ask is an assistant message in a top-level thread of an allowed project
that carries a NEEDS-VICTOR line or a decision ID, or, as the final message of
a thread that is not running, asks Victor a question or for approval. It is
open until a later user message answers it or the thread is settled or
archived after it was written. Each open ask gets one notice, keyed by host,
thread id and message id. Assistant text is read in memory; only the notice
line and the per-ask evidence file carry an excerpt, never the watchdog log.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import time

from sats_stall_collector import timestamp
from sats_stall_mcp import ACTIVE, Gap, ID, pages

FAMILY_HOSTS = {'m3mbp'}   # Mason's laptop: never read
TEXT_LIMIT = 20000         # characters per read; at most CONTINUATIONS more reads per message
CONTINUATIONS = 3
WINDOW = 40                # timeline items read on a thread's first scan
MAX_ATTEMPTS = 3
BACKOFF_MIN, BACKOFF_MAX = 600, 86400  # seconds between by-ID reads of an unlisted thread
MESSAGE_LIMIT = 300
EXCERPT_LIMIT = 1500

MARKER_RE = re.compile(r'^[ \t>*_-]*(?:\d+[.)][ \t]*)?[*_]*NEEDS-VICTOR\b.*$', re.M)
# The notice shape "<thread|lane> BLOCKED <words> <path>" or a BLOCKED verdict line; final messages only.
BLOCKED_LINE_RE = re.compile(r'^[ \t>*_-]*(?:[A-Za-z0-9:_%./-]{3,200}[ \t]+)?[*_]*BLOCKED\b.*$', re.M)
DECISION_ID_RE = re.compile(r'\bDECISION-[A-Z0-9][A-Z0-9_-]*')
DECISION_FOR_RE = re.compile(r'\bdecisions? (?:for|from) (?:you|victor)\b', re.I)
FENCE_RE = re.compile(r'^[ \t]*```.*?^[ \t]*```[^\n]*$', re.M | re.S)
INLINE_CODE_RE = re.compile(r'`[^`\n]*`')
NEXT_STEPS_RE = re.compile(r'^[ \t>#*_]*next steps\b', re.I | re.M)
ACTIONS = r'(?:unlock|approve|confirm|decide|choose|pick|reply|answer|sign|log ?in|say|give|send|plug|ok\b|run\b)'
PROSE = [re.compile(p, re.I) for p in (
    r"\b(?:need|needs|needed|awaiting|await|wait(?:ing)?\s+(?:on|for))\s+(?:your|victor'?s)\s+"
    r"(?:ok\b|okay|go\b|go-ahead|approval|sign-?off|decision|call\b|answer|choice|input|confirmation|reply)",
    r"\bwaiting\s+(?:on|for)\s+(?:you|victor)\b",
    r"\b(?:do you want|would you like|want me to|should i|shall i|can you|could you|will you|are you ok with)\b[^\n?]{0,200}\?",
    r"\b(?:tell me|let me know)\b",
    r"\b(?:once|when|after|if)\s+(?:victor|you)\s+" + ACTIONS,
    r"\b(?:victor|you)\s+(?:must|needs? to|has to|have to|should)\s+" + ACTIONS,
    r"\b(?:please|kindly)\s+" + ACTIONS,
    r"\b(?:calls?|choices?|questions?|asks?|approvals?)\s+for\s+(?:you|victor)\b",
    r"\b(?:approval|sign-?off)\s+(?:is\s+)?(?:needed|required)\b",
    r"\bneeds?\s+(?:a\s+)?(?:victor|human)\s+(?:decision|approval|action|ok\b|go\b)",
)]
# A negation earlier in the same sentence ("Nothing is waiting on Victor") cancels a prose match.
NEGATION_RE = re.compile(r"\b(?:nothing|not|no|never|none|no longer|without)\b|n't\b", re.I)
# Provider message ids can run to several hundred characters.
MESSAGE_ID_RE = re.compile(r'^[A-Za-z0-9:_%.-]{1,1000}$')
# A 24+ character token mixing upper case, lower case and digits looks like a key; it is masked.
TOKENISH_RE = re.compile(r'[A-Za-z0-9_+=-]{16,}')
SECRET_PREFIX_RE = re.compile(r'^(?:sk-|ghp_|gho_|ghs_|github_pat_|glpat-|xox[abpr]-|AKIA|ASIA|crsr_|AIza)')


def mask(text):
    def one(match):
        word = match.group(0)
        if SECRET_PREFIX_RE.match(word) or (len(word) >= 24 and re.search(r'[A-Z]', word)
                                            and re.search(r'[a-z]', word) and re.search(r'[0-9]', word)):
            return '[masked]'
        return word
    return TOKENISH_RE.sub(one, text)


def one_line(text, limit):
    text = ' '.join(''.join(c if c.isprintable() else ' ' for c in text).split())
    return text if len(text) <= limit else text[:limit - 3] + '...'


def classify(text, final):
    """(kind, excerpt, marker lines) for an ask, else None.

    Markers count in any assistant message. Prose counts only in a final
    message, outside code and outside a trailing Next steps offer list."""
    if not isinstance(text, str) or not text.strip():
        return None
    body = FENCE_RE.sub('', text)
    markers = [line.strip(' \t>*_-') for line in MARKER_RE.findall(body)]
    if not markers and final:
        markers = [line.strip(' \t>*_-') for line in BLOCKED_LINE_RE.findall(body)]
    if not markers:
        markers = [line.strip() for line in body.splitlines() if DECISION_ID_RE.search(line) or any(
                   not NEGATION_RE.search(re.split(r'[.!?;]\s', line[:m.start()])[-1]) for m in DECISION_FOR_RE.finditer(line))]
    markers = [mask(one_line(line, EXCERPT_LIMIT)) for line in markers]
    excerpt = None
    if markers:
        excerpt = '\n'.join(markers)
    elif final:
        prose = INLINE_CODE_RE.sub('', body)
        cut = NEXT_STEPS_RE.search(prose)
        prose = prose[:cut.start()] if cut else prose
        for pattern in PROSE:
            for found in pattern.finditer(prose):
                sentence = re.split(r'[.!?;\n]\s', prose[:found.start()])[-1]
                if NEGATION_RE.search(sentence):
                    continue
                start = prose.rfind('\n', 0, found.start()) + 1
                end = prose.find('\n', found.end())
                excerpt = prose[start:end if end >= 0 else len(prose)].strip()
                break
            if excerpt is not None:
                break
    if excerpt is None:
        return None
    scope = excerpt if markers else body
    kind = 'blocker' if re.search(r'\bBLOCKED\b', scope) else 'decision'
    return kind, mask(excerpt)[:EXCERPT_LIMIT], markers


def allowed_projects(projects, ids=None, roots=None, exclude=None):
    """Explicit project IDs, plus live projects whose workspace is inside a Victor home root."""
    ids = set(ids) if isinstance(ids, list) else set()
    exclude = set(exclude) if isinstance(exclude, list) else set()
    homes = [PurePosixPath(r) for r in roots if isinstance(r, str) and r.startswith('/')] if isinstance(roots, list) else []
    result = []
    for project in projects:
        pid = project.get('id')
        if not ID.fullmatch(str(pid or '')) or pid in exclude or project.get('deletedAt'):
            continue
        root = project.get('workspaceRoot')
        inside = False
        if isinstance(root, str) and root.startswith('/') and '..' not in PurePosixPath(root).parts:
            path = PurePosixPath(root)
            inside = any(path == home or home in path.parents for home in homes)
        if pid in ids or inside:
            result.append(pid)
    return result


class AskState:
    """Per-thread read cursor and per-ask delivery record, committed before transport."""

    def __init__(self, directory=None):
        if directory is not None:
            Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(Path(directory) / 'asks.sqlite3') if directory is not None else ':memory:', timeout=5)
        self.db.execute('PRAGMA journal_mode=TRUNCATE')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS threads (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS asks (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
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

    def get(self, table, key):
        row = self.db.execute('SELECT data FROM %s WHERE %s=?' % (table, 'key' if table == 'threads' else 'id'), (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, table, key, value):
        self.db.execute('INSERT OR REPLACE INTO %s VALUES (?,?)' % table, (key, json.dumps(value, separators=(',', ':'))))

    def rows(self, table, prefix):
        column = 'key' if table == 'threads' else 'id'
        return [(k, json.loads(v)) for k, v in self.db.execute(
            'SELECT %s, data FROM %s WHERE %s >= ? AND %s < ?' % (column, table, column, column), (prefix, prefix + '￿'))]

    def close(self):
        self.db.close()


def signature(thread):
    return [thread.get('updatedAt'), thread.get('itemCount'), thread.get('status'),
            thread.get('settled'), thread.get('settledAt'), thread.get('archived')]


def full_text(client, thread_id, item):
    text = item.get('text') if isinstance(item.get('text'), str) else ''
    offset = item.get('nextTextOffset') if item.get('textTruncated') else None
    for _ in range(CONTINUATIONS):
        if type(offset) is not int or not ID.fullmatch(str(item.get('itemId') or '')):
            break
        reply = client.call('t3_thread_read', {'threadId': thread_id, 'itemId': item['itemId'], 'textOffset': offset,
                                               'maxCharsPerItem': TEXT_LIMIT, 'runLimit': 1})
        rows = reply.get('items')
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict) or not isinstance(rows[0].get('text'), str):
            raise Gap('ask-text-shape')
        text += rows[0]['text']
        offset = rows[0].get('nextTextOffset') if rows[0].get('textTruncated') else None
    return text, offset is None


def read_thread(client, thread_id, after):
    """(thread metadata, message items, complete) after timeline position `after`."""
    args = {'threadId': thread_id, 'view': 'messages', 'limit': 50, 'runLimit': 1, 'maxCharsPerItem': TEXT_LIMIT}
    if type(after) is int and after >= 0:
        args['afterPosition'] = after
    items, meta = [], None
    for _ in range(3):
        reply = client.call('t3_thread_read', args)
        meta, page = reply.get('thread'), reply.get('items')
        if (not isinstance(meta, dict) or meta.get('threadId') != thread_id or not isinstance(page, list) or
                not all(isinstance(i, dict) and type(i.get('position')) is int for i in page)):
            raise Gap('ask-thread-shape')
        items += page
        if not reply.get('hasMore') or not page:
            return meta, items, True
        args['afterPosition'] = page[-1]['position']
    return meta, items, False


def find_asks(client, host, thread_id, meta, items, emit):
    """Open asks in this window, plus the asks a later user reply or settle overrides."""
    found, overridden = [], []
    status = meta.get('status')
    settled_at = timestamp(meta.get('settledAt')) if meta.get('settled') or meta.get('archived') else None
    if (meta.get('settled') or meta.get('archived')) and settled_at is None:
        settled_at = float('inf')  # settled at an unknown time: treat as after every ask
    for index, item in enumerate(items):
        if item.get('type') != 'assistant_message' or item.get('visibility') == 'inherited':
            continue
        final = index == len(items) - 1 and status not in ACTIVE and item.get('status') == 'completed'
        text, complete = full_text(client, thread_id, item)
        if not complete:
            # A partial text read fails the whole scan: the thread's marker stays and nothing in it sends this tick.
            raise Gap('ask-text-truncated')
        verdict = classify(text, final)
        if verdict is None:
            continue
        message_id = item.get('messageId') or item.get('itemId')
        # Legacy threads carry no run ids; a stable per-thread run keeps the hook identity fixed.
        run = item.get('runId') or meta.get('latestRunId') or 't3-thread-' + hashlib.sha256(thread_id.encode()).hexdigest()[:32]
        at = timestamp(item.get('updatedAt'))
        if not MESSAGE_ID_RE.fullmatch(str(message_id or '')) or not MESSAGE_ID_RE.fullmatch(str(run or '')) or at is None:
            emit('gap', host=host, reason='ask-identity-invalid')
            continue
        ask = {'host': host, 'thread_id': thread_id, 'message_id': message_id, 'run': run, 'at': at,
               'kind': verdict[0], 'excerpt': verdict[1], 'markers': verdict[2], 'position': item['position'],
               'ask_id': 'ask-' + hashlib.sha256('|'.join((host, thread_id, message_id)).encode()).hexdigest()[:40]}
        answered = any(later.get('type') == 'user_message' for later in items[index + 1:])
        (overridden if answered or (settled_at is not None and settled_at >= at) else found).append(ask)
    return found, overridden


def notice_line(ask, title):
    head = ask['markers'][0] if ask['markers'] else 'NEEDS-VICTOR %s: %s' % (ask['kind'], ask['excerpt'])
    if ask['thread_id'] not in head:
        head = ask['thread_id'] + ' ' + head
    extra = ' (+%d more)' % (len(ask['markers']) - 1) if len(ask['markers']) > 1 else ''
    return one_line('T3 %s %s%s' % (ask['host'], head, extra), MESSAGE_LIMIT)


def write_evidence(path, record):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name('.' + path.name + '.' + str(os.getpid()))
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(json.dumps(record, indent=1) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def tick_host(client, host, state, emit, send, scope, now, max_notices=10, evidence_dir=None,
              max_reads=25, max_pages=12, max_known=4, deadline=None, seed=None):
    """Scan one host's T3 threads and deliver open asks. Returns notices attempted.

    send=None is a dry run: asks are logged as detected and nothing is written."""
    if host in FAMILY_HOSTS or not isinstance(scope, dict):
        emit('gap', host=host, reason='ask-scope-unbound')
        return 0
    dry = send is None
    listed, complete_listing, allowed = {}, False, []
    try:
        client.initialize()
        projects = [p for page in pages(client, 't3_project_list', 'projects', {}, max_pages) for p in page]
        allowed = allowed_projects(projects, scope.get('ids'), scope.get('roots'), scope.get('exclude'))
        complete_listing = True
        for project_id in allowed:
            try:
                for page in pages(client, 't3_thread_list', 'threads', {'projectId': project_id, 'includeSubagents': False}, max_pages):
                    for thread in page:
                        tid = thread.get('threadId')
                        if not ID.fullmatch(str(tid or '')):
                            emit('gap', host=host, reason='ask-thread-identity')
                            continue
                        if thread.get('parentThreadId') is not None or thread.get('relationshipToParent') == 'subagent':
                            continue
                        listed[tid] = dict(thread, projectId=project_id)
            except Gap as error:
                # Other projects still scan; only a complete listing may treat a thread as missing.
                emit('gap', host=host, reason=str(error))
                complete_listing = False
                if str(error) == 'mcp-budget':
                    break
    except Gap as error:
        emit('gap', host=host, reason=str(error))
    prefix = 'thread:' + host + ':'
    saved = {key[len(prefix):]: value for key, value in state.rows('threads', prefix)}
    if not dry:
        # Every listed thread becomes known at once, so archiving it later cannot hide it.
        unseen = [tid for tid in listed if tid not in saved]
        with state.transaction():
            for tid in unseen:
                saved[tid] = {'position': None, 'sig': None, 'project_id': listed[tid]['projectId']}
                state.put('threads', prefix + tid, saved[tid])
    # T3 never lists archived threads. Seeded ids (top-level threads read from each host's database)
    # and known threads that leave a complete listing are read by ID on a capped backoff.
    for tid in seed or []:
        if isinstance(tid, str) and ID.fullmatch(tid) and tid not in saved and tid not in listed:
            saved[tid] = {'position': None, 'next_check': 0, 'seeded': True}
    changed = sorted((t for tid, t in listed.items() if saved.get(tid, {}).get('sig') != signature(t)),
                     key=lambda t: str(t.get('updatedAt')), reverse=True)
    missing = sorted((tid for tid, value in saved.items() if tid not in listed and not value.get('out_of_scope')
                      and value.get('next_check', 0) <= now),
                     key=lambda tid: saved[tid].get('next_check', 0)) if complete_listing else []
    work = [(t['threadId'], t) for t in changed] + [(tid, None) for tid in missing[:max_known]]
    allowed_set = set(allowed)
    current = {tid for tid, t in listed.items() if saved.get(tid, {}).get('sig') == signature(t)}
    held = set()  # threads whose read or text read failed this tick: nothing in them is sent until a later tick
    reads = 0
    for tid, listing in work:
        if reads >= max_reads:
            emit('gap', host=host, reason='ask-read-budget')
            break
        reads += 1
        old = saved.get(tid) or {}
        backoff = min(max(old.get('backoff', 0) * 2, BACKOFF_MIN), BACKOFF_MAX)
        after = old.get('position')
        try:
            if after is None:
                item_count = (listing or {}).get('itemCount')
                if type(item_count) is not int:
                    probe = client.call('t3_thread_read', {'threadId': tid, 'view': 'messages', 'limit': 1, 'runLimit': 1, 'maxCharsPerItem': 1})
                    item_count = (probe.get('thread') or {}).get('itemCount')
                after = item_count - WINDOW - 1 if type(item_count) is int else None
            meta, items, complete = read_thread(client, tid, after)
            in_scope = meta.get('projectId') in allowed_set and meta.get('parentThreadId') is None
            found, overridden = find_asks(client, host, tid, meta, items, emit) if in_scope else ([], [])
        except Gap as error:
            emit('gap', host=host, reason=str(error))
            held.add(tid)
            if str(error) == 'mcp-budget':
                break
            if listing is None and not dry:
                with state.transaction():
                    state.put('threads', prefix + tid, dict(old, backoff=backoff, next_check=now + backoff))
            continue
        # Leave an unfinished final message to be read again.
        last = items[-1] if items else None
        position = old.get('position', after)
        for item in items:
            if item is last and (item.get('status') != 'completed' or meta.get('status') in ACTIVE):
                break
            position = item['position']
        record = {'sig': signature(listing) if listing and complete else None, 'position': position,
                  'checked': now, 'project_id': meta.get('projectId'),
                  'title': mask(one_line(str(meta.get('title') or ''), 120))}
        if listing is None:
            record['backoff'] = BACKOFF_MIN if items else backoff
            record['next_check'] = now + record['backoff']
        if not in_scope:
            record['out_of_scope'] = True
        if dry:
            for ask in found:
                emit('ask-detected', host=host, thread_id=tid, message_id=ask['message_id'], kind=ask['kind'])
            continue
        settled_at = timestamp(meta.get('settledAt')) if meta.get('settled') or meta.get('archived') else None
        if (meta.get('settled') or meta.get('archived')) and settled_at is None:
            settled_at = float('inf')
        replies = [i['position'] for i in items if i.get('type') == 'user_message']
        with state.transaction():
            # Reconcile asks stored on an earlier tick: a later reply or settle closes them before any send.
            for ask_id, prior in state.rows('asks', 'ask-'):
                if (prior.get('host') == host and prior.get('thread_id') == tid and prior.get('state') in ('pending', 'attempting')
                        and (any(r > prior['position'] for r in replies) or (settled_at is not None and settled_at >= prior['at']))):
                    prior['state'] = 'overridden'
                    state.put('asks', ask_id, prior)
            for ask in overridden:
                prior = state.get('asks', ask['ask_id'])
                if prior and prior.get('state') in ('pending', 'attempting'):
                    prior['state'] = 'overridden'
                    state.put('asks', ask['ask_id'], prior)
            for ask in found:
                if state.get('asks', ask['ask_id']) is None:
                    ask.update(state='pending', attempts=0, title=record['title'], project_id=record['project_id'])
                    state.put('asks', ask['ask_id'], ask)
            state.put('threads', prefix + tid, record)
        if complete:
            # Current only once a complete read's reconcile has committed. A partial page read leaves its
            # asks to the pre-send reconcile, which reads on from the saved position.
            current.add(tid)
    if dry:
        return 0
    # A later reply in any thread read this tick has already marked its asks overridden.
    pending = sorted((value for _, value in state.rows('asks', 'ask-') if value.get('host') == host and value.get('state') in ('pending', 'attempting')),
                     key=lambda a: a['at'])
    count = 0
    refreshed = {}  # thread id -> (user reply positions, settled_at, complete), or None after a failed read
    for ask in pending:
        tid = ask['thread_id']
        if tid in held:
            continue
        if tid not in current and count < max_notices:
            # Not fully read this tick (backoff, a failed or a partial read): reconcile before any send.
            # Scans have applied every reply up to the thread's saved position, so one read from there
            # serves every pending ask in the thread.
            if tid not in refreshed:
                start = (state.get('threads', prefix + tid) or {}).get('position')
                if type(start) is not int:
                    start = min(a['position'] for a in pending if a['thread_id'] == tid)
                try:
                    meta, items, complete = read_thread(client, tid, start)
                except Gap as error:
                    emit('gap', host=host, reason=str(error))
                    refreshed[tid] = None
                else:
                    settled_at = timestamp(meta.get('settledAt')) if meta.get('settled') or meta.get('archived') else None
                    if (meta.get('settled') or meta.get('archived')) and settled_at is None:
                        settled_at = float('inf')
                    refreshed[tid] = ([i['position'] for i in items if i.get('type') == 'user_message'], settled_at, complete)
                    if not complete:
                        emit('gap', host=host, reason='ask-reconcile-partial')
            if refreshed[tid] is None:
                continue
            replies, settled_at, complete = refreshed[tid]
            if any(r > ask['position'] for r in replies) or (settled_at is not None and settled_at >= ask['at']):
                with state.transaction():
                    ask['state'] = 'overridden'
                    state.put('asks', ask['ask_id'], ask)
                continue
            if not complete:
                continue  # a reply may sit past this read; a later tick reads on
        if count >= max_notices:
            emit('gap', host=host, reason='ask-notice-budget')
            break
        if deadline is not None and time.monotonic() >= deadline:
            emit('gap', host=host, reason='ask-time-budget')
            break
        count += 1
        evidence = Path(evidence_dir) / (ask['ask_id'] + '.json')
        write_evidence(evidence, {key: ask[key] for key in ('ask_id', 'host', 'thread_id', 'project_id', 'title', 'message_id',
                                                             'run', 'kind', 'at', 'markers', 'excerpt')}
                       | {'link': 't3-thread://v1/' + ask['thread_id']})
        plan = dict(ask, message=notice_line(ask, ask.get('title')), evidence=str(evidence))
        with state.transaction():
            ask['attempts'] += 1
            ask['state'] = 'attempting'
            state.put('asks', ask['ask_id'], ask)
        try:
            receipt = send(plan)
        except Exception:
            receipt = {'accepted': False, 'reason': 'transport-exception'}
        receipt = receipt if isinstance(receipt, dict) else {}
        accepted = receipt.get('accepted') is True
        fields = {k: receipt.get(k) for k in ('event_id', 'http_status', 'sats_receipt', 'recipient_run_id',
                                              'delivery_failure', 'reason') if receipt.get(k) is not None}
        with state.transaction():
            ask['state'] = 'sent' if accepted else ('failed' if ask['attempts'] >= MAX_ATTEMPTS else 'pending')
            ask['receipt'] = fields
            state.put('asks', ask['ask_id'], ask)
        emit('ask-notice', host=host, thread_id=ask['thread_id'], message_id=ask['message_id'], ask_id=ask['ask_id'],
             kind=ask['kind'], state=ask['state'], attempts=ask['attempts'], **fields)
    return count
