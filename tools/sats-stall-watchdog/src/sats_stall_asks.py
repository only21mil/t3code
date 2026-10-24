"""Work generations and open human asks in T3 threads: Sats hears START, BLOCKED, DONE and URGENT once each.

T3 orchestrators ask Victor in final-message prose, so the stall detector,
which ignores terminal, settled and archived threads, never saw them
(t3-pending-decisions-sweep-20261018, Victor GO 17:02 CT 2026-10-18).

Victor GO 3:18 PM CT 2026-10-20 (t3-watchdog-r5-install-20261020): a notice is
keyed on host:threadId, durable generation and event state, never on a run or
turn. Sats gets START, BLOCKED (NEEDS-VICTOR included), DONE and URGENT. START,
DONE and URGENT go at most once per generation; BLOCKED goes once per ask, keyed
on the ask's decision ID when its ask lines carry one, else on its marker lines,
so a new ask sends while a re-wake repeating or rewording the same ask does not
(notice-package-20261023 item 6). An ask whose decision IDs, or else marker
lines, were all carried by asks already noticed in the generation is a
restatement and sends nothing (the live needs-victor fix, cb8a6cc0, whose
'BLOCKED:<digest>' rows this module reads as its own). FAILED and CANCELED keep
their own event state in the key and reach Sats with the BLOCKED kind. Status,
replies, milestones, stalls and prose asks send nothing.

A generation is one piece of work. Its origin is an accepted user message in a
top-level thread: the first one, a Victor answer after BLOCKED, FAILED or
CANCELED, or a new message after DONE, its DONE reply included. A message while
the work is unfinished is a steer and joins it. A re-wake starts a run with no
user message, so it never opens one. Each origin and each (thread, generation,
event state, ask) is a unique row, claimed in the transaction that commits the
scan, before any send.

A generation's DONE is its final reply when that reply leads with DONE, or its
last reply that does, when every reply after it restates the DONE (keeps_done):
it ends on a plain paragraph, not a quote, list item or colon-opened block,
whose last sentence is exactly a whole-work DONE ("The research stays DONE.",
DONE_KEPT_RE), and each other clause of it is settled. A clause is settled when
it names no open or new work, or a negative quantifier opens it ("Nothing is
pending."), and it names nothing unfinished (still, yet, future, sequence,
condition, exception, a question); any other negated clause is unfinished, and
any present participle counts as open work, so an unlisted word drops the DONE
rather than keeping a false one. It is claimed a minute after that reply's turn
ends; any other later reply supersedes it as progress.
Threads known before this round start from a baseline generation 0, so their
history sends nothing.

An ask is an assistant message in a top-level thread of an allowed project
that carries a NEEDS-VICTOR line or a decision ID, or, as the final message of
a thread that is not running, asks Victor a question or for approval. It is
open until a later reply answers it (answers()) or the thread is settled or
archived after it was written. A delegated-task completion, a server or
provider wake and a system notice are artifacts, not replies (cb8a6cc0). A
NEEDS-VICTOR marker, a BLOCKED line, a bold **BLOCKED** in a final message or a
"decision for you" line is a BLOCKED, each ask its own (notice-package-20261023
items 5 and 6); markers count inside fenced and inline code too. A line that only
names the markers asks nothing (LIVE-2): no colon or spaced dash labels the
marker names, the line asks nothing, and the names are joined by and/or or a
detection predicate follows them ("... lines count anywhere"), or the decision
phrase is quoted. Any other marker line asks. A final message that leads with FAILED or
CANCELED is that event. Other asks stay local records. Assistant text is read
in memory; only the notice line and the per-event evidence file carry an
excerpt, never the watchdog log.

A thread's own terminal notice (sats-pm-visible-swarm § T3 terminal notice)
is posted inside the turn, so a marker ask waits while its turn runs, then the
send's thread_notice check under the hook's occurrence lock decides: delivered
records the event without a send, queued or in flight waits, anything else
claims the event for the generation (t3-terminal-notice-20261020). A delivered
notice covers only the asks it carried: the turn's one ask; with several asks,
those whose complete decision ID its message names, or, when it names none, each
ask that one sentence of the message carries: the sentence holds no negation,
it and one line of the ask hold each other as an unbroken phrase of three or
more words with the marker words dropped from both, that line holds every path
the sentence names, and no other ask of the turn matches that sentence. Each
other ask of the turn still sends its own BLOCKED, so a generic notice
("BLOCKED: needs Victor") covers none.
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
TURN_GRACE = 60            # seconds after a turn stops before its asks are decided

# Markers count wherever they stand, fenced or inline code included: MBP 64539631 posted its 28 asks inside a
# text fence (notice-package-20261023 item 5). A backtick may open the line or the token.
MARKER_RE = re.compile(r'^[ \t>*_`-]*(?:\d+[.)][ \t]*)?[*_`]*NEEDS-VICTOR\b.*$', re.M)
# The notice shape "<thread|lane> BLOCKED <words> <path>", "Closed as BLOCKED" or a BLOCKED verdict line; final
# messages only. A negation before the token ("not BLOCKED") disqualifies it.
BLOCKED_LINE_RE = re.compile(r'^[ \t>*_`-]*(?:(?i:closed[ \t]+as)[ \t]+|[A-Za-z0-9:_%./-]{3,200}[ \t]+)?[*_`]*(BLOCKED)\b.*$', re.M)
# A bold BLOCKED inside a final message's line: "The reviewed result is **BLOCKED**" (F-D 7237c08a). A table row
# reports other work's state and never counts.
INLINE_BLOCKED_RE = re.compile(r'(\*\*|__)BLOCKED\1')
# A final message whose first line leads with FAILED or CANCELED, in the same notice shape.
TERMINAL_LINE_RE = re.compile(r'^[ \t>*_-]*(?:[A-Za-z0-9:_%./-]{3,200}[ \t]+)?[*_]*(FAILED|CANCEL+ED)\b')
# A reply whose first line leads with DONE, in the same notice shape, is the generation's own DONE.
DONE_LINE_RE = re.compile(r'^[ \t>*_-]*(?:[A-Za-z0-9:_%./-]{3,200}[ \t]+)?[*_]*(DONE)\b')
# A later reply keeps that DONE only when it restates it as a claim and says nothing of unfinished work (SOL-1, review
# rounds 1-3; keeps_done). The claim is the last sentence of the reply's last Markdown block outside fenced code, and
# that block is a plain paragraph: no quote, list item, heading or table row, and not opened by a block that ends in a
# colon (a template, "It is false that:"). Its lines join as Markdown joins them, so a sentence runs on across a line
# break. The sentence is exactly a whole-work DONE: the whole work as subject (the objective, research, work, task, job,
# project, goal, lane, brief, package, assignment, review, repair, delivery or migration, "all work", "the whole work",
# everything), is, stays or remains (still or now allowed), DONE in any case, now and "and settled" allowed after it.
# "The objective is DONE and settled.", "The research stays DONE." (Kimi, mini 3e9f5d46). A part ("Phase 1 is DONE."),
# a condition, exception or negation in that sentence, a code span or quote in it, are no claim.
DONE_KEPT_RE = re.compile(r'^[*_]*(?:(?:(?:all[ \t]+(?:of[ \t]+)?)?(?:the|this|our|my)[ \t]+(?:whole[ \t]+|entire[ \t]+)?|all[ \t]+)?'
                          r'(?:objective|research|work|task|job|project|goal|lane|brief|package|assignment|review|repair|delivery|migration)'
                          r'|everything)[ \t]+(?:is|stays|remains)(?:[ \t]+(?:still|now))?[ \t]+[*_]*DONE[*_]*(?:[ \t]+now)?'
                          r'(?:[ \t]+and[ \t]+settled)?[ \t]*[.!]?[*_]*[ \t]*$', re.I)
# Every other clause of that reply must be settled: it names no open or new work (OPEN_WORK_RE) unless a negative
# quantifier opens it ("Nothing is pending.", "No remaining items."), and it names nothing that is unfinished whatever
# the negation (UNFINISHED_RE: still, yet, again, future, sequence, condition, exception, obligation; or a question).
# A clause under any other negation ("Phase 2 is not finished.", "No tests passed.") is unfinished. Any present
# participle counts as ongoing work, so a synonym the lists miss fails toward no DONE, never toward a false one.
OPEN_WORK_RE = re.compile(r"\b(?!(?:no|some|any|every)?thing\b|morning\b|evening\b|during\b|string\b)\w+ing\b|"
                          r"\b(?:pending|remain\w*|left|open\w*|outstanding|underway|under[ \t]+way|in[ \t]+(?:progress|flight|the[ \t]+works)|"
                          r"on[ \t]+deck|queued|scheduled|unfinished|incomplete|partial\w*|half|mostly|almost|nearly|wip|todos?|to-?do|tbd|"
                          r"start\w*|begin\w*|began|begun|kick\w*[ \t]+off|launch\w*|resum\w*|restart\w*|re-?open\w*|continu\w*|proceed\w*|"
                          r"re-?runs?|retr(?:y|ies|ied)|red(?:o|oes|id|one)|follow\w*|blocked|blockers?|fail\w*|wait\w*|await\w*|"
                          r"need\w*|requir\w*|actions?|new|more|further|else|chang\w*|due|red)\b|\b\d+[ \t]*(?:of|/)[ \t]*\d+\b", re.I)
UNFINISHED_RE = re.compile(r"\?|\b(?:still|yet|again|will|shall|about[ \t]+to|to[ \t]+(?:come|follow)|soon|shortly|later|tomorrow|tonight|"
                           r"overnight|noon|afternoon|(?:mon|tues|wednes|thurs|fri|satur|sun)day|next|then|afterwards|until|till|unless|"
                           r"except|but|however|although|though|if|once|when|whenever|assuming|provided|must|should|ha(?:ve|s)[ \t]+to|"
                           r"so[ \t]+far|for[ \t]+now|meanwhile)\b|['’]ll\b", re.I)
NEGATIVE_QUANTIFIER_RE = re.compile(r'^[ \t*_]*(?:there[ \t]+(?:is|are|was|were)[ \t]+)?(?:nothing|none|nobody|no[ \t]+\w)', re.I)
CLAUSE_NEGATION_RE = re.compile(r"\b(?:nothing|not|no|never|none|nobody|neither|nor|cannot|without)\b|n['’]t\b", re.I)
CLAUSE_RE = re.compile(r'[,:()–—]|[ \t]-[ \t]|\b(?:and|but|while|whereas|although|though|because|since|so|yet|plus)\b', re.I)
# URGENT is a line that leads with the token and names one of Victor's three cases on that line.
URGENT_RE = re.compile(r'^[ \t>*_-]*(?:\d+[.)][ \t]*)?[*_]*URGENT\b.*?(?i:\b(?:security|data[ -]at[ -]risk|destructive))', re.M)
# Event state -> the hook's --kind. URGENT rides its own urgent kind (sats-completion-notify MILESTONE_KINDS and
# NOTICE_KINDS gain it in this round), never relabeled as another kind.
SATS_KIND = {'START': 'start', 'BLOCKED': 'blocker', 'FAILED': 'blocker', 'CANCELED': 'blocker', 'DONE': 'done', 'URGENT': 'urgent'}
EVENT_ORDER = ('START', 'URGENT', 'BLOCKED', 'FAILED', 'CANCELED', 'DONE')
TERMINAL_STATES = ('DONE', 'BLOCKED', 'FAILED', 'CANCELED')
ASK_STATES = ('BLOCKED', 'FAILED', 'CANCELED')  # a later reply or settle closes them before they send
DECISION_ID_RE = re.compile(r'\bDECISION-[A-Z0-9][A-Z0-9_-]*')
# A decision line asks Victor when it is "for" him ("**Decision for you:**", "Two decisions for you") or in an ask
# shape ("C14 needs a decision from you."). A report of his decision ("Decision from Victor: GO") stays local.
_WHO = r'[*_]{0,2}(?:you|victor)\b'
DECISION_FOR_RE = re.compile(r'\bdecisions?[*_]{0,2}[ \t]+for[ \t]+' + _WHO +
                             r"|\b(?:needs?|needed|requires?|required|awaits?|awaiting|waiting[ \t]+(?:on|for)|asks?[ \t]+for)"
                             r"[ \t]+(?:an?[ \t]+|your[ \t]+|victor'?s[ \t]+)?decisions?[ \t]+(?:from|by)[ \t]+" + _WHO +
                             r'|\bdecisions?[ \t]+(?:from|by)[ \t]+' + _WHO + r'[*_]{0,2}[ \t]+(?:is[ \t]+|are[ \t]+)?(?:needed|required|pending)\b',
                             re.I)
# Prose that only names the markers is no ask (LIVE-2, 2026-10-23 23:05 CT: the bullet "NEEDS-VICTOR, BLOCKED, and
# decision markers anywhere, including fenced and inline code." in a status sent a false BLOCKED). A marker token is a
# name, not an ask, only when three things hold (names_markers). Nothing labels it: a colon or a spaced dash after the
# marker names makes it an ask's label ("NEEDS-VICTOR and BLOCKED: pick A", "BLOCKED: lines 40-60 failed"). The line
# asks nothing (REQUEST_RE or a PROSE ask). And either a list of marker names joined by a conjunction follows it, in
# any case ("NEEDS-VICTOR AND BLOCKED markers"), or a detection predicate follows it, after at most one noun for it
# (MENTION_TAIL_RE: "matches inside fences", "lines count anywhere", "status is now covered by the suite"). Every
# other shape asks, so an unlisted mention costs a notice, never an ask. A quoted or coded decision phrase names it too.
_QUOTE = '[*_`\'"“”‘’]*'
_NAME = r'(?:NEEDS-VICTOR|BLOCKED|DECISION-[A-Z0-9_-]*|DECISION|[Dd]ecisions?(?:[ \t]+for[ \t]+(?:you|Victor))?|DONE|FAILED|CANCEL+ED|START|URGENT)\b'
_JOIN = r'(?i:\band\b|\bor\b)'
MENTION_LIST_RE = re.compile(r'(?:' + _QUOTE + r'[ \t]*(?:,|/|&|' + _JOIN + r')(?:[ \t]*' + _JOIN + r')?[ \t]*' + _QUOTE + _NAME + r')*' + _QUOTE)
MENTION_LABEL_RE = re.compile(r'[ \t*_]*:|[ \t]+[-\u2013\u2014][ \t]')
MENTION_TAIL_RE = re.compile(
    r'(?:[ \t]+(?:markers?|lines?|tokens?|labels?|tags?|prefix(?:es)?|keywords?|forms?|shapes?|prose|status|detection|handling|'
    r'matching|parsing|support|coverage|rules?|behaviou?r|cases?|notices?|tests?))?(?:[ \t]+(?:now|still|also|always|only))?[ \t]+'
    r'(?:count(?:s|ed)?|match(?:es|ed)?|appear(?:s|ed)?|appl(?:y|ies|ied)|fire(?:s|d)?|trigger(?:s|ed)?|mean(?:s|t)?|anywhere|everywhere|'
    r'inside|within|including|(?:is|are|was|were|stays?|remains?)(?:[ \t]+(?:now|still|also|always|only|not|never))*[ \t]+'
    r'(?:covered|matched|counted|recogni[sz]ed|detected|supported|handled|parsed|stripped|ignored|caught|asks?|an[ \t]+ask|local))\b', re.I)
REQUEST_RE = re.compile(r'\?|\b(?:approve|confirm|decide|choose|pick|reply|answer|sign|unlock|rotate|grant|provide|paste|share|allow|'
                        r'authori[sz]e|bypass|please|tell[ \t]+me|let[ \t]+me[ \t]+know|may[ \t]+i|can[ \t]+i|should[ \t]+i|shall[ \t]+i)\b', re.I)
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
# The events table before notice-package-20261023, byte for byte, and after it. `ask` is derived from the event's
# JSON ('' for every event but a BLOCKED), so an INSERT still names five columns and the older watchdog, rolled
# back without the down-migration, keeps writing this table under its old one-per-generation rule.
EVENTS_V1 = ('CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL,'
             ' state TEXT NOT NULL, data TEXT NOT NULL, UNIQUE (thread, generation, state))')
EVENTS_V2 = ('CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL,'
             ' state TEXT NOT NULL, data TEXT NOT NULL, ask TEXT GENERATED ALWAYS AS'
             " (CASE WHEN json_valid(data) THEN coalesce(json_extract(data, '$.ask'), '') ELSE '' END) VIRTUAL,"
             ' UNIQUE (thread, generation, state, ask))')
EVENT_COLUMNS = 'id, thread, generation, state, data'


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


def names_markers(rest):
    """True when `rest`, the text right after a marker token, makes the token a name, not an ask: no colon or spaced
    dash labels the marker names (MENTION_LABEL_RE), the line asks nothing (REQUEST_RE, PROSE), and a list of marker
    names joined by a conjunction follows ("…, BLOCKED, and decision markers"), or a detection predicate does
    (MENTION_TAIL_RE: "… matches inside fences", "… lines count anywhere")."""
    listed = MENTION_LIST_RE.match(rest)
    after = rest[listed.end():]
    if MENTION_LABEL_RE.match(after) or REQUEST_RE.search(rest) or any(pattern.search(rest) for pattern in PROSE):
        return False
    return bool(re.search(r'\b(?:and|or)\b|&', listed.group(0), re.I) or MENTION_TAIL_RE.match(after))


def marker_ask(line):
    """True for a NEEDS-VICTOR line that asks, not one that only names the markers (names_markers)."""
    found = re.search(r'NEEDS-VICTOR', line)
    return found is not None and not names_markers(line[found.end():])


def decision_for(line):
    """True for a line that asks Victor for a decision ("**Decision for you:**"), unless a negation earlier in its
    sentence cancels it ("That needs no decision from Victor") or the phrase is only named: quoted or coded
    ('"Decision for you:" prose'), or followed by a noun for it or a list of marker names (names_markers)."""
    def asks(m):
        before, after = line[:m.start()], line[m.end():]
        quoted = re.search('[`\'"“‘][*_]*$', before) and re.match('[:*_]{0,3}[`\'"”’]', after)
        return not quoted and not names_markers(after) and not NEGATION_RE.search(re.split(r'[.!?;]\s', before)[-1])
    return any(asks(m) for m in DECISION_FOR_RE.finditer(line))


def blocked_lines(text):
    """A final message's BLOCKED lines: the notice shape or "Closed as BLOCKED", else lines with a bold BLOCKED
    that are not table rows. A negation before the token, in its line or sentence, disqualifies it."""
    lines = [found.group(0).strip(' \t>*_`-') for found in BLOCKED_LINE_RE.finditer(text)
             if not NEGATION_RE.search(found.group(0)[:found.start(1) - found.start()])
             and not names_markers(text[found.end(1):found.end()])]
    if not lines:
        for line in text.splitlines():
            found = INLINE_BLOCKED_RE.search(line)
            if (found and not line.lstrip().startswith('|') and not NEGATION_RE.search(re.split(r'[.!?;]\s', line[:found.start()])[-1])
                    and not names_markers(line[found.end():])):
                lines.append(line.strip(' \t>*_`-'))
    return lines


def blocks(text):
    """The Markdown blocks of a reply in order, each [kind, lines]: 'fence' (its inner lines), 'quote', 'item' (a list
    item), 'heading', 'table' or 'para'. A plain line joins the paragraph, quote or item above it, as Markdown joins
    it; a blank line ends a block."""
    parts, at = [], 0
    for fence in FENCE_RE.finditer(text):
        parts += [('plain', text[at:fence.start()]), ('fence', fence.group(0))]
        at = fence.end()
    parts.append(('plain', text[at:]))
    found = []
    for kind, part in parts:
        if kind == 'fence':
            found.append(['fence', part.splitlines()[1:-1]])
            continue
        current = None
        for line in part.splitlines():
            if not line.strip():
                current = None
                continue
            kind = ('quote' if re.match(r'[ \t]*>', line) else 'item' if re.match(r'[ \t]*(?:[-*+]|\d+[.)])[ \t]', line)
                    else 'heading' if re.match(r'[ \t]*#', line) else 'table' if re.match(r'[ \t]*\|', line) else 'para')
            if kind == 'para' and current is not None and current[0] in ('para', 'quote', 'item'):
                current[1].append(line)
                continue
            current = [kind, [line]]
            found.append(current)
            if kind in ('heading', 'table'):
                current = None
    return found


def sentences(lines):
    """A block's lines joined as one run of text, split after . ! ? or ;"""
    return [part for part in re.split(r'(?<=[.!?;])\s+', ' '.join(line.strip() for line in lines)) if part.strip()]


