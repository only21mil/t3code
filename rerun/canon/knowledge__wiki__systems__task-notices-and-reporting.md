---
title: Task notices and reporting
aliases: [task-notices, reporting-owner, task-notices-and-reporting]
created: 2026-10-14
updated: 2026-10-25
verified: 2026-10-18
type: system
status: active
tags: [agent-system, workflow, decision]
sources:
  - 'Victor 2026-10-25 10:47 PM CT approved the rule audit (research/gate-rethink-audit-20261025/RECOMMENDATIONS.md at 75d859c4), row C2, C3, C8, M1, M4'
  - 'Sats 2026-10-25 8:54 PM CT amended brief v2 (91c463b8), Victor 8:38/8:40 PM CT: every no-continuation stop reports, including hold/wait/draft/input; the stopped lane owns its report; Genesis stop-notice lane mcp:d8b5d3cf names those kinds'
  - 'Victor 2026-10-25 6:51 PM CT, genesis-notice-kind-start-records-20261025: an exit-0 lane with a fresh RESULT and no verdict line sends done (§ Terminal self-report, Route)'
  - 'Victor 2026-10-25 18:18 CT, thread-bot-relay-via-sats-20261025: relay notice 9fe43770 exposed the reply-waiver conflict (§ Report-out standard); incident thread excluded from this canon edit'
  - 'Victor 2026-10-25, thread-bot-relay-via-sats-20261025: Genesis-to-Lightning handoff correction (§ Channels and shape)'
  - 'Victor 2026-10-25 18:00 CT: Grok-launched and Victor-started T3 threads share the report-out standard; files and bot notices do not replace in-chat wake updates'
  - 'Victor 2026-10-25 4:41 PM CT nested V2 design and 4:58 PM CT canon alignment (objective canon-nested-v2-and-cc-providers-20261025, brief sha256 c38ef22b961e187048ee093fb1c48f1e8ea0d5c8f32a4512c6c31aba6729e207): the master thread is the tree''s top-level orchestrator and sole terminal sender; per-PR orchestrators hand back to it'
  - 'Sats 2026-10-25, applied by lane-notice-direct-https-20261025, cd7414e9 (readback 1:38-1:50 PM CT under Genesis''s 1:17 PM CT GO-SKIP): every host posts by direct HTTPS, a sent notice is exit 0 WEBHOOK_ACCEPTED and anything else NOT_SENT non-zero, no exit-dropping filter (§ Terminal self-report, Route); fallback now covers only M3 and the Muse VM'
  - 'Sats 2026-10-25 12:03 PM CT via Hash, from Genesis''s settle and webhook audit (t3-e2771e52 AUDIT.md): probe briefs name their terminal route (§ Milestones and wakes item 2), a failed run or all-failed children sends BLOCKED at once (item 5), terminal kinds (§ Terminal self-report, Route)'
  - 'Grok bots agreed 2026-10-25, relayed by Hash: lane notices cover headless lanes too, the key header stays off argv and logs, and Sats''s webhook is the fallback for NEEDS-VICTOR, owners without an entry and threads launched before the entries; § Terminal self-report, Route'
  - 'Victor 2026-10-25 8:38 AM CT: each owner bot gets its own notice routine and webhook; replaces the 2026-10-23 single-webhook owner routing'
  - 'Victor 2026-10-24 10:08 AM CT, reviews bypassed by his order: the F13 Pro T3 thread f07163de-a84b-477d-a7d1-aa9bd2944103 report-outs plus the Ben Davis shape become § Report-out standard'
  - 'Victor 2026-10-25 8:38 AM CT, "Once confirmed we need to delete the script": stall watchdog removed after the per-owner sender proof (log 2026-10-25); 2026-10-23 9:01 PM CT: notifier fallback until install'
  - 'Victor 2026-10-20 1:17 PM CT: terminal generation per-run counter, approved proposal sha256 a4f8d3b479dfa4f4ca33462a23efb776523526a62fcc86e6f622b163c8b46cea'
  - 'Full source list and earlier text: [[wiki/archive/canon-cleanup-crossapp-history-2026-10-25]], [[wiki/archive/task-notices-and-reporting-2026-10-18]], [[wiki/archive/task-notices-changelog]]'