def settled(sentence):
    """True when a sentence says nothing of unfinished work: no UNFINISHED_RE word, and each clause either names no
    open or new work (OPEN_WORK_RE) and holds no negation, or opens with a negative quantifier, holds no other
    negation and names open work ("Nothing is pending", "No remaining items"). Any other negated clause is unfinished."""
    if UNFINISHED_RE.search(sentence):
        return False
    for clause in CLAUSE_RE.split(sentence):
        if not re.search(r'\w', clause):
            continue
        negations, open_work = len(CLAUSE_NEGATION_RE.findall(clause)), OPEN_WORK_RE.search(clause) is not None
        if negations == 0 and open_work:
            return False
        if negations and not (negations == 1 and open_work and NEGATIVE_QUANTIFIER_RE.match(clause.strip())):
            return False
    return True


def keeps_done(text):
    """True for a later reply that restates the generation's DONE and says nothing of unfinished work: its last
    block outside fenced code is a plain paragraph that no block ending in a colon opens, the paragraph's last sentence
    is exactly a whole-work DONE (DONE_KEPT_RE) with no code span or quote, and every other sentence of the reply,
    fenced lines included, is settled (settled())."""
    found = blocks(text) if isinstance(text, str) else []
    if not found or found[-1][0] != 'para' or (len(found) > 1 and found[-2][0] != 'fence' and found[-2][1][-1].rstrip(' \t*_').endswith(':')):
        return False
    claim = sentences(found[-1][1])
    if '`' in claim[-1] or DONE_KEPT_RE.match(claim[-1]) is None:
        return False
    rest = claim[:-1] + [sentence for kind, lines in found[:-1]
                         for sentence in (lines if kind == 'fence' else sentences([line.strip(' \t>#|*+-') for line in lines]))]
    return all(settled(sentence) for sentence in rest)


def classify(text, final):
    """(kind, excerpt, marker lines, event state) for an ask, else None.

    Markers count in any assistant message, inside fenced and inline code too. Prose counts only in a final
    message, outside code and outside a trailing Next steps offer list. The event is BLOCKED for a NEEDS-VICTOR
    marker, a BLOCKED line or bold BLOCKED of a final message, or a "decision for you" line; FAILED or CANCELED
    for a final message that leads with one; else None, and a DECISION- ID alone or a prose ask stays local. A marker,
    BLOCKED or decision line that only names the markers (names_markers, LIVE-2) is none of these."""
    if not isinstance(text, str) or not text.strip():
        return None
    body = FENCE_RE.sub('', text)
    markers = [line.strip(' \t>*_`-') for line in MARKER_RE.findall(text) if marker_ask(line)]
    event = 'BLOCKED' if markers else None
    if not markers and final:
        head = next((line for line in body.splitlines() if line.strip()), '')
        found = TERMINAL_LINE_RE.match(head)
        if found and not NEGATION_RE.search(head[:found.start(1)]):
            markers, event = [head.strip(' \t>*_-')], 'FAILED' if found.group(1) == 'FAILED' else 'CANCELED'
        else:
            markers = blocked_lines(text)
            event = 'BLOCKED' if markers else None
    if not markers:
        # "Decision for you:" asks Victor (c95235ec kept 17 of them local); a DECISION- ID only names a decision.
        markers = [line.strip() for line in text.splitlines() if DECISION_ID_RE.search(line) or decision_for(line)]
        event = 'BLOCKED' if any(decision_for(line) for line in markers) else None
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
    return kind, mask(excerpt)[:EXCERPT_LIMIT], markers, event


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
    """Per-thread read cursor, per-ask record, and the work generations and events, committed before transport.

    generations: one row per (thread, generation), its origin unique per thread. events: one row per
    (thread, generation, event state, ask), unique, holding the frozen notice and its delivery status; ask is ''
    except for a BLOCKED, which is keyed per ask."""

    def __init__(self, directory=None):
        if directory is not None:
            Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(Path(directory) / 'asks.sqlite3') if directory is not None else ':memory:', timeout=5)
        self.db.execute('PRAGMA journal_mode=TRUNCATE')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS threads (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS asks (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.commit()
        with self.transaction():
            if self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'").fetchone() is None:
                # Additive migration, once: every thread already known gets baseline generation 0, so its history
                # sends nothing, and a thread whose old notice was a blocker keeps that as its BLOCKED.
                self.db.execute('CREATE TABLE generations (thread TEXT NOT NULL, generation INTEGER NOT NULL, origin TEXT NOT NULL,'
                                ' data TEXT NOT NULL, PRIMARY KEY (thread, generation), UNIQUE (thread, origin))')
                self.db.execute(EVENTS_V2)
                self.db.execute('CREATE TABLE migrations (name TEXT PRIMARY KEY, at REAL NOT NULL)')
                self.baseline(time.time())
                self.db.execute("INSERT INTO migrations VALUES ('events-per-ask', ?)", (time.time(),))
            elif not events_per_ask(self.db):
                upgrade_events(self.db, time.time())

    def baseline(self, now):
        # Threads created before this moment are history wherever they are first seen (a scope added later).
        self.db.execute("INSERT INTO migrations VALUES ('generations', ?)", (now,))
        blocked = {}
        for _, ask in self.rows('asks', 'ask-'):
            if ask.get('state') == 'sent' and (ask.get('kind') == 'blocker' or any(
                    MARKER_RE.match(str(line)) for line in ask.get('markers') or [])):
                key = (ask.get('host'), ask.get('thread_id'))
                blocked[key] = max(blocked.get(key, -1), ask.get('position', -1))
        for key, record in self.rows('threads', 'thread:'):
            _, host, thread_id = key.split(':', 2)
            sig = record.get('sig')
            running = isinstance(sig, list) and len(sig) > 2 and sig[2] in ACTIVE
            self.put_generation(host + ':' + thread_id, 0, {'host': host, 'thread_id': thread_id, 'origin': 'baseline',
                                'baseline': True, 'position': record.get('position'), 'closed': not running, 'at': now})
            if (host, thread_id) in blocked:
                self.claim(event(host, thread_id, 0, 'BLOCKED', blocked[(host, thread_id)], now, status='baseline'))

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

    def generations(self, thread):
        return [(n, json.loads(v)) for n, v in self.db.execute(
            'SELECT generation, data FROM generations WHERE thread=? ORDER BY generation', (thread,))]

    def put_generation(self, thread, number, value):
        self.db.execute('INSERT OR REPLACE INTO generations VALUES (?,?,?,?)',
                        (thread, number, value['origin'], json.dumps(value, separators=(',', ':'))))

    def upgraded(self):
        row = self.db.execute("SELECT at FROM migrations WHERE name='generations'").fetchone()
        return row[0] if row else 0

    def origin_known(self, thread, origin):
        return self.db.execute('SELECT 1 FROM generations WHERE thread=? AND origin=?', (thread, origin)).fetchone() is not None

    def event(self, event_id):
        row = self.db.execute('SELECT data FROM events WHERE id=?', (event_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def events(self, prefix):
        """Events of one thread ('host:threadId') or, with a trailing ':', one host."""
        if prefix.endswith(':'):
            query, args = 'thread >= ? AND thread < ?', (prefix, prefix + '￿')
        else:
            query, args = 'thread = ?', (prefix,)
        return [json.loads(v) for (v,) in self.db.execute('SELECT data FROM events WHERE ' + query + ' ORDER BY rowid', args)]

    def claim(self, value):
        """Insert one event under its unique (thread, generation, state, ask) key. False when the key is already claimed."""
        try:
            self.db.execute('INSERT INTO events VALUES (?,?,?,?,?)', (value['event_id'], value['host'] + ':' + value['thread_id'],
                            value['generation'], value['state'], json.dumps(value, separators=(',', ':'))))
        except sqlite3.IntegrityError:
            return False
        return True

    def sent_before_per_ask(self, host, thread_id, generation, slot):
        """The generation's BLOCKED from before per-ask keys when it carried this same ask, else None: its source
        ask, or for a baseline event the round-4 ask at its position, has the same marker lines. A re-wake that
        repeats an ask notified before the upgrade stays that one notice; an ask the old key only bound sends."""
        legacy = self.event(event_key(host, thread_id, generation, 'BLOCKED'))
        if legacy is None:
            return None
        for _, prior in self.rows('asks', 'ask-'):
            if prior.get('host') == host and prior.get('thread_id') == thread_id and ask_key(prior) == slot and (
                    prior.get('ask_id') == legacy.get('source') or (legacy.get('status') == 'baseline'
                                                                    and prior.get('position') == legacy.get('position'))):
                return legacy
        return None

    def restated(self, ask):
        """The event of an earlier ask of the same generation when this BLOCKED ask only restates asks already
        noticed there, else None. Its decision IDs, or without one its marker lines, all appear among the noticed
        asks, so a re-wake that merges or repeats them sends nothing (the live needs-victor fix, cb8a6cc0: "A restated
        ask sends nothing"). Noticed is an ask its own event carried: the event's source, its per-ask key, or a
        round-4 'sent' record. An ask an older one-per-generation event only bound was never shown to Victor and
        still sends, which the needs-victor fix counted as noticed. Its 'BLOCKED:<digest>' events carry their source
        like any other."""
        host, thread_id, generation = ask['host'], ask['thread_id'], ask['generation']
        own = identities(ask, ids_only=bool(decision_ids(ask)))
        if not own:
            return None
        noticed, boundaries = [], None
        for _, prior in self.rows('asks', 'ask-'):
            if (prior.get('host') != host or prior.get('thread_id') != thread_id or prior.get('ask_id') == ask.get('ask_id')
                    or prior.get('state') not in ('bound', 'sent') or not blocked_ask(prior)):
                continue
            number = prior.get('generation')
            if number is None:  # a record stored before generations: its generation by position
                boundaries = spans(self, host + ':' + thread_id) if boundaries is None else boundaries
                number = generation_at(boundaries, prior['position'])
            value = self.event(prior['event_id']) if prior.get('event_id') else None
            if number == generation and (prior['state'] == 'sent' or value is not None and (
                    value.get('source') == prior.get('ask_id') or value.get('ask') == ask_key(prior))):
                noticed.append((prior.get('position', -1), identities(prior), value))
        if not own <= set().union(*(seen for _, seen, _ in noticed)):
            return None
        return next((value for _, seen, value in sorted(noticed, key=lambda row: row[0]) if value is not None and own & seen),
                    None) or self.event(event_key(host, thread_id, generation, 'BLOCKED'))

    def put_event(self, value):
        self.db.execute('UPDATE events SET data=? WHERE id=?', (json.dumps(value, separators=(',', ':')), value['event_id']))

    def close(self):
        self.db.close()


def events_per_ask(db):
    """True once the events table keys a BLOCKED per ask (it has the derived ask column)."""
    return any(row[1] == 'ask' for row in db.execute('PRAGMA table_xinfo(events)'))


def upgrade_events(db, now):
    """Rebuild events under the per-ask key, inside the caller's transaction. Every row keeps its rowid, id and
    data; old rows derive ask ''. No VACUUM, no checkpoint (notice-package-20261023 item 6)."""
    db.execute('ALTER TABLE events RENAME TO events_v1')
    db.execute(EVENTS_V2)
    db.execute('INSERT INTO events (rowid, %s) SELECT rowid, %s FROM events_v1 ORDER BY rowid' % (EVENT_COLUMNS, EVENT_COLUMNS))
    db.execute('DROP TABLE events_v1')
    db.execute("INSERT OR REPLACE INTO migrations VALUES ('events-per-ask', ?)", (now,))


def downgrade_events(db, now):
    """The tested rollback of upgrade_events, inside the caller's transaction: events returns to EVENTS_V1. One row
    of each (thread, generation, state) stays: its legacy row when it has one, else its first per-ask row, which
    takes the legacy event id the older watchdog looks up, so that watchdog binds later asks of the generation to
    it instead of claiming a second BLOCKED or binding to a missing id (DS-M3). The other per-ask BLOCKED rows move
    to events_parked, a table the older watchdog never reads. No VACUUM, no checkpoint."""
    db.execute('ALTER TABLE events RENAME TO events_v2')
    db.execute(EVENTS_V1)
    first = ("rowid IN (SELECT coalesce(min(CASE WHEN ask = '' THEN rowid END), min(rowid)) FROM events_v2"
             ' GROUP BY thread, generation, state)')
    db.execute('INSERT INTO events (rowid, %s) SELECT rowid, %s FROM events_v2 WHERE %s ORDER BY rowid'
               % (EVENT_COLUMNS, EVENT_COLUMNS, first))
    for rowid, data in db.execute("SELECT rowid, data FROM events_v2 WHERE ask != '' AND %s ORDER BY rowid" % first).fetchall():
        value = json.loads(data)
        value['per_ask_event_id'] = value['event_id']
        value['event_id'] = event_key(value['host'], value['thread_id'], value['generation'], value['state'])
        value.pop('ask', None)
        db.execute('UPDATE events SET id=?, data=? WHERE rowid=?', (value['event_id'], json.dumps(value, separators=(',', ':')), rowid))
    if db.execute('SELECT 1 FROM events_v2 WHERE NOT ' + first).fetchone():
        db.execute('CREATE TABLE IF NOT EXISTS events_parked (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL,'
                   ' state TEXT NOT NULL, data TEXT NOT NULL, parked_at REAL NOT NULL)')
        db.execute('INSERT INTO events_parked SELECT %s, ? FROM events_v2 WHERE NOT %s ORDER BY rowid' % (EVENT_COLUMNS, first), (now,))
    db.execute('DROP TABLE events_v2')
    db.execute("DELETE FROM migrations WHERE name='events-per-ask'")


def decision_ids(ask):
    """The decision IDs on the ask's own ask lines. A line that only cites an ID ("Recorded as DECISION-PUSH-2")
    names a past decision and gives none."""
    lines = [str(line) for line in ask.get('markers') or []]
    asking = [line for line in lines if 'NEEDS-VICTOR' in line or re.search(r'\bBLOCKED\b', line) or decision_for(line)]
    return sorted({found for line in asking for found in DECISION_ID_RE.findall(line)})


def identities(ask, ids_only=False):
    """What an ask asks: 'decision:<ID>' for each decision ID on its ask lines, and each marker line unless ids_only."""
    ids = {'decision:' + found for found in decision_ids(ask)}
    return ids if ids_only else ids | {str(line) for line in ask.get('markers') or []}


def ask_key(ask):
    """A BLOCKED event's per-ask key: the ask's decision ID when its ask lines carry one, so a re-wake that rewords
    the same decision is the same notice (SOL-4), else its own marker lines. A new ask is its own notice, while a
    re-wake or duplicate message repeating the same ask is not (Victor GO 3:18 PM CT 2026-10-20: re-wakes,
    retries and duplicates each yield exactly one notice)."""
    ids = decision_ids(ask)
    lines = ['decision:' + found for found in ids] or sorted(set(str(line) for line in ask.get('markers') or [ask.get('excerpt') or '']))
    return 'ask-' + hashlib.sha256('\n'.join(lines).encode()).hexdigest()[:32]


def ask_identity(host, thread_id, message_id):
    return 'ask-' + hashlib.sha256('|'.join((host, thread_id, message_id)).encode()).hexdigest()[:40]


# Words that only name the notice's kind: the marker forms an ask or a notice opens with. A notice and an ask line are
# compared without them, so "BLOCKED rotate the hub key" and "NEEDS-VICTOR rotate the hub key" read alike, and a phrase
# needs three other words to name an ask: "mcp:t1 BLOCKED: needs Victor" names none (NEW-1).
NOTICE_WORDS = frozenset(('needs', 'need', 'needed', 'victor', 'blocked', 'closed', 'as', 'decision', 'decisions'))
# A path token, compared whole like a decision ID: "/repo/main" never matches "/repo/staging".
PATH_RE = re.compile(r'[^\s()\[\]<>"\'`*]*/[^\s()\[\]<>"\'`*]*')


def paths(text):
    """The path tokens of a notice or ask line, without trailing punctuation."""
    return {found.rstrip('.,;:!?') for found in PATH_RE.findall(text)} - {'', '/'}


def phrase(text, thread_id):
    """A notice's or ask line's content words in order, lower case, without decision IDs, paths, the thread id's
    words and the marker words (NOTICE_WORDS)."""
    own = set(re.findall(r'[a-z0-9]+', thread_id.lower()))
    text = PATH_RE.sub(' ', DECISION_ID_RE.sub(' ', text))
    return [word for word in re.findall(r'[a-z0-9]+', text.lower()) if word not in own and word not in NOTICE_WORDS]


def holds(longer, shorter):
    """True when the word list `shorter`, three or more words, runs unbroken in `longer`."""
    size = len(shorter)
    return size >= 3 and any(longer[start:start + size] == shorter for start in range(len(longer) - size + 1))


def notice_carries(message, ask, others=()):
    """True when a thread's own notice message carries this ask and no other ask of its turn (`others`, SOL-2).

    A message that names decision IDs carries exactly the asks with one of those IDs, matched as complete IDs
    (DECISION-PUSH-20 never carries DECISION-PUSH-2). A message without one is read sentence by sentence, and a
    sentence under a negation ("Do not act on …") carries nothing. A sentence carries the ask when it and one of the
    ask's lines hold each other as an unbroken phrase of content words ("mcp:<id> BLOCKED rotate the hub key" carries
    "NEEDS-VICTOR rotate the hub key /y"), that line holds every path the sentence names, and no line of another ask
    of the turn matches the sentence too. A generic message ("BLOCKED: needs Victor") carries none, and one that
    names neither of two paths two asks differ by carries neither."""
    if not isinstance(message, str) or not message.strip():
        return False
    named = set(DECISION_ID_RE.findall(message))
    if named:
        return bool(named & set(decision_ids(ask)))
    text = re.sub(r'^\s*\S*:\S*\s+', '', message)  # without its leading "<thread>" token

    def matches(record, sentence):
        named, notice = paths(sentence), phrase(sentence, ask['thread_id'])
        lines = [str(line) for line in record.get('markers') or []]
        return any(named <= paths(line) and (holds(words, notice) or holds(notice, words))
                   for line in lines for words in [phrase(line, ask['thread_id'])])
    return any(matches(ask, sentence) and not any(matches(other, sentence) for other in others)
               for sentence in re.split(r'(?<=[.!?;])\s+|\n', text) if sentence.strip() and not CLAUSE_NEGATION_RE.search(sentence))


def blocked_ask(ask):
    """True for an ask that is a BLOCKED event, a record the round-4 watchdog wrote included."""
    if 'event' in ask:
        return ask['event'] == 'BLOCKED'
    return ask.get('kind') == 'blocker' or any(MARKER_RE.match(str(line)) for line in ask.get('markers') or [])


def notice_covers(state, send, ask):
    """True when the thread's delivered notice for this ask's turn carried this ask (SOL-2): it is the turn's only
    open ask, or the notice's message carries it and no other ask of the turn (notice_carries). Every other ask of
    the turn sends its own."""
    own = ask_key(ask)
    others = [prior for _, prior in state.rows('asks', 'ask-')
              if prior.get('host') == ask['host'] and prior.get('thread_id') == ask['thread_id'] and prior.get('run') == ask['run']
              and prior.get('state') in ('pending', 'attempting', 'bound') and blocked_ask(prior) and ask_key(prior) != own]
    if not others:
        return True
    return notice_carries(send.notice_message(ask) if hasattr(send, 'notice_message') else None, ask, others)


def event_key(host, thread_id, generation, state, ask=''):
    parts = [host, thread_id, generation, state] + ([ask] if ask else [])
    return 'event-' + hashlib.sha256(json.dumps(parts, separators=(',', ':')).encode()).hexdigest()[:40]


def event(host, thread_id, generation, state, position, at, status='pending', detail='', ask='', **facts):
    """One event record. Its hook run is the generation and its occurrence the state, plus the ask key for a
    BLOCKED, so a retry is the same notice and each ask its own."""
    kind = SATS_KIND[state]
    value = dict(facts, event_id=event_key(host, thread_id, generation, state, ask), host=host, thread_id=thread_id,
                 generation=generation, state=state, kind=kind, position=position, at=at,
                 status=status, attempts=0,
                 run='generation-%d' % generation, occurrence='generation-%d-%s' % (generation, state) + ('-' + ask if ask else ''),
                 message=one_line('T3 %s %s %s generation %d: %s' % (host, thread_id, state, generation, detail), MESSAGE_LIMIT))
    if ask:
        value['ask'] = ask
    return value


def answers(item):
    """True for a timeline item that answers an earlier ask: a user message from a person, or one an agent relays
    through MCP (Sats passing on Victor's reply). A delegated-task completion, a server or provider wake or
    continuation, and a system notice are artifacts that leave the ask open (the live needs-victor fix, cb8a6cc0)."""
    if item.get('type') != 'user_message' or item.get('delegatedCompletion') is not None:
        return False
    created = item.get('createdBy')
    return created != 'system' and not (created == 'agent' and item.get('creationSource') in ('server', 'provider'))


def closed(state, thread, number, record, position):
    """True when generation `number` ended before `position`: a terminal event, an observed event marker
    (`ended`, kept whether or not its notice is ever sent) or its standing DONE reply (`done_at`, DS-H2) at an
    earlier item, or a baseline taken while the thread was not running."""
    if record.get('baseline') and record.get('closed') and type(record.get('position')) is int and record['position'] < position:
        return True
    if type(record.get('ended')) is int and record['ended'] < position:
        return True
    if type(record.get('done_at')) is int and record['done_at'] < position:
        return True
    return any(e['generation'] == number and e['state'] in TERMINAL_STATES and e['position'] < position
               for e in state.events(thread))


def spans(state, thread):
    """[(first position, generation)]: a baseline covers everything before the next origin."""
    return [(-1 if record.get('baseline') else record['position'], number) for number, record in state.generations(thread)]


def generation_at(boundaries, position):
    found = None
    for start, number in boundaries:
        if start <= position:
            found = number
    return found


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
    """Open asks in this window, the asks a later user reply or settle overrides, open URGENT lines, and done:
    {position: True} for each completed reply whose first line leads with DONE, {position: False} for one whose
    last sentence restates it (keeps_done)."""
    found, overridden, urgent, done = [], [], [], {}
    status = meta.get('status')
    settled_at = timestamp(meta.get('settledAt')) if meta.get('settled') or meta.get('archived') else None
    if (meta.get('settled') or meta.get('archived')) and settled_at is None:
        settled_at = float('inf')  # settled at an unknown time: treat as after every ask
    for index, item in enumerate(items):
        if item.get('type') != 'assistant_message' or item.get('visibility') == 'inherited':
            continue
        # Final: the completed last reply of a finished turn, the read's last item or one a user message in a
        # later run follows (a turn read only after the next began). A reply with more work after it in its run is not.
        following = items[index + 1] if index + 1 < len(items) else None
        final = item.get('status') == 'completed' and (
            status not in ACTIVE if following is None else
            following.get('type') == 'user_message' and None not in (item.get('runId'), following.get('runId'))
            and following['runId'] != item['runId'])
        text, complete = full_text(client, thread_id, item)
        if not complete:
            # A partial text read fails the whole scan: the thread's marker stays and nothing in it sends this tick.
            raise Gap('ask-text-truncated')
        line = URGENT_RE.search(FENCE_RE.sub('', text)) if isinstance(text, str) else None
        at = timestamp(item.get('updatedAt'))
        if line and at is not None and not any(answers(later) for later in items[index + 1:]) and not (
                settled_at is not None and settled_at >= at):
            urgent.append({'position': item['position'], 'at': at, 'excerpt': mask(one_line(line.group(0).strip(' \t>*_-'), EXCERPT_LIMIT))})
        head = next((row for row in FENCE_RE.sub('', text).splitlines() if row.strip()), '') if isinstance(text, str) else ''
        lead = DONE_LINE_RE.match(head)
        if item.get('status') == 'completed' and lead and not NEGATION_RE.search(head[:lead.start(1)]):
            done[item['position']] = True
        elif item.get('status') == 'completed' and keeps_done(text):
            done[item['position']] = False
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
        # turn: the message's own run id, kept as evidence; None for a legacy message. Events key on the generation.
        ask = {'host': host, 'thread_id': thread_id, 'message_id': message_id, 'run': run, 'at': at,
               'turn': run if item.get('runId') else None, 'event': verdict[3],
               'kind': verdict[0], 'excerpt': verdict[1], 'markers': verdict[2], 'position': item['position'],
               'ask_id': ask_identity(host, thread_id, message_id)}
        answered = any(answers(later) for later in items[index + 1:])
        (overridden if answered or (settled_at is not None and settled_at >= at) else found).append(ask)
    return found, overridden, urgent, done


def allocate(state, host, thread_id, meta, items, history, marked, now, done=None):
    """Open a generation at each accepted user message of this read, track the last assistant reply, and claim
    START and DONE, inside the scan transaction. Returns (spans, absorbed, waiting): absorbed is a baseline thread's
    first read, whose items are history for generations; its open marker asks still become baseline BLOCKED.
    waiting is a DONE held only by TURN_GRACE.
    marked: positions of this read's messages that carry an event marker, which never end a generation as DONE.
    done: find_asks' DONE replies, {position: True} leading with DONE, {position: False} restating it."""
    thread = host + ':' + thread_id
    done = done if isinstance(done, dict) else dict.fromkeys(done or (), True)

    def claim_done(number, record):
        """Claim generation `number`'s DONE when its DONE reply is due; True while TURN_GRACE alone holds it.

        DONE is the generation's own DONE reply (done_at), claimed once its turn has ended and TURN_GRACE has
        passed, when it is later than every other terminal event of the generation and no later reply superseded
        it. Settling neither sends DONE nor is needed for it. Keying DONE on the settle held the notice for every
        thread that failed to self-settle, and a bulk settle then announced unfinished threads
        (notice-delay-rca-20261023). A generation a user message closed (closed_by) has its final reply: its DONE
        waits only for the DONE reply's own run (DS-H2). The current generation's final reply may still change, so
        its DONE waits while the thread runs. The DONE's turn is the DONE reply's own run."""
        done_at = record.get('done_at')
        if type(done_at) is not int:
            return False
        ends = [e['position'] for e in state.events(thread) if e['generation'] == number and e['state'] in TERMINAL_STATES]
        ends += [record['ended']] if type(record.get('ended')) is int else []
        if done_at <= max([record['position'] if type(record.get('position')) is int else -1] + ends):
            return False
        closing = type(record.get('closed_by')) is int
        if not closing and meta.get('status') in ACTIVE:
            return False
        if turn_running(meta, {'run': record.get('done_run') if closing else None}, now):
            return True
        state.claim(event(host, thread_id, number, 'DONE', done_at, (record.get('done_time') or now) if closing else now,
                          turn_run=record.get('done_run') or meta.get('latestRunId'),
                          detail=mask(one_line(str(meta.get('title') or ''), 120))))
        return False

    rows = state.generations(thread)
    visible = [item for item in items if item.get('visibility') != 'inherited']
    if not rows and visible and (history or visible[0].get('type') != 'user_message'):
        # A seeded archived thread's first read, or a first item that is not a user message: baseline.
        rows = [(0, {'host': host, 'thread_id': thread_id, 'origin': 'baseline', 'baseline': True, 'at': now,
                     'position': None if history else visible[0]['position'] - 1,
                     'closed': meta.get('status') not in ACTIVE})]
        state.put_generation(thread, 0, rows[0][1])
    number, current = rows[-1] if rows else (None, None)
    absorbed = current is not None and current.get('position') is None
    for item in [] if absorbed else visible:
        position = item['position']
        if item.get('type') == 'assistant_message' and current is not None:
            origin_at = current['position'] if type(current.get('position')) is int else -1
            if position in marked and position > origin_at:
                # An event marker ends the generation where it stands, in timeline order and whether or not its
                # notice ever sends (a later reply or settle suppresses that), so an answer after it is new work.
                current['ended'] = min(position, current.get('ended', position))
            # The current last reply is refreshed when reread at the same position (its text or final state may
            # have changed); an item before it or before the origin never moves it back.
            if item.get('status') == 'completed' and position > origin_at and position >= current.get('last_assistant', -1):
                current.update(last_assistant=position, last_assistant_at=timestamp(item.get('updatedAt')), last_marked=position in marked)
            if item.get('status') == 'completed' and position > origin_at:
                lead = done.get(position)
                if lead and position > current.get('done_at', -1):
                    current.update(done_at=position, done_run=item.get('runId'), done_time=timestamp(item.get('updatedAt')))
                elif lead is None and type(current.get('done_at')) is int and position > current['done_at']:
                    # A later reply that neither leads with DONE nor restates it: that DONE was progress (SOL-1).
                    for key in ('done_at', 'done_run', 'done_time'):
                        current.pop(key, None)
            continue
        message_id = item.get('messageId') or item.get('itemId')
        at = timestamp(item.get('updatedAt'))
        if item.get('type') != 'user_message' or not MESSAGE_ID_RE.fullmatch(str(message_id or '')) or at is None:
            continue
        origin = 'message:' + message_id
        if state.origin_known(thread, origin) or (current is not None and not closed(state, thread, number, current, position)):
            continue  # already allocated, or a steer that joins the unfinished generation
        if current is not None:
            if type(current.get('done_at')) is int and current['done_at'] < position:
                # The generation's DONE reply is its final reply: its DONE is claimed before this message opens the
                # next generation, or as soon as the DONE reply's run is over (DS-H2).
                current['closed_by'] = position
                if claim_done(number, current):
                    current['done_pending'] = True
            state.put_generation(thread, number, current)
        number = 1 if current is None else number + 1
        current = {'host': host, 'thread_id': thread_id, 'origin': origin, 'position': position, 'at': at,
                   'message_id': message_id, 'run': item.get('runId')}
        state.put_generation(thread, number, current)
        state.claim(event(host, thread_id, number, 'START', position, at, detail=mask(one_line(str(meta.get('title') or ''), 120))))
    if current is None:
        return [], False, False
    if absorbed:
        current['position'] = max([-1] + [item['position'] for item in visible])
    # waiting: a due DONE inside TURN_GRACE. The thread's listing usually never changes again after its turn ends,
    # so the caller rereads it next tick instead of leaving the DONE to the next listing change.
    waiting = claim_done(number, current)
    state.put_generation(thread, number, current)
    for earlier, record in state.generations(thread):
        if earlier != number and record.get('done_pending'):
            if claim_done(earlier, record):
                waiting = True
            else:
                record.pop('done_pending')
                state.put_generation(thread, earlier, record)
    return spans(state, thread), absorbed, waiting


def turn_running(meta, ask, now):
    """True while the ask's own turn may still run: its thread is active on the ask's run or on an unknown run,
    or stopped less than TURN_GRACE ago, so a notice the turn started has reached the hook's occurrence lock."""
    if not isinstance(meta, dict):
        return True
    if meta.get('status') not in ACTIVE:
        ended = timestamp(meta.get('updatedAt'))
        return ended is not None and now - ended < TURN_GRACE
    run = meta.get('activeRunId') or meta.get('latestRunId')
    return run is None or run == ask['run']


def notice_line(ask):
    """The ask's part of its event's notice line."""
    head = ask['markers'][0] if ask['markers'] else ask['excerpt']
    extra = ' (+%d more)' % (len(ask['markers']) - 1) if len(ask['markers']) > 1 else ''
    return head + extra


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
    """Scan one host's T3 threads, record generations and asks, and deliver claimed events. Returns notices attempted.

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
    upgraded = state.upgraded()
    turns = dict(listed)  # thread id -> latest metadata this tick, for turn_running
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
            # A thread created after this round's upgrade is read from its start, so its first message opens
            # generation 1; a known, seeded or older thread keeps the bounded first window, as history.
            created = timestamp((listing or {}).get('createdAt'))
            history = bool(old.get('seeded')) or (created is not None and created < upgraded)
            fresh = not dry and not history and not state.generations(host + ':' + tid)
            if after is None and not fresh:
                item_count = (listing or {}).get('itemCount')
                if type(item_count) is not int:
                    probe = client.call('t3_thread_read', {'threadId': tid, 'view': 'messages', 'limit': 1, 'runLimit': 1, 'maxCharsPerItem': 1})
                    item_count = (probe.get('thread') or {}).get('itemCount')
                after = item_count - WINDOW - 1 if type(item_count) is int else None
            meta, items, complete = read_thread(client, tid, after)
            turns[tid] = meta
            in_scope = meta.get('projectId') in allowed_set and meta.get('parentThreadId') is None
            found, overridden, urgent, done = find_asks(client, host, tid, meta, items, emit) if in_scope else ([], [], [], [])
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
        replies = [i['position'] for i in items if answers(i)]
        local = []
        with state.transaction():
            # Reconcile asks and events stored on an earlier tick: a later reply or settle closes them before any send.
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
            for prior in state.events(host + ':' + tid):
                if (prior['status'] in ('pending', 'attempting') and prior['state'] in ASK_STATES
                        and (any(r > prior['position'] for r in replies) or (settled_at is not None and settled_at >= prior['at']))):
                    prior['status'] = 'overridden'
                    state.put_event(prior)
            marked = {ask['position'] for ask in found + overridden if ask['event']}
            boundaries, absorbed, waiting = allocate(state, host, tid, meta, items, history, marked, now, done) if in_scope else ([], False, False)
            if waiting:
                record['sig'] = None  # read again next tick, whatever its listing
            for ask in found:
                prior = state.get('asks', ask['ask_id'])
                # A record nothing has notified yet, read while its message streamed or before it was final, is
                # decided again on the text read now: a streamed DECISION- line that completes as "Decision for
                # you:" is an ask (SOL-3).
                refresh = prior is not None and 'event' in prior and prior.get('state') in ('local', 'pending') and any(
                    prior.get(key) != ask[key] for key in ('event', 'kind', 'excerpt', 'markers'))
                if prior is None or refresh:
                    # Only a marker or terminal line in a known generation is an event.
                    ask['generation'] = generation_at(boundaries, ask['position'])
                    ask.update(state='local' if ask['event'] is None or ask['generation'] is None else 'pending', attempts=0,
                               title=record['title'], project_id=record['project_id'])
                    state.put('asks', ask['ask_id'], ask)
                    if ask['state'] == 'local' and (prior is None or prior.get('state') != 'local'):
                        local.append(ask)
                elif 'turn' not in prior:
                    prior['turn'] = ask['turn']  # a record the round-4 watchdog wrote; kept for its evidence
                    state.put('asks', ask['ask_id'], prior)
            # A pending record whose completed text no longer asks anything stays a local record.
            asking = {ask['ask_id'] for ask in found + overridden}
            completed = {ask_identity(host, tid, item.get('messageId') or item.get('itemId')) for item in items
                         if in_scope and item.get('type') == 'assistant_message' and item.get('status') == 'completed'
                         and MESSAGE_ID_RE.fullmatch(str(item.get('messageId') or item.get('itemId') or ''))}
            for ask_id in completed - asking:
                prior = state.get('asks', ask_id)
                if prior is not None and 'event' in prior and prior.get('state') == 'pending':
                    prior.update(state='local', event=None)
                    state.put('asks', ask_id, prior)
                    local.append(prior)
            for line in [] if absorbed else urgent:
                generation = generation_at(boundaries, line['position'])
                if generation is None:
                    continue
                state.claim(event(host, tid, generation, 'URGENT', line['position'], line['at'], detail=line['excerpt'],
                                  excerpt=line['excerpt'], title=record['title'], project_id=record['project_id']))
            state.put('threads', prefix + tid, record)
        for ask in local:
            emit('ask-local', host=host, thread_id=tid, message_id=ask['message_id'], ask_id=ask['ask_id'], kind=ask['kind'])
        if complete:
            # Current only once a complete read's reconcile has committed. A partial page read leaves its
            # asks to the pre-send reconcile, which reads on from the saved position.
            current.add(tid)
    if dry:
        return 0
    count = 0
    refreshed = {}  # thread id -> (user reply positions, settled_at, complete), or None after a failed read

    def reread(tid, fallback):
        """Reconcile before a send for a thread not fully read this tick (backoff, a failed or a partial read).
        Scans have applied every reply up to the thread's saved position, so one read from there serves it all."""
        if tid not in refreshed:
            start = (state.get('threads', prefix + tid) or {}).get('position')
            try:
                meta, items, complete = read_thread(client, tid, start if type(start) is int else fallback)
            except Gap as error:
                emit('gap', host=host, reason=str(error))
                refreshed[tid] = None
            else:
                turns[tid] = meta
                settled_at = timestamp(meta.get('settledAt')) if meta.get('settled') or meta.get('archived') else None
                if (meta.get('settled') or meta.get('archived')) and settled_at is None:
                    settled_at = float('inf')
                refreshed[tid] = ([i['position'] for i in items if answers(i)], settled_at, complete)
                if not complete:
                    emit('gap', host=host, reason='ask-reconcile-partial')
        return refreshed[tid]

    # A later reply in any thread read this tick has already marked its asks overridden.
    pending = sorted((value for _, value in state.rows('asks', 'ask-') if value.get('host') == host and value.get('state') in ('pending', 'attempting')),
                     key=lambda a: a['at'])
    # One decision per event: a BLOCKED event belongs to one ask (ask_key), a FAILED or CANCELED event to
    # the generation. An event already claimed binds every later ask of it, and once one ask of an unclaimed event
    # has been looked at this tick, the event's other asks wait for a later tick.
    looked = set()
    for ask in pending:
        tid = ask['thread_id']
        if tid in held:
            continue
        if tid not in current:
            seen = reread(tid, min(a['position'] for a in pending if a['thread_id'] == tid))
            if seen is None:
                continue
            replies, settled_at, complete = seen
            if any(r > ask['position'] for r in replies) or (settled_at is not None and settled_at >= ask['at']):
                with state.transaction():
                    ask['state'] = 'overridden'
                    state.put('asks', ask['ask_id'], ask)
                continue
            if not complete:
                continue  # a reply may sit past this read; a later tick reads on
        if 'event' not in ask:
            # Stored before this round: a blocker or NEEDS-VICTOR marker is its baseline generation's BLOCKED.
            ask['event'] = 'BLOCKED' if ask.get('kind') == 'blocker' or any(MARKER_RE.match(str(line)) for line in ask.get('markers') or []) else None
            ask['generation'] = generation_at(spans(state, host + ':' + tid), ask['position'])
        if ask.get('event') is None or ask.get('generation') is None:
            with state.transaction():
                ask['state'] = 'local'
                state.put('asks', ask['ask_id'], ask)
            emit('ask-local', host=host, thread_id=tid, message_id=ask['message_id'], ask_id=ask['ask_id'], kind=ask['kind'])
            continue
        slot = ask_key(ask) if ask['event'] == 'BLOCKED' else ''
        key = event_key(host, tid, ask['generation'], ask['event'], slot)
        value = state.event(key) or (state.sent_before_per_ask(host, tid, ask['generation'], slot) or state.restated(ask) if slot else None)
        key = value['event_id'] if value else key
        if value is None:
            if key in looked:
                continue
            looked.add(key)
            if turn_running(turns.get(tid), ask, now):
                continue  # the turn may still post its own notice for this ask; a later tick looks again
            carried = send.thread_notice(ask) if hasattr(send, 'thread_notice') else None
            if carried == 'pending':
                continue  # the hook still holds the thread's notice, queued or in flight; a later tick looks again
            if carried == 'delivered' and slot and not notice_covers(state, send, ask):
                carried = None  # the turn's notice carried another of its asks: this one sends its own (SOL-2)
            value = event(host, tid, ask['generation'], ask['event'], ask['position'], ask['at'],
                          status='thread-notice' if carried == 'delivered' else 'pending', detail=notice_line(ask), ask=slot,
                          source=ask['ask_id'], message_id=ask['message_id'], excerpt=ask['excerpt'],
                          title=ask.get('title'), project_id=ask.get('project_id'))
        with state.transaction():
            state.claim(value)
            ask.update(state='bound', event_id=key)
            state.put('asks', ask['ask_id'], ask)
        emit('ask-bound', host=host, thread_id=tid, message_id=ask['message_id'], ask_id=ask['ask_id'],
             event_id=key, state=ask['event'], status=value['status'])
    # Each claimed event goes out under its own occurrence, at most MAX_ATTEMPTS times, START first.
    claimed = sorted((v for v in state.events(host + ':') if v['status'] in ('pending', 'attempting')),
                     key=lambda v: (v['at'], v['generation'], EVENT_ORDER.index(v['state'])))
    for value in claimed:
        tid = value['thread_id']
        if tid in held:
            continue
        if value['attempts'] >= MAX_ATTEMPTS:
            # An attempt that never returned used the last try; the hook's own ledger owns any retry.
            with state.transaction():
                value['status'] = 'failed'
                state.put_event(value)
            emit('event-notice', host=host, thread_id=tid, event_id=value['event_id'], generation=value['generation'],
                 state=value['state'], kind=value['kind'], status='failed', attempts=value['attempts'], reason='attempt-cap')
            continue
        if value['state'] in ASK_STATES and tid not in current:
            seen = reread(tid, value['position'])
            if seen is None:
                continue
            replies, settled_at, complete = seen
            if any(r > value['position'] for r in replies) or (settled_at is not None and settled_at >= value['at']):
                with state.transaction():
                    value['status'] = 'overridden'
                    state.put_event(value)
                continue
            if not complete:
                continue
        if value['state'] == 'DONE' and not value['attempts'] and value.get('turn_run') and hasattr(send, 'thread_notice'):
            carried = send.thread_notice({'thread_id': tid, 'run': value['turn_run']}, kinds=('done',))
            if carried == 'pending':
                continue
            if carried == 'delivered':
                with state.transaction():
                    value['status'] = 'thread-notice'
                    state.put_event(value)
                emit('event-notice', host=host, thread_id=tid, event_id=value['event_id'], generation=value['generation'],
                     state='DONE', kind=value['kind'], status='thread-notice', attempts=0)
                continue
        if count >= max_notices:
            emit('gap', host=host, reason='ask-notice-budget')
            break
        if deadline is not None and time.monotonic() >= deadline:
            emit('gap', host=host, reason='ask-time-budget')
            break
        count += 1
        evidence = Path(evidence_dir) / (value['event_id'] + '.json')
        write_evidence(evidence, {key: value.get(key) for key in ('event_id', 'host', 'thread_id', 'project_id', 'title', 'generation',
                                                                   'state', 'kind', 'position', 'at', 'message_id', 'excerpt')}
                       | {'link': 't3-thread://v1/' + tid})
        plan = {key: value[key] for key in ('host', 'thread_id', 'run', 'kind', 'occurrence', 'message')} | {'evidence': str(evidence)}
        with state.transaction():
            value['attempts'] += 1
            value['status'] = 'attempting'
            state.put_event(value)
        try:
            receipt = send(plan)
        except Exception:
            receipt = {'accepted': False, 'reason': 'transport-exception'}
        receipt = receipt if isinstance(receipt, dict) else {}
        accepted = receipt.get('accepted') is True
        fields = {k: receipt.get(k) for k in ('event_id', 'http_status', 'sats_receipt', 'recipient_run_id',
                                              'delivery_failure', 'reason') if receipt.get(k) is not None}
        with state.transaction():
            value['status'] = 'sent' if accepted else ('failed' if value['attempts'] >= MAX_ATTEMPTS else 'pending')
            value['receipt'] = fields
            state.put_event(value)
        emit('event-notice', host=host, thread_id=tid, event_id=value['event_id'], generation=value['generation'],
             state=value['state'], kind=value['kind'], status=value['status'], attempts=value['attempts'],
             **{('hook_event_id' if k == 'event_id' else k): v for k, v in fields.items()})
    return count