confidence: high
owner: sats
---

# Task notices and reporting

This page owns task notices for every Victor/Sats seat, lane and bot on every
host and harness: what gets reported, to whom, in what shape, and what stays
quiet. What an orchestrator tells Victor on each wake is in
[[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]].
Lifecycle and settlement are in
[[wiki/systems/sats-pm-visible-swarm#Settle on finish, archive after one week]].
A child's questions follow Questions in
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]].
Launch and hook mechanics are in
[[wiki/systems/lane-milestones-and-stall-watchdog]].

## Milestones and wakes

A work episode's external stop notice follows § Terminal self-report below.
Ordinary progress stays in the local log or the native child return; that
section decides whether a wait is a reportable stop.

1. A milestone is start, step, blocker, decision, done or stalled. Append each
   to `<lanedir>/MILESTONES.log` with a timestamp, one line and an evidence
   path. A step reports its check or artifact status. A failure, rule
   violation or approval wait is a blocker and carries the exact action or
   request ID when one exists.
2. Stop-report ownership and native child suppression follow § Terminal
   self-report. A per-PR orchestrator also hands its work back to the master;
   a delegate returns through its native task channel. Who
   may start children follows
   [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]].
   Every brief carries this duty and the log and report paths, and passes them
   down. A brief may name a different recipient for its
   task; that override stands. Every bot-launched brief, probes and seat or
   full-access proofs included, names its terminal route under § Terminal
   self-report, Route; no brief is exempt by default (Sats 2026-10-25 12:03 PM
   CT, from Genesis's settle audit: 5 probe threads sent nothing).
3. Answer a question Victor asks directly in its thread, status asks first.
4. Before terminal handback, check the single self-report receipt. Log any
   missing required report with event, run, delivery stage and corrective
   owner.
5. A stall is local evidence. If the owner cannot continue, it finalizes
   BLOCKED through the same terminal self-report. A top-level orchestrator
   whose run fails, or whose children have all failed with no rerun path,
   sends that BLOCKED in the same turn, without waiting for another wake
   (Sats 2026-10-25 12:03 PM CT, from Genesis's settle audit). A per-PR
   orchestrator in that state hands BLOCKED back to its master in the same
   turn; the master's rerun or terminal BLOCKED then follows this item.

## Terminal self-report

This contract applies on every Victor/Sats host, backend environment and
harness, T3 threads and headless lanes alike. Each lane or independently
launched thread owns one stop report per canonical threadId and work episode,
sent through its owner's webhook under Route below and
`sats-completion-notify`.

Send whenever accepted work stops without an autonomous continuation:
DONE, BLOCKED, FAILED, CANCELED, NEEDS-VICTOR, HOLD, HOLD-DRAFT, a draft
awaiting approval, or waiting for input, amended scope or an external
dependency. Stops use `hold`, `wait`, `draft` and `input` alongside existing
terminal kinds; preserve the original disposition and required action in
the payload. Kind normalization belongs to the sender's kind list in
`tools/sats-lane-notice/README.md`, aligned with Genesis lane `mcp:d8b5d3cf`.
An owned child, queued accepted work or a registered native event that will
continue the work makes a turn end an interim yield; an unregistered hope of
resumption does not. Ordinary progress stays local.

The stopped lane sends its own notice; its opener never substitutes its own
report for that lane's. This includes a separately launched per-PR thread,
even when its work also returns to a master. Native delegates, reviewers and
headless wrappers suppress a duplicate webhook only with a registered
parent binding and durable native handback. A prose opener ID is not proof;
unknown binding is a delivery gap, never permission to silently suppress.
A chat reply does not discharge this handoff. Every brief ordering a stop
names this section, the result path, report owner and stop route.

Sending a stop notice does not accept, complete or settle the objective.
Holds, drafts and unresolved waits remain unsettled under the separate
settlement predicate.

Agents call the installed notifier operation and read its receipt. The
notifier and receiver hold the environment and thread binding, generation
allocation, outbox, dedupe and receipt storage, under one durable authority
shared across all routes and hosts for each backend environment. Keep these
controls until their owner demonstrates equivalent native behavior. The
requirements below specify that operation; they call for no agent-run ledger
and no second watcher.

Register the canonical environment and thread binding before work. The key
is threadId plus terminal generation in that environment. The final state
is frozen in its body, never another key for a second send in that episode.
Allocate the generation durably for a new work episode before any terminal
send. A new accepted objective, or a Victor answer that resumes terminal
work, starts a new generation. A stop ends its episode even when the thread
stays open. An accepted input or report-owner instruction resuming HOLD,
draft, wait, input, BLOCKED or FAILED allocates the next episode once from
the immutable originating message ID. So does a Victor answer relayed by Sats. A retry,
duplicate relay, native hook, concurrent route, provider switch or forced
re-wake alone never advances it, and a re-wake repeating the same terminal
event keeps its original generation. Every route uses the recorded generation
and immutable body for that episode. A pure headless task keeps its stable
host/lane/run identity. A wrapper that starts T3 forwards to the T3 key and
suppresses its own launch-terminal notice. A second BLOCKED decision after
resumed work and a later objective's DONE get new generation keys; each sends
once. Same-event retries and re-wakes keep the original receipt and send
nothing new.

The thread requests its stop notice. Native run finalization and pending-input
transitions must durably enqueue the same immutable event if it missed that
request, sharing the event key, outbox and receipt with explicit sends. A
hook failure leaves delivery pending with a visible action owner; settlement
never proves a send. Native integration is Genesis-owned under
[[wiki/systems/lane-milestones-and-stall-watchdog#Terminal delivery integration]];
this canon change proves neither installation nor native coverage. Keep any
existing transitional completion watcher until that owner verifies its
replacement; add no polling watcher.

The terminal generation is a durable per-thread run counter. Persist the
counter, accepted objective or originating resume message, full key,
immutable body hash and original receipt in notifier storage. Deduplicate the
objective or resume message before allocation so competing routes cannot
advance the counter twice for the same work episode.

Freeze the event ID, recipient binding, result path/hash and payload bytes
before sending. The receiver atomically dedupes the key and body hash and
starts at most one run of the receiving bot's routine through a durable
idempotent dispatch or a reconcilable dispatch identity. It returns the
original receipt on retries. Different payload bytes under one key are a
conflict, not permission to send again. Keep uncertain sends pending with
that same key. Notifier state survives process death and reopening; a
host-local lock is insufficient.

Mark DELIVERED only for an authenticated successful receipt matching the
event ID, full environment/thread/generation/state key, body hash and
recipient and naming the run actually started. HTTP 2xx, local append, dedupe
suppression and an agent's claim alone are not delivery. Missing receipt or
receiver idempotency is a delivery gap: retain the outbox and report the gap
in RESULT. Retry through the existing bounded outbox path, with no new
watcher or model polling. Runtime delivery completion requires real receipt
evidence, never a simulated unit-test receipt. Canon-only publication does
not establish implementation, adoption or real canary success. Integration
and migration belong to
[[wiki/systems/lane-milestones-and-stall-watchdog#Terminal delivery integration]].

Fallback until install, Victor 2026-10-23. The generation-bound authenticated
receipt above is the target contract. On a host where its owner has not yet
installed and read back the generation-bound notifier operation, a thread whose
substantive work is complete closes on its RESULT.md and its registry close-out
row. Line 1 follows the substantive work. RESULT records terminal delivery as
unverified and names the notifier gap. The thread makes one terminal send
through the installed route and reports only the receipt that route returned,
under its real kind: a legacy milestone receipt stays a legacy receipt. A brief
whose objective is the delivery proof itself still reports that proof unproved.
Once the owner installs and reads back the operation on a host, the full
contract applies there again. Since 2026-10-25 the fallback covers only M3
(`m3mbp`) and the Muse VM; the MBP, Mac mini, Yoga, F13 Pro and F-D run the
installed notifier (Sats 2026-10-25, applied by
lane-notice-direct-https-20261025, cd7414e9).

Route (Victor 2026-10-25 8:38 AM CT). Each bot that owns lanes has its own
notice routine and webhook. The owner is the bot in the thread's or lane's
row in [[cross-app-owner-registry]]. Each independently launched thread or
headless lane posts its stop report to that owner's webhook. A per-PR thread
uses its brief's report owner, else inherits its master's registry owner;
the master does not send on its behalf. A brief's explicit recipient stands.
A NEEDS-VICTOR, a decision only Victor can make, goes to Sats's webhook. A
child's question, a per-PR orchestrator's included, goes to its opener;
an independently launched thread's stop notice remains its own duty above
([[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]],
Questions). Each webhook's URL and key are the secrets
`LANE_NOTICES_URL_<BOT>` and `LANE_NOTICES_KEY_<BOT>`, `<BOT>` in upper case.
Only `hash`, `genesis`, `oracle`, `mempool`, `node` and `miner` have entries
so far. Sats has no `LANE_NOTICES` entry: its existing route is the
NEEDS-VICTOR route and the fallback. Read them from the host's fleet
secrets under [[wiki/systems/sats-secrets-and-api-locations]]; no value goes
in canon, argv or logs. The sender passes the key header from a file
(`curl -H @file`) or from an environment variable on stdin (`curl -H @-`),
never as a plain `-H` carrying the key. Sats's webhook is the fallback. It
takes every NEEDS-VICTOR, the notices of an owner with no loaded entry (now
`lightning`, `seed` and `relay`) or a row whose owner cannot be resolved, and
the notices of threads launched before the entries existed.
The sender is `sats-lane-notice` (victor-vault `tools/sats-lane-notice/`),
installed with the generation-bound `sats-completion-notify` on every T3 host
except the two that Fallback until install above names.
A thread or script sends with `sats-lane-notice send`. Each host posts its own
notices by direct HTTPS, Sats-routed ones included, with no relay through F-D.
Its README holds the commands, exit codes and install.
A sent notice is exit 0 with `"state":"WEBHOOK_ACCEPTED"`. Anything else
prints one JSON line with `"state":"NOT_SENT"` and the real error, and exits
non-zero. Keep that exit code: never pipe the sender or notifier through
`tail`, `head` or any filter that drops it, and run an unavoidable pipe under
`set -o pipefail`, so a failed send fails the step (Sats 2026-10-25, applied
by lane-notice-direct-https-20261025, cd7414e9). On 2026-10-25 three
NEEDS-VICTOR asks from F-D root `d9ddd550` were lost between 12:17 and
12:35 PM CT: `post` then exited 3 unsent for any Sats-routed notice, and
`| tail -1` hid the exit code.
Terminal DONE sends `--kind done`, BLOCKED `--kind blocker` and NEEDS-VICTOR
`--kind decision`; the stop dispositions above use the corresponding sender
kind. The sender's accepted kinds and aliases are in that README
(Sats 2026-10-25 12:03 PM CT, from Genesis's settle audit).
A launched lane's own terminal takes its kind from the run. A fresh RESULT
with a passing verdict line, or with no verdict line and a proven exit 0, is
`done`. A named stop follows the stop classification above. A failing or
unrecognized verdict, a failed or unproven exit, and a stale or missing RESULT
are `blocker` (Victor 2026-10-25 6:51 PM CT, after
exit-0 proof lane genesis-launcher-yolo-proof-20261025 went out as a blocker).

Name the episode with `--occurrence terminal-gen<N>-<STATE>`; a retry
keeps its generation and frozen event key. A different terminal state in
that episode is a conflict. A new objective or accepted resume starts the
next generation under the allocation contract above. FYI, status, ACK and
canary milestones are local-only, including queued FYIs from older senders.
`post` is the notifier's transport for a frozen notice, never an alternate
front door for hand-made messages or keys. Test contexts reach neither the
secret reader nor an owner webhook. Required action-needed handoffs and
priority wakes remain governed by § Shared decisions and results.

## Channels and shape

- When a T3 thread has no direct route to a Grok bot, it sends a lane notice to Sats's webhook naming the recipient bot and handoff path; Sats relays it, and the thread never asks Victor to carry messages between bots.
- Victor talks only with Sats, with two Lightning exceptions. Every other bot
  routes results, asks and alerts under § Shared decisions and results,
  and writes nothing addressed to Victor in its own chat. Lightning sends Victor its alert lines directly,
  deduped, one short line each. Lightning also works all X
  work (reply sweep, trends report and drafts, weekly recap, approvals and
  posting) with Victor in her own chat and keeps Sats informed.
- A notice, and every bot-to-bot message, is one short line naming the
  thread or lane, its state, what happened and the absolute path of its file.
  Bodies, logs and diffs stay in the named file. A relayed Victor decision is written
  into the thread or brief first; the message carries its path. Only Sats
  relays Victor's words; a bot that sees them elsewhere does not relay them
  again.
- That file opens with frontmatter and any machine-read line-1 verdict
  (`DONE <sha>`, `PASS`, `BLOCKED <reason>`), then a 3 to 5 line plain-English
  TLDR (Victor 2026-10-11, guidance): what was done or found, what it means, what Victor must decide. A
  BLOCKED or failed file names the cause and its owner when known. IDs, paths
  and SHAs go below the TLDR.
- Every report-out to Victor or Sats, from Sats, a lane, a bot or a T3
  thread, takes the shape in § Report-out standard below.
- Every orchestrator report-out to the human or report owner, status answers
  included, states `Running delegates: N/C`, with reviewers included in N and
  the effective ceiling in C. Use the last verified run table and delivered
  results, and mark an unverified count as unverified. Keep producer and
  reviewer counts separate under
  [[wiki/systems/sats-pm-visible-swarm#Worker cap]], and list the
  orchestrator separately. Each layer counts against its own thread's
  ceiling: a per-PR orchestrator's delegates count in its own N, never the
  master's.

### Report-out standard (all machines and harnesses in T3 Code)

This is the only report-out shape rule in canon. It covers every report-out a
T3 thread, lane or bot gives Victor or Sats: START, interim wake updates,
status answers, BLOCKED, NEEDS-VICTOR, DONE and final reports, on every host
and harness. The one-line notice and the RESULT file head above
keep their own shape. Model: the report-outs in F13 Pro T3 thread
`f07163de-a84b-477d-a7d1-aa9bd2944103`, written in the Ben Davis shape.

Victor reads every T3 thread, including `[grokbot]` threads. Every wake ends
with a non-empty in-chat report-out under this section, with a visual where
it helps, even when an incoming relay or notice says a reply is unnecessary.
Relay and notice templates for bots and threads omit "no reply needed".
A RESULT file or one-line bot notice never replaces that report-out.
The terminal notice to the owner still follows § Terminal self-report. Bot
chats retain § Channels and shape.

Order:

1. Bottom line. Open with 2 to 5 short sentences and no header: the verdict or outcome first, then what was done and what was not ("Nothing is installed yet.").
2. State table. When the work covers more than one machine, agent, option or item, show it as a Markdown pipe table under a `##` header. Give one row per item and list every item, offline or unknown ones included. Use 3 or 4 columns with cells of 1 to 4 words: the item, its state, the work left.
3. Sections. Use 2 to 5 `##` headers in plain words that name what the section answers, such as "What I found on your fleet", "Does it fit your goal" or "The way I would build it". Under each header put one fact per bullet, or a paragraph of 2 to 4 short sentences. Compare options in a table with one row per measure and one column per option, then name the pick in one line.
4. Limits. Put unproven or partial items in one short paragraph that names them ("Two honest limits."), each marked verified or pending.
5. Agent board. An orchestrator adds `## Agent board, Running delegates: N/C` with an Agent | Job | State table, one row per child (a master's per-PR orchestrators included), then one line saying what is read-only, running or done.
6. Close. When Victor must decide, end with `## N call(s) I need from you`: a numbered list where each item is one question with its options and the recommended option marked "(recommended)", then one line saying what happens on go. Otherwise end with a numbered **Next steps** list of 2 to 3 offers, which start only when he picks one. A NEEDS-VICTOR or BLOCKED machine line that a brief requires stays the very last line.

Style:

- Short sentences, mostly 5 to 15 words, in plain words and of varied length. No filler and no restated brief.
- Inline code spans for every command, path, flag, tool, script and host name, such as `brew install btop` or `fleet-top`.
- Status as words in table cells: Installed, Missing, Offline, Running, Done, Blocked. No emoji, icons or color markers. No bold in body text except the **Next steps** label.
- IDs, SHAs and long paths go in one evidence line at the end or in the RESULT file. Evidence, logs and diffs go to a file or PR.

Length by report:

- START and interim wake updates: 3 to 6 short lines with no header, unless several items changed state. Say what came back, what it changes, `Running delegates: N/C` and what is still awaited. Example: "Linux probe is back. It matches my check and tightens the scope. Still running, 3 of 10 slots in use."
- BLOCKED and NEEDS-VICTOR: the bottom line, the blocker or ask, and the decision block, in about 15 lines or fewer. For PR or upstream text approval, summarize what it fixes, give `branch@sha` and the reviewer result, and include one link, normally the fork branch compare view. Label the title and body `sha256` values as fingerprints (not posted). Keep the full text in the lane files, never paste it into chat; lanes' `NEEDS-VICTOR` cards carry that link.
- DONE and final reports: the full order above. The bottom line still fits in the first 5 lines, and the whole report fits on one screen where it can, about 60 lines.
- The 8, 12 and 4 o'clock day briefs: a short paragraph per item with what happened, why it matters, key numbers and a link.
- Skip the close for a one-line status, a question to him, or after he says he is done for the night.
- A surface that does not render Markdown tables, such as Telegram, keeps the same order and uses one-fact bullets in place of tables.

Template:

```markdown
Short answer. <Verdict in one sentence.> <What was done.> <What was not done, or what waits on Victor.>

## Fleet today

| Host | State | Work left |
| --- | --- | --- |
| fd | Installed | None |
| mbp | Missing | `brew install btop` |
| mason-f13 | Offline | Check when it wakes |

## <Question this section answers>

- <One fact.>
- <One fact.>

Two honest limits. <Limit one, pending.> <Limit two, verified.>

## Agent board, Running delegates: 2/10

| Agent | Job | State |
| --- | --- | --- |
| Linux probe | Check fd and yoga | Done |
| Mac probe | Check mbp and mini | Running |

## 1 call I need from you

1. Scope. Include the Mason machines? Options: in, out (recommended), later.

Say go and I install on the Macs and test every host.
```

With no decision pending, the close is instead:

```markdown
**Next steps**
1. <Offer one.>
2. <Offer two.>
```

## Evidence in reports

- Mark each fact verified or pending. Keep source saved, CI passed, deployed, installed and acceptance verified apart. Exclude secrets and routine output.
- Keep requested model and effort apart from runtime-verified ones; report unavailable evidence honestly.
- Report a pending Allow or approval at once with the exact action, target and request ID. The parent answers it under Questions in [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]] or surfaces it as blocked, then verifies resumed execution or reports rejection or expiry.
- A supervisor of a foreground CLI worker or `claude -p` review captures its progress in its log and reports under [[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]]. Report only progress the log shows; a CLI process never messages its parent on its own.

## Asks, owners and checks

- Each task and result has one owner bot. Shared records and bot wakes follow § Shared decisions and results.
- A T3 orchestrator records each open ask once in the thread and result. When Victor is needed to continue, finalize BLOCKED and include all pending asks in the single terminal self-report. A per-PR orchestrator puts its open asks in its handback, and the master carries them. The watchdog and native ask paths suppress an independent webhook send for that bound terminal event. A notifier receipt says `sats_receipt: DELIVERED` only under § Terminal self-report.
- Ask Victor each item once and not again while it is open. Whether an existing approval covers the next action follows [[wiki/systems/sats-pm-visible-swarm#Child permissions, Victor 2026-10-11]] and [[wiki/systems/sats-pm-visible-swarm#Approvals across chats, 2026-10-11]]; a covered action proceeds without a NEEDS-VICTOR. Anything a lane-wide "take the recommended option" rule would decide goes to Sats as a Victor decision with a TLDR and numbered options, and the work waits. A review that reaches its round budget follows review-and-babysit § Stop and escalate.
- Before alerting DIED, check whether the stop was intentional: lane log, unit history, a NO-ACCEPT exit (a spent review budget is an end) and owner notes.
- Before relaying a deploy GO, confirm the artifact exists, is built and passes its smoke or start check; otherwise report BLOCKED with what is missing.
- A computer-use lane retries a step inside the permission it holds while each try changes its evidence, input or route (`adapters/sats-shared-common.md` § Working style, Completion). When no changed try remains, it reports BLOCKED with the exact failure. A step is one action toward the goal, such as a sign-in, a dialog or a post. A GO that covers a step covers its retries.

## Shared decisions and results

The one append-only decisions-and-results file is
`/home/box/agent-data/decisions-and-results.log` on the shared Grok Bot box,
where every Grok Bot can read it. Hash owns its availability and this contract.
Sats appends Victor's verbatim decisions with their time and source. Each
owner appends `DONE <lane|thread> <absolute report path>` when its result is
ready. Reports stay in the named files; this log is their shared index.

At turn start, every Grok Bot reads new complete lines from its own saved
byte offset in this file, then saves the offset it consumed. FYIs, status and
ACKs stay in the work's log; nobody copies a result to a second bot.

Wake another agent when the recipient must act or someone is waiting on it.
Needed handoffs, questions, decisions, blockers and native child completions
still wake their recipient; a result needed to continue is an action-needed
wake. FYI, status and ACK wakes stop. A routine DONE goes in the shared file;
the lane's one required terminal self-report to its owner still follows
§ Terminal self-report, without a second-bot relay or owner ACK.

## Quiet, waits and reads

- Shared records and bot wakes follow § Shared decisions and results. Unchanged polling, empty X digests, corrections, read-backs and repeat alerts stay in the work's own log ([[wiki/systems/task-state-and-board]]). One event gets one alert; Lightning owns dedupe. An action-needed bot message is sent once, with its priority right the first time; a held or non-urgent receipt is not a reason to resend. Corrections fold into the next real message. Answer a status question in its existing thread in the shape above.
- A waiting lane checks its gate with a shell or systemd poll that makes no model call (`test -s`, `systemctl --user is-active`, `grep -qF`, an `until ...; do sleep 60; done` loop, or a timer or path unit), and starts a model only when the gate opens. A Grok routine runs only jobs that need judgment each time; a change check becomes a shell check that wakes the bot.
- Lightning's reply-check implementation is victor-vault
  `tools/lightning-reply-check/`. Its README owns the free-reader and
  priority-handoff interfaces and the 30-minute wiring example. Genesis
  hands that wiring to Lightning; source publication changes no routine.
  A missing reader or wake route is a failed prerequisite, never an empty
  sweep. Reply handoffs are action-needed wakes, not lane terminal notices.
- Read append-only logs from a saved byte offset, keep dedupe checks silent on exit codes, and cap growing output (`| head -c 2000`). Large tool results go to a file; tool-output handling belongs to [[wiki/systems/sats-agent-context-efficiency]].

Dated runtime readbacks and removed choreography:
`git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/task-notices-and-reporting.md`.
