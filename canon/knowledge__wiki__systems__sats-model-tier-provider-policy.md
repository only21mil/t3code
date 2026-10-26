---
title: Sats model and reasoning selection
aliases: [model-tier-routing, provider-policy]
created: 2026-06-18
updated: 2026-10-25
type: policy
status: active
tags: [sats, routing, models, providers]
sources:
  - 'Victor 2026-10-25 4:41 PM CT nested V2 design and 4:58 PM CT audit order, brief sha256 c38ef22b961e187048ee093fb1c48f1e8ea0d5c8f32a4512c6c31aba6729e207: master and per-PR V2 orchestrator threads both take the T3 orchestrator row; layer mechanics in [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]]'
  - 'Victor 2026-10-25 4:58 PM CT, same brief: "Also all non codex or claude code models need to be ran through claude code like we did with muse. So Kimi and openrouter need to be set up like this and it needs to run through the hub like everything we do." § Accounts and transport, Other models through Claude Code. Research and preparation receipts (MBP): /Users/m5mbp/work/canon-v2-nested-design-and-claude-code-providers-20261025/{provider-research,hub_usage,hub_model_preparation,provider_generator_implementation,provider_smoke_pack,provider_generator_packet,hub_model_activation}/RESULT.md'
  - 'Victor 2026-10-25, T3 thread mcp:c24e6f61-4297-4646-8ba1-80053a6175c7, on the fixed CODEX_MASON or CODEX_MAIN computer-use account: "Take out the requierment completely. I do not like restrictions". Computer use routes on AUTO_CODEX; § Computer-use tier and route'
  - 'Victor 2026-10-24, canon-gh-main-20261024 steer 7: "Crew is done. Clean it all."'
  - 'Victor 2026-10-24, canon-gh-main-20261024 steer 2: "Hermes is gone."' # History
  - 'Victor 2026-10-23 ~18:15 CT, original brief of thread mcp:4f5dd34b-c5de-434a-998f-439e3f34a87f, copied verbatim by Hash from Sats'' handoff: "Ok do it that way I can run muse code in the claude code inside of t3. Hopefully that fixes all the issues I am having with muse. Make sure to keep it on contributor on." "That way" is Option A, Claude Code calling the Muse Code CLI headless; Option B, a paid Meta API key, was not chosen. Receipt with sha256: /Users/m5mbp/work/muse-exec-in-claude-code-t3-20261023/produce/decision/OPTION-A-PROVENANCE.md (MBP)'
  - 'Superseded 2026-10-25 by Victor''s AUTO_CODEX ruling above; history only. Victor 2026-10-23 5:14 PM CT via Sats, C14 H3: the computer-use account pick uses the maintained hub client, not a self-asserted Tailscale identity header or 127.0.0.1:8332. Record /home/victor/.t3-nightly/worktrees/t3code-fork/grokbot-fd-master-fix-20261023/lanes/fd-master-fix-20261023/DECISIONS-CURRENT.md'
  - 'Victor 2026-10-23 12:57 PM CT via Sats, Claude Code agent definitions: reviewer, reviewer-opus and produce-review retired; the nine kept definitions move to canon agents/claude/; sol-xhigh runs Sol at high. Brief: /home/victor/work/agent-defs-canon-20261023/BRIEF.md'
  - 'Victor 2026-10-23, reviewer scripts retired; review vehicles: review-and-babysit SKILL.md § Vehicles. Brief: /home/victor/work/retire-review-scripts-20261023/BRIEF.md'
  - 'Inside T3, narrowed 2026-10-25 by Victor''s nested V2 design above (a master opens per-PR orchestrator threads; delegates still start nothing); the swarm owner holds the current creation rule. Victor 2026-10-23, no PM hierarchies (root starts every worker and reviewer; children start no children): [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]]'
  - 'Victor direct, 2026-10-20, sol-standard-40-20261020: Sol 6.1 Standard at every effort, T3 serviceTier default, CLI Standard/default equivalent; Fast only when Victor names Fast for that specific task'
  - 'Victor 2026-10-25 08:43 CT canon cleanup, "Yes. I do": T3 and review rules link their owners; dated narrative moved to [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-25]]'
  - 'Dated source history through 2026-10-18: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-18]]'
  - 'Earlier history: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03]]'
owner: sats
confidence: high
---

# Sats model and reasoning selection

This page owns Sats model selection. The Codex section covers Sats/Victor
Codex accounts on every Sats machine (Victor, 2026-09-22). Family Codex homes
kept the 2026-09-08 block, which Victor approved for family agents too; moving
them to the new block waits on a Victor/Rachel decision. Outside T3, other runtimes retain the rules below. All T3 threads, including family harnesses, follow [[wiki/systems/sats-t3-and-review-routing]]. Before orchestration, read
[[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]].
That section owns vehicles, worker creation and capacity;
[[wiki/concepts/dispatch-vehicle-doctrine]] owns Direct and Parent Mode procedures;
review-and-babysit (canon `skills/review-and-babysit/`) owns review rounds, findings and non-writing proof. Current reviewer selection follows [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]], including its upstream exception. The skill owns the review process.

## Computer-use correction, Victor 2026-09-30

Inside T3, model, effort and tier follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
The profiles below apply outside T3; host and evidence requirements remain
on every harness. 3D and Blender tasks, their computer use included, take
their model from § 3D and Blender, Victor 2026-10-18 instead of this section.

Victor, 2026-10-10: computer use on every harness in the Sats/Victor scope
runs Sol 6.1 (`gpt-6.1-sol`), `high` for ordinary interactions and `xhigh`
for difficult or high-risk verification. This includes design-related browser,
GUI, simulator and screenshot interaction. Design judgments remain under
§ Sats design standard. The default execution host remains the MBP.

This supersedes the September 30 non-design restriction. Existing sessions
keep their running profiles.

Victor 2026-10-10 (D24): every harness, Claude Code included, runs computer use on GPT-6.1 Sol, `high` for ordinary interactions and `xhigh` for difficult or high-risk verification. The 2026-10-03 Claude Code `xhigh`-only exception is retired.

Split code authoring from screen operation where possible. Non-design code
that can only be written through a screen runs on Sol 6.1 at the interaction's
`high` or `xhigh`. Design code remains Opus 5.5 `high`;
Sol operates the screen using the Opus-authored result. An inseparable design
code task needs Victor's decision before departing from that design route.

**Computer-use tier and route, Victor 2026-10-20 and 2026-10-25.** Computer use on every harness runs GPT-6.1 Sol (`gpt-6.1-sol`) at `high`, pinned to high; the D24 split (`high` ordinary, `xhigh` difficult or high-risk) is superseded for this task class. Computer use is the standing exception to the Standard tier rule in § Accounts and transport, Sol speed: it runs on the fast (ultrafast) tier under Victor's 2026-10-20 pin, reaffirmed 2026-10-21 (Sol is Standard everywhere else; the computer-use pin stands). The computer-use pin is this model, effort and tier. The route is `AUTO_CODEX` under its existing pool rules (Victor, 2026-10-25: "Take out the requierment completely. I do not like restrictions"). No fixed account, usage read, hub client or HOLD gates computer use.

Spellings by surface for the computer-use fast tier: hub calls carry `service_tier: "priority"`; T3 carries `serviceTier: "priority"`; Codex carries `-c service_tier="priority"` or the supported Fast equivalent; the foreground wrapper takes `--account AUTO_CODEX --service-tier priority`. As elsewhere on this page, an absent readback of the tier actually served stays unverified.

## Execution access, Victor 2026-10-01

Every new Sats/Victor agent and swarm uses the full task-access mode already
authorized and actually supported by its executor. On an eligible Sol CLI
route this means `--sandbox danger-full-access`. Reviewer access and flags
follow review-and-babysit. Other executors use only their exposed controls.
Keep requested, supported and runtime-observed access separate; unknown stays
unknown. Disclose unsupported modes without inventing fields or bypassing
denials. Full access grants no task-scope, account, resource, credential or
permission expansion. Platform controls, approval, privacy and secret
safeguards remain in force.

Codex routing blocks carry self-contained exports of this
shared rule for local-only consumers. Maintain those exports with this section;
a source edit does not establish installation or running-session adoption.

### CLI full-access defaults, Victor 2026-10-17

Victor 2026-10-17 4:46 PM CT sets full access as the default for Sats/Victor
producer CLIs on Framework Desktop, Victor's MBP, F13Pro, Yoga, mini and m3mbp,
for their confirmed owner and agent users. Codex uses
`--dangerously-bypass-approvals-and-sandbox`, or config
`sandbox_mode = "danger-full-access"`, `approval_policy = "never"`,
`web_search = "live"`, and `[sandbox_workspace_write] network_access = true`.
On F-D the `~/.local/bin/codex` wrapper adds that flag itself and exits 1
when a caller passes it, `--yolo`, or any sandbox or approval flag or
config. Callers on F-D pass none of them; sats-lane-launch drops the
full-access requests from codex lane commands before the wrapper sees them.
Claude uses `--dangerously-skip-permissions` or
`permissions.defaultMode = "bypassPermissions"`. Muse Code uses
`permissions.default_profile = ":unrestricted"` in its user settings.
The installed Muse Code schema names that setting; its native profile catalog
says Unrestricted has no filesystem sandbox or approval prompts and allows
direct network access. `muse --yolo` provides the per-run equivalent.

All codex-workflow writing classes, including gather and workspace-write,
default to danger-full-access. Claude maps that to bypassPermissions.
Reviewer classes remain separate, launch full access with review-only in
their brief (review-and-babysit § 2), and keep their content fingerprints and
mutation checks. The existing gitconfig guard stays.
Full access changes no task authority, approval, privacy or secret rules.
Sats confirmed m3mbp, Masons-MacBook-Pro, as a Victor fleet machine at
4:54 PM CT on 2026-10-17. Its mason login is the Victor fleet agent account;
user-level CLI and workflow settings are in scope. The password/keychain
switch stays pending. Mason's F13 Pro, Rachel's MBA and the F-D mason and
rachelvogel users stay excluded. muse-sats remains an unresolved scope decision.

Workflow tests must never deliver lane notices. In versions with a notice
bridge, NODE_TEST_CONTEXT, SATS_TEST=1 or CODEX_WORKFLOW_TEST=1 suppresses both
required-notice creation and hook delivery. Test scratch setup clears the
exported NOTICE_ENV_KEYS and sets SATS_TEST=1 so subprocesses inherit the
marker. Older copies without a notice bridge use the same marker and key
list, clear fixture identity, and sanitize child environments during tests.
The guard also applies to Yoga's archival workflow copy. This isolation
preserves normal non-test notice delivery.

Sol service tier follows § Accounts and transport, Sol speed (Victor,
2026-10-20: Standard at every effort). Saved config is distinct from effective runtime readback. Existing sessions
are not restarted. Rollout evidence is in
`/home/victor/work/fleet-full-access-20261017/RESULT.md`; final proof lanes
remain with Hash.

## T3 routing, Victor 2026-10-17

Moved 2026-10-18 to
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
That page owns every T3 role, effort, tier and readback rule.

### Review routing, Victor 2026-10-17 20:14 CT

Moved 2026-10-18 to
[[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]].
That page owns reviewer selection, the upstream panel and route HOLDs.

## T3 Code vehicle, Victor 2026-10-07

Before starting T3 children, read
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]]
(V2 mechanics, splitting, workspace, readback) and
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]
(model, effort, service tier and reviewer selection, master and per-PR
orchestrators included). Creator roles for the master and per-PR orchestrator
layers live in
[[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]]. Relays, Workflow agents,
native agents, foreground `claude -p` workers and Codex-harness handoffs named
below are outside-T3 vehicles only. The 2026-10-07 V2 quote is in
[[wiki/archive/sats-model-tier-provider-policy-history-2026-10-25#T3 Code vehicle quote]].

## Model routing, Victor 2026-09-29 (evening)

Source: Victor's answers in the Claude Code lane-5 session on the evening of
2026-09-29, recorded as the `model_routing` lane spec. On the wrapper timeout
cap he said "remove it". This section overrides older routing on this page
for the points below. Every safety, privacy, approval, zero-limits and
no-overseer rule stays.

Before execution or dispatch for any role, apply § Execution access, Victor
2026-10-01 above through the current executor's supported controls.

### Who does what

Claude Code assignments follow § Claude Code routing, Victor 2026-10-03.
The superseded September 29 record is preserved verbatim in
[[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Claude Code routing superseded 2026-10-03]].

Outside T3, Victor's 2026-10-10 rule remains: Claude Code and Codex keep their own routing.
Other seats run Sol 6.1 by § Sol 6.1 effort by class for coding and
non-coding work. Design follows § Sats design standard. Claude Auto Opus 5.5
`high` handles parent-feeding gather on Claude Code and Codex outside T3
through § Current gather procedure. Gather runs with full tools,
MCP included (Victor 2026-10-12). Grok-launched lanes follow
§ Grok-launched lanes, Victor 2026-10-18, where research and
gathering use Sol 6.1 `high` with Standard.
Compaction (Victor 2026-10-12): every harness, subagents included, compacts on its session model at the harness default point; the hub Haiku rewrite and the 390K overrides are retired.
Cursor is undecided.

Outside T3, orchestrators follow the harness profiles in
§ Claude Code routing and the Codex block. Coding and repairs use the harness's coding model at
task-selected effort. Design, its implementation code and repairs remain
Opus 5.5 `high` under § Sats design standard.

Computer use follows § Computer-use correction; review follows review-and-babysit.
Inside T3 Code, load [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] for every role. Session compaction still uses
the session model at the harness default point. Outside T3, the Sol relay
by-name rule remains in § Claude Code agent definitions.

The Muse-app ask-only rule applies only inside that app. Native Muse app agents
may do light work there; `Muse auto` stays unchanged. Muse Wonderful is not the
default on other harnesses and has no default outside-T3 review route
(§ Muse Wonderful, Victor 2026-10-14). T3 starts use the T3 routing owner.
Review selection, including occasions Victor names, follows
[[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]].

Victor 2026-10-11: "Please have this be for Muse and Grokbot when they run T3, Codex or Claude code threads from their harness also. They do it alot using the hub codex auto and claude auto. They only have used T3 but I want to be prepared if they use claude code or codex."
Outside T3, the harness model and effort routing applies to Muse app
threads running Codex or Claude Code, including AUTO_CODEX and AUTO_CLAUDE
hub lanes. Grok Bot lanes follow § Grok-launched lanes, Victor 2026-10-18
instead. Muse app and Grok Bot T3 threads follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Their native app defaults stay with their owners.
This harness extension grants no compaction activation.

ROUTING.md scope, Victor 18:26 CT 2026-10-11, relayed by Sats (paraphrase,
not a quote; final wording, replacing the 18:12 and 18:25 CT relays):
`/home/victor/work/model-routing-review-opus-20261010/exec/broadcast/ROUTING.md`,
the 2026-10-11 routing broadcast that summarises this page, governs every
Codex Auto and Claude Auto call made by any Grok Bot agent, and every such
call made by the Muse app. It does not govern a Grok Bot's own
session, which keeps its native app defaults. ROUTING.md names this page as
its source of truth, so where the two differ this page wins. Its October 11
snapshot still names Haiku gather, 390K compaction and the hub compaction
rewrite; this section and § Current gather procedure replace those values.
Line-by-line check:
`/home/victor/work/canon-evening-rules-1854-2026-10-11/ROUTING-CHECK.md`.
Dated snapshot and its 2026-10-12 read: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#ROUTING.md October 11 snapshot, moved 2026-10-14]].

### Grok-launched lanes, Victor 2026-10-18

Victor, 4:55 PM CT 2026-10-18, relayed by Sats, adopted rows 1-5 and a-i of
the r6 routing card
(`/home/victor/work/fleet-routing-table-draft-20261018-r6/out/ADOPT-LIST.md`).
Grok Bot standard lanes and T3 lanes use the same role-based model routing;
Grok Bot is not a Claude Code or Codex harness. Inside T3, use
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
Outside T3, this table covers every lane a Grok Bot launches and overrides
the Claude Code, Codex and other-seat rows elsewhere on this page:

| Work | Model and route | Effort |
|---|---|---|
| Coding and code repairs | Claude Opus 5.5 (`claude-opus-5-5`) on AUTO_CLAUDE | `high`; `xhigh` for complex coding |
| Design and its implementation code | Claude Opus 5.5 through Claude design on AUTO_CLAUDE | `high`; 3D and Blender work, its gather and research included, follows § 3D and Blender, Victor 2026-10-18 |
| Research, gathering, extraction, filing and other misc work | GPT-6.1 Sol (`gpt-6.1-sol`) on AUTO_CODEX with Standard, `service_tier=default` set explicitly | `high` |
| Light writing, docs and X drafts | Claude Opus 5.5 on AUTO_CLAUDE | `high` |
| Computer use | GPT-6.1 Sol under § Computer-use correction, Victor 2026-09-30, at the Fast tier under the computer-use pin (Victor 2026-10-20) | `high` for every interaction (pinned, Victor 2026-10-20) |

Grok launches run no Sonnet. A missing observed tier leaves Standard
unverified (§ Accounts and transport, Sol speed). Orchestration and review
keep their owners in [[wiki/systems/sats-t3-and-review-routing]]. A Grok Bot's
own session keeps its native app defaults. Other scopes keep their owners,
scoped full tools and the retired-Haiku-gather rule.

### Claude Code routing, Victor 2026-10-03

Victor, 2026-10-03: "I want the providers in claude code to be Opus 5.5 with
reasoning set like the Sol 6.1 depending on tasks. Sol 6.1 on Xhigh is still
used for computer use and Sol 6.1 does the adversarial review."
This table applies outside T3 and supersedes the Claude Code producer routes
from September 29 there; Codex, OpenCode and other seats retain
their outside-T3 routes. Victor 2026-10-10 amends the rows below
(items 3 and 4, D04, D09, D19, D22-D24), and Victor 2026-10-23 retires the
reviewer definitions (§ Retired). Inside T3, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
Grok-launched lanes use § Grok-launched lanes, Victor 2026-10-18 instead.

| Work | Model | Effort |
|---|---|---|
| Mechanical (inventories, formatting, bounded checks) | Claude Opus 5.5, native | `medium` |
| Gather for a parent (file search, log sweeps, inventories, classification, extraction that feeds a parent) | Claude Opus 5.5 (`explorer`) on Claude Auto/AUTO_CLAUDE per § Current gather procedure; Grok-launched lanes: § Grok-launched lanes, Victor 2026-10-18 | `high` (Victor 2026-10-13) |
| Ordinary (most code, repairs, planning) | Claude Opus 5.5, native | `high` |
| Light unmatched work, docs, summaries, extraction that is the deliverable (outside T3 Code) | Claude Sonnet 5.5, native (`sonnet`) | `medium`; `high` only with a stated reason; never `xhigh` or `max` |
| Research lanes | GPT-6.1 Sol through a direct `AUTO_CODEX` lane with Standard, `service_tier=default` set explicitly; Sonnet `high` only for Claude-side synthesis | `high`, hard research included (Victor 2026-10-18) |
| CI fixes | GPT-6.1 Sol through a direct `AUTO_CODEX` lane, never Sonnet | `medium` mechanical, `high` otherwise |
| Hard (security, auth, secrets, Bitcoin, payments, concurrency, migrations, architecture, hard debugging, adversarial verifiers that gather their own evidence) | Claude Opus 5.5, native | `xhigh` |
| Design, 3D, graphics, games | Claude Opus 5.5, native (`designer`) | `high`; 3D and Blender: § 3D and Blender, Victor 2026-10-18 |
| Computer use, every kind | GPT-6.1 Sol (`gpt-6.1-sol`), Fast tier at `high`, pinned under the computer-use pin (Victor 2026-10-20, reaffirmed 2026-10-21; § Computer-use correction). Outside T3 Code the `sol` relay runs it on `AUTO_CODEX` at the fast tier (§ Claude Code agent definitions); inside T3 Code it runs as a V2 child under [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] | `high` for every interaction (pinned, Victor 2026-10-20); 3D and Blender: § 3D and Blender, Victor 2026-10-18 |
| Review, follow-up and per-finding verification | [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]] selects; review-and-babysit runs it | per the routing owner |

This table covers built-in agents on Opus, including Explore,
general-purpose and Workflow agents outside T3, and
the named definitions below.
The parent session runs Claude Opus 5.5 `xhigh` (Victor 2026-10-10, item 3). Claude Fable 5.1 runs
only when Victor asks for it by name; no agent definition pins Fable.

Historical T3 `claude_auto` effort note, 2026-10-07: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#T3 claude_auto effort note 2026-10-07, moved 2026-10-18]].

Outside T3 Code, Sonnet 5.5 runs as the relay wrapper at `medium`, carrying the brief to Sol and returning Sol's result unchanged. On the Claude Code seat outside T3 Code it is also a named producer for light unmatched work, docs, summaries and extraction that is the deliverable, at `medium`, `high` only with a stated reason, never `xhigh` or `max` (native `sonnet`; Victor 2026-10-10, D04, D22, D23). This amends Victor's 2026-09-24 ruling that Sonnet is not a default producer for those classes on that seat only. Sonnet never codes, reviews, runs computer use or leads research.

Inside T3 Code, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] and [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]], with no Sonnet relay.
The definitions in § Claude Code agent definitions are outside-T3 vehicles
for producer work; review runs only through T3 (review-and-babysit § Vehicles,
Victor 2026-10-23).

### Sol 6.1 effort by class

This class table applies outside T3. Inside T3, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].

| Class | Effort | Use |
|---|---|---|
| mechanical | `medium` | extraction, inventories, digest rebinds, formatting, WIP preservation, bounded checks with a decisive result |
| ordinary | `high` | most code, repairs, docs, research, planning; the default |
| hard | `xhigh` | security, auth, secrets, Bitcoin, payments, concurrency, migrations, architecture, hard debugging, large three-way merges |
| verify | `xhigh` | adversarial verifiers that gather their own evidence |
| `max`, `ultra` | only when Victor asks | |

A worker that confirms or refutes one existing finding or candidate is
independent review under review-and-babysit. Outside Claude Code,
the Sol `xhigh` verify class covers adversarial investigations that gather
their own evidence; Claude Code adversarial verifiers follow § Claude Code
routing, Victor 2026-10-03. In a swarm, workers and adversarial verifiers
report facts to the coordinator (the parent), who integrates them and writes
the result (Victor, 2026-10-04).

Never `low`, for any model, on a bot launch: the effort floor is `medium`
for every orchestrator or bot spin-up call, meaning seat launches,
`delegate_task`, `t3_thread_launch`, AUTO lanes and the workers they start.
The Sonnet wrapper runs at `medium`. The floor is a launch rule, not a picker
ban: Victor's T3 picker keeps every model and every reasoning level for the
threads he starts himself (Victor ruling 2026-10-10 04:23 CT, relayed by
Sats). Bot launches still leave `max` and `ultra` to Victor's request (table
above).

### Accounts and transport

- Every Claude or Codex/GPT model call by any Sats or family agent, bot,
  app or tool, on every machine, uses `AUTO_CLAUDE` or `AUTO_CODEX`
  respectively through the Sats hub on Framework Desktop. Universal AUTO
  scope is explicit in
  [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]]
  under Victor's direct 2026-10-12 instruction. Victor's
  2026-10-10 harness-specific routing rule selects the model outside T3; [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] selects it inside T3. This section
  selects its transport. Native Muse-app work remains under the app's
  own rule (§ Who does what).
  The hub has two parts. The `sats-router` dashboard on `127.0.0.1:8332`
  (Tailscale Serve `:7443` from other hosts) owns AUTO and pins; CLIProxyAPI
  on `127.0.0.1:8330` sits behind it and holds the account sign-ins. A call
  reaches AUTO only when it goes to `:8332` with the header
  `X-Sats-Account: AUTO_CODEX` or `X-Sats-Account: AUTO_CLAUDE`. Muse Code
  calls use `X-Sats-Account: AUTO_MUSE` the same way (§ Muse Wonderful). A
  Claude or GPT call straight to `:8330`, or to `:8332` with no
  `X-Sats-Account` header, skips AUTO and is a gap (audit 2026-10-10, gap 5).
  For Claude and GPT models, direct OAuth, direct API keys, OpenRouter, any
  other upstream and any Claude account pin are gaps. Other models follow the
  next bullet. Personal settings and private-source bindings grant no account pin or
  personal model provider. Decisions are quoted in
  `/home/victor/work/auto_route_20261007/CONTEXT.md`; per-host proof is in the
  receipts `auto-route-20261007/fix/<lane>` and in
  [[wiki/systems/cli-proxy-cpamc-sat-1792-2026-10-02]].
- Other models through Claude Code, Victor 2026-10-25 4:58 PM CT (quoted in
  sources). Every non-Codex, non-Claude model, Kimi and OpenRouter models
  included, runs as a Claude Code backend through the Sats hub. The Claude
  Code CLI keeps its own agent loop and sets `ANTHROPIC_BASE_URL` to the
  host's hub root, without `/v1`. It sends the person's existing hub key as
  bearer and no `X-Sats-Account` header, because OpenRouter catalog models
  route headerless and an AUTO or `OPENROUTER` pin breaks the route. `model`,
  every Claude model variable and the subagent model are pinned to the
  selected hub model, with no fallback model. Upstream keys stay in the hub:
  no client holds an OpenRouter or Moonshot key or calls an upstream
  directly. Muse differs: there Claude Code calls the Muse Code CLI
  (§ Muse Wonderful, Option A), and that route stays as it is. The hub
  accepts Claude Code's Anthropic Messages requests for Kimi and OpenRouter
  models, so these need no second CLI.
  - Support is per model. Anthropic does not support non-Claude models
    behind a gateway, and a catalog listing proves no tool support. A model
    is supported only once live-verified.
  - States, reported separately; none implies the next. Required: Victor's
    rule above. Prepared: a source or config candidate exists, not applied.
    Activated: applied to the live hub catalog, both hubs' price overrides
    and the fleet provider config, and loaded. Live-verified, per host: a
    Claude Code session made a Read-tool round trip on the pinned model
    through the hub, and the hub rows for its `X-Sats-Exec-Id` carry the
    expected identity, provider and exact model and non-NULL cost. A T3
    claim also needs a T3-owned `claudeAgent` canary.

  | Route | Model through the hub | State, 2026-10-25 |
  |---|---|---|
  | `claude_openrouter_free`, a T3 `claudeAgent` instance | `cohere/north-mini-code:free`, headerless OpenRouter catalog | Prepared, not activated. Instance enabled in `fleet-provider-sync` candidate `1a0f3be9` (supersedes `c3dc7d51`), local to the F-D authoring clone, not pushed or applied; installed on no host. Hub catalog live on F-D and the MBP standby (`/v1/models` lists it). Explicit zero-rate price key installed on both hubs, not loaded. Not live-verified |
  | `claude_kimi_api`, a T3 `claudeAgent` instance | `moonshotai/kimi-k3.1-pro`, headerless OpenRouter catalog, standard `moonshotai/mxfp4` endpoint pinned | Prepared, not activated. Disabled in candidate `1a0f3be9` until Victor approves paid Kimi spend; installed on no host. Catalog entry live on both hubs and price key installed, not loaded, as above. The endpoint pin loaded on F-D; the standby shows no load line, so the served endpoint is unproven until the first paid cell. Not live-verified |
  | `KIMI_VICTOR` subscription, `kimi-k3.1-pro` and `kimi-k3.1-pro-highspeed` | `X-Sats-Account: KIMI_VICTOR` | Current through the OpenCode provider `sats-kimi` ([[wiki/systems/sats-hub-account-lifecycle#Kimi (KIMI_VICTOR, 2026-10-25)]]). No Claude Code route: Kimi's Coding Plan terms cover personal interactive use and exclude non-interactive automation and reverse-proxy sharing, and its Messages path books provider `claude` until a hub release ([[wiki/systems/sats-router-usage-sources#Prices]]) |
  | DeepSeek V4.1 Flash voting reviewer | `deepseek-v4.1-flash` | Current through OpenCode ([[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]). No Claude Code backend prepared: unpriced rows and no tool check |
  | `glm-5.3-flash`, `minimax/minimax-m3.1-flash:free` | F-D catalog only | Not prepared; no price key |

  - An existing OpenCode route for one of these models stays current until a
    Claude Code backend for the same model is live-verified and the route's
    owner swaps it. Nothing has migrated yet.
  - Activation gates. The hub catalog hot reload changes production config,
    and a `fleet-provider-sync` deploy applies T3 config fleet-wide; both
    take the production-action gate. Candidate `1a0f3be9` confirms each new
    instance's model listing from T3's own provider status cache
    (`<base>/caches/<instanceId>.json`) over the existing SSH route, so its
    apply issues no T3 session and needs no credential approval. Its
    `--refresh-session` and `--mode prove` paths still issue a two-minute
    `orchestration:read` T3 session, which needs Victor's credential approval
    under Safety gates; so does the live timer at `a49bf45`, which issues that
    session on any pass that rewrites an opencode or CLI wrapper or the
    opencode config, until the candidate is applied.
    Price overrides load at the 24-hour refresh or a Victor-approved
    restart. A paid model needs Victor's spend approval; a new upstream
    credential needs his credential approval.
  - Catalog and price state, 2026-10-25 22:55Z: the F-D catalog lists 5
    OpenRouter models (`/v1/models` 220 ids), the standby 176 ids. The
    installed overrides (`pricing_overrides.yaml` sha256 `4c21986b…f99d`)
    load at the natural 24-hour refresh with no restart, about 2026-10-26
    16:47Z on F-D and 16:52Z on the standby gateway; a failed LiteLLM feed
    at that refresh skips them and retries hourly. Receipt:
    `canon-v2-nested-design-and-claude-code-providers-20261025/hub_model_activation`.
- AUTO account choice, Victor 2026-10-17 ("Whatever account has the soonest
  reset gets taken from that account. That should be codex and claude auto
  too." and "the weekly reset."). In every AUTO pool (`AUTO_CLAUDE`,
  `AUTO_CODEX`, `AUTO_MUSE`) the hub sends a new, unbound conversation to the
  eligible account whose weekly window resets soonest. For Claude and Codex
  that rank key is the general all-models weekly window. Resets within 60 s
  of the earliest reset tie; then more weekly quota left, then less 5-hour
  use, then the smaller account id; the 5-hour reset time never ranks (a
  5-hour window only gates). An account with any applicable window at 0% is
  skipped, even when it resets soonest. A bound conversation keeps its
  account only while that account stays eligible. The hub reselects it when
  a fresh reading shows any applicable window at 0%, after a capability
  miss, when its weekly window has rolled with no new sample while a
  verified account exists, and on failover after a classified limit error.
  AUTO_CLAUDE and AUTO_CODEX already ranked this way; AUTO_MUSE does since
  hub release `muse-da355fc16efa`, live 2026-10-17 21:22Z. For a Meta
  account only `subs_usage.weekly` ranks. `subs_usage.window` is the 5-hour
  gate when its duration is exactly 300 minutes, and an account-wide gate
  otherwise, including when no duration is given. A Meta account with no
  fresh quota reading (over 15 minutes old, failed, or just after a hub
  restart) ranks after the accounts that have one, by fewest usage-ledger
  tokens in the last 5 hours, ties in registry order. Quota and ledger sources:
  [[sats-router-usage-sources#Muse Auto pool (hub rows, 2026-10-17)]].
  Receipts: `~/work/muse-hub-usage-20261017/{g8-soonest-reset,c9-review,r2-release}`.
- Claude inference, Victor 2026-10-12: every new Claude call uses Claude Auto,
  `claude_auto` in T3 and `AUTO_CLAUDE` at the hub, with the task's model and
  effort passed explicitly. Dedicated gather providers, manual `CLAUDE_*`
  pins and direct-auth CLI helpers are retired for new calls. Keep accounts,
  credentials, metadata probes, usage reporting and running children's loaded
  settings. Retire future selectors through their reviewed owner; saved
  instructions alone do not prove runtime enforcement.
- Codex agent calls, Victor 2026-10-12: use Codex Auto, `codex_auto` in T3
  and `AUTO_CODEX` at the hub. A task's named reason no longer authorizes an
  agent-selected `CODEX_*` pin. This supersedes earlier agent account-pin
  instructions. Explicit human T3 picker choices remain available; they
  grant no pin authority to agents or their workers.
  Former fixed-account wrapper controls: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Fixed-account wrapper controls, moved 2026-10-14]].
- Keys: each call books under its person's own hub key
  (`CREW_CLIPROXY_KEY_<PERSON>`, names only), except on the shared binding
  Victor approved on 2026-10-07 (`auto_route_20261007/CONTEXT.md`, ~14:45):
  the Framework `sats` login (Archimedes seat) sends Rachel's key and books as
  `rachel-mba`, whoever the work is for. That 2026-10-07 decision also covered
  every caller on the Mac mini. Since 2026-10-10 the two mini T3 servers send
  their owner's key (CL03, RP6): Victor's `:3774` sends Victor's key, Rachel's
  `:3776` sends Rachel's key, each through its own `claude_auto`/`codex_auto`
  homes (`<base>/claude-home`, `<base>/codex-home`) and the owner wrapper
  `<base>/bin/claude-auto`. The shared mini `~/.codex` still sends Rachel's
  key and the shared `~/.claude` Victor's (Victor's key since the 2026-10-07
  ~16:52 item 1B lane); other callers of those shared homes book under them.
  Details: [[wiki/systems/cli-proxy-cpamc-sat-1792-2026-10-02]] mini row.
  Two different things check accounts, and neither
  does work for a person. The router's Claude and Codex quota probes on
  `:8332` are metadata GETs with each account's own sign-in, every 120 s
  (Claude at most every 5 min), and call no model. Its Meta probe is a POST
  to Meta's key endpoint, each account at most every 5 min, staggered, and
  also calls no model; details in
  [[sats-router-usage-sources#Muse Auto pool (hub rows, 2026-10-17)]]. The `sats-account-keepalive` timer runs every
  5 hours (00/05/10/15/20, plus 10 min after boot). The Framework service
  runs `--check-only --page`, with metadata reads and no model call, per the
  2026-10-12 caller audit F5. Preserve this coverage check. Its dormant
  per-account Claude inference branch is retired under the all-Claude AUTO
  rule; an AUTO ping cannot prove coverage of every account.
  Where a host runs the full keepalive, it sends one pong per `on` Codex
  account straight to `:8330` as `<prefix>/gpt-6-astra` (no effort) under
  the shared `sats` key. AUTO cannot carry it because AUTO refuses an
  explicit prefix. This per-account path remains a named exception under
  review (audit 2026-10-10 § 5 item 2, A12 R6). Codex behavior is unchanged;
  this repair neither expands nor fixes that exception. Other hosts need
  their own service readback. Host-to-key bindings live in
  [[wiki/systems/sats-router-usage-sources]].
- Pools: membership lives in the hub registry
  `~/.config/sats-hub/accounts.yaml` with owners `mason` and `victor`, so both
  pools include Mason's accounts. A pool moves to another account when one
  runs out. A pool membership change needs Victor's approval. On 2026-10-07
  `AUTO_CODEX` held five accounts (`CODEX_MAIN`, `CODEX_ONLY21MIL`,
  `CODEX_SATS21M`, `CODEX_VICTOR_SATS21M`, `CODEX_MASON`) and `AUTO_CLAUDE`
  three (`auto-route-20261007/audit/hub`). `AUTO_CLAUDE` has held four since
  2026-10-08 18:30 CDT: `CLAUDE_GMAIL`, `CLAUDE_SATS21M`, `CLAUDE_ONLY21MIL`
  (owner `victor`) and `CLAUDE_MASON` (owner `mason`). `CLAUDE_ONLY21MIL`
  joined with no approval record; Victor approved it on 2026-10-10 (Victor
  ruling 2026-10-10 04:23 CT, relayed by Sats; audit
  `/home/victor/work/model-routing-audit-clean-2026-10-10/RESULT.md` § 5
  item 1).
- Claude-side route: each host's `~/.claude/settings.json` sets
  `ANTHROPIC_BASE_URL` to the hub, `X-Sats-Account: AUTO_CLAUDE` in
  `ANTHROPIC_CUSTOM_HEADERS`, and an `apiKeyHelper` that returns the person's
  key. A Claude process reads it at start, so terminal sessions, native agents
  and T3 `claude_auto` children started after a settings change use the new
  route. A session already running at the change, and every native agent it
  starts, keeps its loaded route until it ends. Running children are not
  restarted for this instruction change. After the
  2026-10-07 flip no process was restarted, so running T3 sessions stayed on
  `:8330` (`fix/claude_fd_victor`). Framework's `victor` home sent Claude
  straight to `:8330` with no pool from 2026-10-04 until
  `fix/claude_fd_victor` moved it to `AUTO_CLAUDE` on 2026-10-07; the `sats`
  home, the kid profiles and the Mac mini moved the same day
  (`fix/claude_sats_kids`, `fix/mini`).
- Historical Claude exceptions kept on 2026-10-07: the Claude desktop app's
  Code tab and Claude Remote Control ran on their own sign-in. The
  2026-10-12 direct instruction, "All claude calling needs to go through
  claude auto.", supersedes those exceptions for supported future inference
  routes in this task. Their existing sign-ins and accounts remain, and this
  source change does not reload unrelated active sessions. Cursor Cloud Agents
  and Self-hosted Machines stay enabled ("I want those to be available if
  needed later") and are not a default work vehicle. The 2026-09-22 Muse
  Spark OpenRouter seat is retired (§ Muse Spark). App chat under a person's
  own sign-in follows the identity model in
  [[wiki/systems/sats-hub-account-lifecycle]]. The remaining Cursor exceptions,
  the T3 Codex fixed-account picks below, Cursor outside the 13 Pro choice recorded in the
  next bullet (CLI default `grok-4.6`, the F-D T3 instances `cursor` and
  `cursor_linencloset`, Cloud Agents, Self-hosted Machines) and the Grok Bot
  app and its routines on Cursor are under review (audit 2026-10-10 § 5
  item 2) against the 2026-10-10 AUTO rule above. Victor has not ruled on
  them, so each stays as written until he does.
- Cursor in the 13 Pro T3, named exception, Victor 2026-10-10 (NOTES answer 3
  in the pack): the 13 Pro desktop T3 `cursor` instance runs on the Cursor
  plan of the desktop app's account (`proof-of-work@only21mil.xyz`, Victor's),
  after Victor clicks "Sign in with Cursor" in that T3 once; no
  `CURSOR_API_KEY`. Sign-in and a working Cursor turn are pending: the
  instance read `error/unauthenticated` at the 2026-10-10 review (R1b) and
  stays pending until verified. Cursor's custom endpoint (desktop "Override
  OpenAI Base URL") is called from Cursor's servers, which cannot reach the
  tailnet-only hub, and no Cursor surface sends the `X-Sats-Account` header
  (`/home/victor/work/t3-providers-usage-2026-10-10/audit/C02-cursor-cliproxy-endpoint.md`,
  verdict NO; its T3 mechanism is corrected in its 2026-10-10 note and by
  `audit/C03-t3-cursor-driver-source.md`: T3 runs the Cursor SDK, which has no
  endpoint override). It is not a default work vehicle; V2 children keep
  the targets in [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Mechanism: [[wiki/systems/sats-pm-visible-swarm]]
  § T3 Code children, bullet "Cursor".
- T3 Codex fixed-account choices remain opt-in: `codex` shown as
  "CodexSats566" (`CODEX_MAIN`), `codex_sats21m`, `codex_only21mil`,
  `codex_victorsats21m` and `codex_mason`, each on its matching `CODEX_*`
  pin. Choosing one by name in T3 is the human user's choice.
  Agent-created work outside T3 uses `codex_auto` or `claude_auto`.
  For every V2 child and reviewer, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]],
  including its Muse AUTO route. Preserve person-key booking.
  New Claude selections use `claude_auto`; root retires future selection of
  `claude_gmail`, `claude_mason` and `claudeAgent` through their reviewed
  owner without deleting accounts, credentials or running sessions.

Dated 2026-10-07 fixed-account receipt, which grants no current agent pin: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Fixed-account receipt 2026-10-07, moved 2026-10-14]].

- T3's own text generation (thread titles, commit messages, PR text): T3
  settings carry no `textGenerationModelSelection`, so T3 falls back to its
  schema default, the `codex` instance on the `CODEX_MAIN` pin with
  `gpt-6-luna` at `low` and no service tier (audit 2026-10-10, A10). That is
  a gap against the AUTO rule above and the retired Luna route. The target
  follows the misc row in [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]], set as
  `textGenerationModelSelection` in `~/.t3-nightly/userdata/settings.json`
  (audit C2, a config change not yet made).
- Sol speed, Victor direct, 2026-10-20 (`sol-standard-40-20261020`). Every
  GPT-6.1 Sol (`gpt-6.1-sol`) agent at every effort uses Standard on every
  harness and transport, inside and outside T3, for parents, workers,
  reviewers and bot turns (computer use excepted: it stays on the fast tier under its pin, § Computer-use correction). Set V2 `serviceTier: "default"`,
  hub `service_tier: "default"`, or the CLI's supported Standard/default
  equivalent (`--service-tier standard` for the foreground wrapper,
  `-c service_tier="default"` for Codex). An unset CLI tier is equivalent
  only when its effective default is verified Standard. Explicit selection
  clears inherited Fast. Fast (`priority`) runs only when Victor names Fast
  for that specific task. Earlier lane exceptions, frozen candidate records
  and copied options grant no tier override to a new launch. This supersedes
  the 2026-10-17 high-priority default — the computer-use ultrafast pin of 2026-10-20 is not superseded: it stands as the sole fast-tier exception (reaffirmed 2026-10-21); dated evidence remains history. Keep model, effort, account and
  private-scope choices with their existing owners. Compare readback with
  the current task decision; a mismatch is a route failure, an absent
  readback is unverified. Source text, installed defaults and running-session
  adoption require separate evidence. Other GPT models retain their defaults.
- Historical speed rule (its Sol portion is superseded by the Sol speed
  bullet above; current for the other GPT models and for Claude fast mode):
  every non-Sol GPT model in the Codex pool requests service tier `priority`
  (Codex calls it Fast) on every call, on every seat and whatever the
  transport. The 2026-10-07 source also named Sol (Victor, 2026-10-07,
  widening the 2026-10-03 Sol-only rule; source
  `/home/victor/work/crew_orchestrators_20261007/CONTEXT.md` § "Victor's
  answers after the design repairs, 2026-10-07"). The hub ledger does not yet
  prove the upstream tier: on 2026-10-07 most `victor` Sol rows reported tier
  `default` (`auto-route-20261007/audit/codex_fd`), and build items `F2V1` and
  `ST-S2` in `/home/victor/work/crew_orchestrators_20261007/BUILD_ITEMS.md`
  add the proof. Claude fast mode
  stays off because Victor does not pay for it (Victor, 2026-10-03);
  `fastMode` comes from `settings.json` for terminal launches and from T3
  argv and `--settings` for T3 sessions, with runtime readback required.
- Every new T3 V2 thread and child, master and per-PR orchestrators included, follows [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Transport belongs to
  [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]].
- Main-session model and effort come from each host's
  `~/.claude/settings.json` for terminal launches and from T3's launch
  arguments and settings for T3 sessions.
- For transport invocation, workspace guards, access checks, waiting,
  timeout behavior and the relay commit mandate, read
  [claude_agents/README.md § How the Sol relays run](/home/victor/work/model_routing/claude_agents/README.md#how-the-sol-relays-run).
  § Execution access owns the shared access rule.
  Host hashes and activation receipts belong to
  [[wiki/systems/instruction-surface-registry]].

The prior transport and account record is preserved in
[[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Accounts and transport]].

### Token economics, Victor 2026-10-20

Standing note. The AUTO pools in § Accounts and transport
(`AUTO_CLAUDE`, `AUTO_CODEX`, `AUTO_MUSE`) run on Victor's
subscriptions — great quality, very, very token cheap. Muse
in-app use is pretty token cheap too. **Grokbot is not token
cheap.** Simple and token-efficient designs win, without
sacrificing quality, so shared machinery routes to the cheap
vehicles by design; Sats-side notice and watch work rides the
AUTO lanes. Grokbot's duties under
[[wiki/systems/sats-grokbot-cross-app-protocol-2026-10-20]]
are kept minimal-token: registry row updates and terminal
email only — no polling or watching. A cross-thread or cross-host sweep
(status, settle, lost DONE) is one AUTO lane writing a file; a Grok turn
reads that file and never pages `t3_thread_list`.

The shell status writer is victor-vault `tools/grokbot-thread-status/`.
Its per-host file is `~/.local/state/grokbot-thread-status/status.json`.
Read its `complete` and `generated_at` fields before using it; a partial or
stale file proves neither a complete inventory nor settlement eligibility.
The tool README owns invocation and activation requirements; lifecycle
authority stays in [[wiki/systems/sats-pm-visible-swarm#Settle on finish, archive after one week]].

### Sidebar names

On T3 Code, the Claude Code CLI and Claude Desktop, on every Sats machine,
every agent the Claude seat starts shows its wrapper and real model in its
name or label. Inside T3 Code, the V2 row also covers every V2 child that the
Claude Code, Codex, OpenCode or Cursor harness starts (Victor, 2026-10-07:
"I need to see the subagents/swarms model and reasoning").

| Agent | Label |
|---|---|
| Native Opus producer (`opus-medium`, `opus`, `opus-xhigh`, `designer`) | `Opus 5.5 Medium`, `Opus 5.5 High` or `Opus 5.5 Xhigh` |
| Native gather (`explorer`) on Claude Auto | `Opus 5.5 High` |
| Native Sonnet producer (`sonnet`, outside T3 Code only) | `Sonnet 5.5 Medium` or `Sonnet 5.5 High` |
| Sol through a relay (`sol`, `sol-xhigh`, `sol-medium`) | `Sonnet>Sol 6.1 High`; `Sonnet>Sol 6.1 Medium` for `sol-medium` |
| Sol computer use relayed from the Claude seat | `Sonnet>Sol 6.1 High` (pinned, Victor 2026-10-20); the relay runs it on `AUTO_CODEX` at the fast tier under § Claude Code agent definitions |
| V2 child inside T3 Code, every harness | Real model and effort selected by [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]], with no wrapper; reviewers add `review` |
| Per-PR V2 orchestrator thread a master opens | Real model and effort from the same owner, then the PR's branch, for example `Sol 6.1 High · pr:<branch>` |

A native definition carries the label at the start of its `description`. A
Workflow agent's `label` starts with it, for example
`Opus 5.5 High · produce:heartbeats`. Every V2 child's `delegate_task` `title`
starts with it, for example `Sol 6.1 High · extract:inventory` or
`Sol 6.1 High review · correctness`.
V2 targets Sol directly, so no Sonnet wrapper appears. The label reports the
effort routing chose. The T3 routing owner selects T3 profiles. Outside T3, each seat's table selects its profiles and the Sol producer by-name
gate remains in § Claude Code agent definitions. Which surfaces display
the label is unverified until the install check records it.

### Claude Code agent definitions

| Definition | Wrapper | Worker model | Worker effort | Sandbox rule | Account rule | Service tier rule |
|---|---|---|---|---|---|---|
| `opus-medium` | native | `claude-opus-5-5` | `medium` | producer | Claude | fast mode off |
| `opus` | native | `claude-opus-5-5` | `high` | producer | Claude | fast mode off |
| `opus-xhigh` | native | `claude-opus-5-5` | `xhigh` | producer | Claude | fast mode off |
| `designer` | native | `claude-opus-5-5` | `high` | producer | Claude | fast mode off |
| `explorer` | native, full tools/MCP | `claude-opus-5-5` | `high` | scoped gather producer | Claude Auto/AUTO_CLAUDE | fast mode off |
| `sonnet` | native | `claude-sonnet-5-5` | `medium` | producer | Claude | fast mode off |
| `sol-xhigh` | `claude-sonnet-5-5` `medium` relay | `gpt-6.1-sol` | `high` | producer | Sol, `AUTO_CODEX` | computer use priority; other assignments standard |
| `sol` | `claude-sonnet-5-5` `medium` relay | `gpt-6.1-sol` | `high` | producer | Sol, `AUTO_CODEX` | computer use priority; other assignments standard |
| `sol-medium` | `claude-sonnet-5-5` `medium` relay | `gpt-6.1-sol` | `medium` | producer | Sol | standard |

Canon `agents/claude/` holds these nine definitions; each file's `description`
is the line the Claude Code seat lists for that agent type.
`agents/claude/install.sh` copies them into `~/.claude/agents/` and
removes the retired names in § Retired.

`sol` and `sol-medium` stay installed and run only when Victor asks for
them by name (Victor, 2026-10-03). Select assignments by class from
§ Claude Code routing, Victor 2026-10-03.
Every GPT-6.1 Sol call outside computer use, at every effort, follows Standard under § Accounts and transport: `sol-medium` and `sol`'s by-name assignments pass `--account AUTO_CODEX` and no tier flag, which the foreground wrapper resolves to Standard. Computer use runs on the fast (priority) tier under § Computer-use tier and route, Victor 2026-10-20 and 2026-10-25: the relays pass `--account AUTO_CODEX --service-tier priority`.
`sol` runs computer use as above; its by-name rule covers every other assignment. `sol-xhigh` keeps its name for briefs that call it, runs at `high` like `sol` (Victor 2026-10-23) and splits the same way by task class: computer use runs as above, and any other assignment, by name only, runs on Standard and `AUTO_CODEX`. `sonnet` runs only outside T3 Code, for the classes in § Claude Code routing.

These definitions are the vehicle outside T3 Code for production and repair;
review runs only through T3 (review-and-babysit § Vehicles, Victor 2026-10-23).
Inside T3 Code,
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] selects profiles;
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]]
owns how it starts.

The sandbox column selects producer access from § Execution access.
Account and service-tier columns select route rules from § Accounts and transport.
For relay mechanics and the result contract, read
[claude_agents/README.md § How the Sol relays run](/home/victor/work/model_routing/claude_agents/README.md#how-the-sol-relays-run).
For installed definitions, host hashes and runtime activation, read
[[wiki/systems/instruction-surface-registry]].
[[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]] selects reviewers, and every review runs in T3 (review-and-babysit § Vehicles). A definition whose effort differs from the selected effort is unavailable.
Replacement history and staged source receipts are in
[[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Claude Code agent definitions]].

### Retired

Victor, 2026-10-23 12:57 PM CT via Sats: the `reviewer` and `reviewer-opus`
agent definitions and the `produce-review` Workflow are retired, because every
review runs as T3 V2 children (review-and-babysit § Vehicles). No seat starts
them. `agents/claude/install.sh` deletes `agents/reviewer.md`,
`agents/reviewer-opus.md` and `workflows/produce-review.js` from each Claude
config dir it processes, `~/.claude` and every account dir alike. Their last
canary record is
`/home/victor/work/policy-reviewer-pins-high-20261016/CANARY-RECEIPTS.md`.

Older historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Retired]].

### What this supersedes

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#What this supersedes]].

## Sonnet 5.5 T3 non-coding children, Victor 2026-10-09

Status: amended 2026-10-10 by Victor (Lane B thread D04, D22, D23; root thread 22:01Z "on t3 v2 do sol instead of sonnet"). Inside T3 Code no child runs Sonnet. The former T3 tiered Sol routing is superseded by [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Sonnet 5.5 runs only on the Claude Code seat outside T3 Code, through the native `sonnet` definition on `AUTO_CLAUDE`, for light unmatched work, docs, summaries and extraction that is the deliverable. The original 2026-10-09 ruling and its scope: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Sonnet T3 children ruling 2026-10-09, moved 2026-10-14]].

Victor 2026-10-10, D04, D22 and D23: on the Claude Code seat outside T3 Code, light unmatched work, docs, summaries and extraction that is the deliverable use native `sonnet` with `claude-sonnet-5-5` on `AUTO_CLAUDE` through the Sats hub. Effort is `medium` by default, `high` only with a stated reason, never `xhigh`, `max` or `ultra`. This amends the 2026-09-24 Sonnet producer restriction for those classes on that seat only. Never use OpenRouter or the `anthropic/claude-sonnet-5-5` catalog form.

Scope IN: light unmatched work, docs, summaries and extraction that is the deliverable, on the Claude Code seat outside T3 Code.
Scope OUT: all other work follows § Claude Code routing.

Guardrails (MUST — checks, not suggestions):
1. Effort `medium` by default, `high` only with a stated reason, never `xhigh`, `max` or `ultra` (D23). Work that needs more goes to Opus 5.5 by tier.
2. API shape (gotchas-bugs lane, 2026-10-08): never force `tool_choice`
   (returns 400); default sampling params only — no custom temperature/top_p/top_k,
   no `thinking: disabled`, no assistant prefill; conversations append-only
   (editing earlier turns invalidates thinking blocks); ~30% tokenizer tax vs older
   models, so realized savings are ~35%, not 50%.
3. Pre-flight: 1-token probe of `claude-sonnet-5-5` on the hub before first use
   (probe passed 2026-10-09).

Rollback (one line): route the IN-scope classes to Claude Opus 5.5 by tier and mark this section SUPERSEDED.

## Haiku 5.5 subagent class, Victor 2026-10-09

Haiku gather spawning and selection are retired, Victor 2026-10-13 09:20.
This heading stays for existing links and historical receipts. Active gather
on Claude Code and Codex outside T3 uses ordinary Claude Auto Opus 5.5 `high` under § Current gather procedure; Grok-launched gather follows § Grok-launched lanes, Victor 2026-10-18. Inside T3, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
Auxiliary Haiku title/compression uses retired with Hermes on 2026-10-24; their dated gates are history.
Dated Haiku gather installation recipes are retired. Preserve their evidence;
use § Current gather procedure for new gather children.

### Compaction and gather effort, Victor 2026-10-12

Victor, 2026-10-12 (direct to Lane B, paraphrase): every harness, subagents
included, compacts on its session model at the point the harness uses by
default. Opus 5.5 on Claude Code compacts where Claude Code normally does for
its 1M window, and Sol 6.1 on Codex where Codex defaults. The hub Haiku
compaction rewrite and the 390K overrides are retired. Gather effort is `high`
on every harness and machine; the gather model is set in § Current gather
procedure. Running sessions keep the settings they loaded; new sessions pick
these up.

The dated ruling, which named Haiku as the gatherer before 2026-10-13, and its
application snapshot: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Compaction and gather ruling 2026-10-12, moved 2026-10-14]].

Current gather retains Victor's October 12 full capability requirement:
gather runs with every tool, MCP included, under § Current gather procedure.
Outside T3 its profile remains Claude Auto Opus 5.5 `high` on Claude Code
and Codex and Sol 6.1 `high` with Standard in Grok-launched lanes; inside T3 the
profile comes from [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
`claude_haiku_gather` stays enabled. The r4 proof
(`/home/victor/work/haiku-gather-purge-20261013/staging/r4_t3/PROOF.md`)
shows Codex Auto V2 children use it on F-D and F13. Removal needs a new
Victor decision. The dated general Haiku V2-use exception is superseded for new T3
assignments by [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]; preserving provider availability
does not select Haiku for a new T3 role. Outside T3, auxiliary Haiku uses remain; shared or unproven providers on other hosts stay enabled.
Former hot-removal evidence and plan, which grant no removal authority: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#claude_haiku_gather removal plan, moved 2026-10-14]].
Claude Code `explorer.md`
has no `tools:` line, and the codex-workflow gather class passes no `--tools`
list and no `--strict-mcp-config`.

Victor then removed every token cap on runs (paraphrase: no token caps on any
runs right now). The 90K gather guard, its T3 void-on-breach check, gather
unit sizing by token count and the Codex `tool_output_token_limit` overrides
are gone; each harness uses its own defaults. Every 90K, 90,000 or token-cap
rule below is superseded.

AUTO_CLAUDE must offer Haiku 5.5 at every effort advertised for the model,
per `/home/victor/work/hub-haiku-5-5-20261012/ISSUE.md`. This auxiliary
capability requirement is separate from the current Opus gather route. The current
registry omission causes a serving failure even on `claude_auto`; removing
the dedicated provider alone cannot repair it. Root owns registry repair
and correlated replies/ledger checks. Catalog listing is not serving proof.

Dated Haiku routing and compaction receipts, 2026-10-09 to 2026-10-11: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Historical Haiku routing and compaction receipts]].

### Hermes auxiliary vehicle and gather scope (retired 2026-10-24)

History (Hermes retired 2026-10-24, Victor): former Hermes compression and
title-generation routes, gates and exceptions no longer apply.

Parent-feeding gather on Claude Code and Codex outside T3 uses Claude Auto Opus 5.5 `high` under § Current gather
procedure; Grok-launched lanes use § Grok-launched lanes, Victor 2026-10-18. Inside T3, use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].

Gather scope IN: parent-feeding gather on Claude Code,
Codex and T3. T3 profiles come from [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]];
the Claude Auto profile below applies to Claude Code and Codex outside T3, and
§ Grok-launched lanes, Victor 2026-10-18 to Grok-launched lanes. Gather includes file search, code location, log sweeps, test-run
summaries, inventories, classification, triage, source-cited extraction,
codebase exploration and bounded summaries that cite their sources.
Each gather task is narrow, with one deliverable.
Gather may run scoped shell commands and write or edit the output files its
brief names. Shell and write access do not authorize repairs, secret reads,
external sends, production actions or new workers.

Dated parent-compaction and gather rollout, 2026-10-11 to 2026-10-12: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Historical parent-compaction and gather rollout]].

### Current gather procedure

Scope OUT: code writing or repairs as the task; plans, RCA and hard debugging;
review, babysit and verdicts; orchestration and scheduling; shared-quota side
effects; knowledge-heavy factual recall; design. These tasks follow the
harness table outside T3 and the T3 routing owner inside T3. Gather shell/write tools grant no broader
approval or spawning authority.

Extraction precedence: inside T3, all parent-feeding and deliverable extraction
uses [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Outside T3, parent-feeding extraction on Claude Code or Codex
uses Claude Auto Opus 5.5 `high` through the vehicles below. Deliverable
extraction remains Sonnet 5.5 `medium` on Claude Code and GPT-6.1 Sol
`medium` on Codex and OpenCode. Grok-launched gathering and
extraction, parent-feeding or deliverable, use Sol 6.1 `high` with Standard
under § Grok-launched lanes, Victor 2026-10-18. Muse app threads on
Codex or Claude Code follow § Who does what.

Current gather vehicles; pass each selected model and effort explicitly:
- Claude Code outside T3: native `explorer`, `claude-opus-5-5`, `high`,
  through the owning Claude Auto process and AUTO_CLAUDE. It inherits full
  tools, MCP included; `explorer.md` carries no `tools:` restriction.
- Codex outside T3: codex-workflow class `gather`, foreground
  `claude -p --model claude-opus-5-5 --effort high` on AUTO_CLAUDE.
  Gather passes no `--tools` list or `--strict-mcp-config` and has full tools,
  MCP included, with no imposed token or context cap. Reviewer restrictions
  remain separate. Verify the current runner's source/install binding before
  applying a package; prose corrections do not authorize replacing newer code.
- Grok-launched lanes outside T3: an AUTO_CODEX lane, `gpt-6.1-sol`, `high`,
  with Standard, `service_tier=default` set explicitly; full tools, MCP included.
- Inside T3 on every harness: the owning V2 orchestrator, master or per-PR, starts a V2 child under
  [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] and reads back the target, model, effort and tier.
  Keep full tools/MCP and scoped output writes; no dedicated gather provider.

Victor 2026-10-13 19:01 r4 exception keeps Haiku model availability. Its T3
assignment rule is superseded by [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. The r4 proof above confirms
`claude_haiku_gather` is shared, so it stays enabled. Removal needs a new
Victor decision. Shared or unproven providers on other hosts also stay enabled.
Retire only gather jobs, routes and defaults. General model lists, accounts,
credentials and running children remain unchanged. This gather retirement
grants no provider-removal, auth-change or service-restart authority.

The interim Haiku-serving fallback is retired. Outside T3, Opus 5.5 `high` on Claude
Auto is the ordinary Claude Code and Codex gather route. Inside T3, use the T3 routing owner. If that route is refused or unavailable,
the parent reports the failure with its evidence and continues independent
authorized work. A stale Haiku gather override requires correction to this
route. No dedicated gather provider, `CLAUDE_*` pin, direct OAuth or silent
model substitution is permitted. Auxiliary Haiku serving repair and host
acceptance remain their own release assignment under ISSUE.md.

Every gather brief names its question, paths or prepared evidence, permitted
commands and output writes. It requests path/line/exact-text facts, misses
with patterns and searched paths, and files read with line ranges. Commands
and writes stay within that brief; commands that could hang carry a timeout.
Network access needs authorization.
Exclude key, token, credential and secrets files and other private scope.
The child starts no agents, subagents, workflows or delegated tasks. If
judgment or wider scope is needed, return the evidence and `needs_parent`.
The parent re-checks any claim that gates an action. Full tools do not
grant new permissions or dispatch authority. Each harness uses its own
context defaults; token estimates, line counts and ledger peaks impose
no artificial stop or evidence-void threshold.

Dated gather tool and G2 receipts: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Historical gather tool receipts]].

### Current gather checks

- Outside-T3 AUTO lane on Claude Code or Codex: `sats-account AUTO_CLAUDE claude -p --model claude-opus-5-5 --effort high`.
- Grok-launched lane outside T3: AUTO_CODEX, `gpt-6.1-sol`, `high`, Standard, `service_tier=default` set explicitly (§ Grok-launched lanes, Victor 2026-10-18).

Guardrails:
1. Gather uses [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] inside T3. Outside T3 it uses
   Claude Auto Opus 5.5 `high` on Claude Code and Codex, and Sol 6.1 `high`
   with Standard in Grok-launched lanes. Every delegation passes
   that effort explicitly. The class default does not clamp the API's
   advertised efforts; bot-launch floors and Victor's `max`/`ultra` gate
   still apply. Session compaction uses the session model at the harness
   default, with the hub rewrite and 390K overrides retired.
2. No run has an imposed token or context cap. Use each harness's defaults.
   Retired 90K/100K guards, size-based reroutes and void-on-breach ledger
   checks do not apply. The model's physical context window remains an API
   capability, not an added gather policy limit.
3. API shape: temperature and top_p stay at defaults, never top_k
   or forced tool_choice. Keep thinking on and conversations append-only.
   The parent reports an observed model/route failure with its evidence and
   follows § Current gather procedure. Outside T3, a model other than the
   lane's selected gather model, or a direct-auth/pinned call, is not gather
   AUTO acceptance. Inside T3,
   acceptance requires the exact profile in the T3 routing owner.
4. Evidence, not a verdict: the parent re-checks any gather claim that gates
   an action. Whether a gather result gets review follows review-and-babysit
   § 1; producer model does not decide it. Full tools/MCP preserve brief scope, private
   boundaries and the rule that a child starts no further work.

Acceptance checks, owned by the parent:
1. Confirm the selected model/effort and correlate a returned reply with
   the selected AUTO ledger row: outside T3, AUTO_CLAUDE on Claude Code and
   Codex or AUTO_CODEX in Grok-launched lanes; inside T3, the route in
   [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. A picker entry or reply alone does not prove
   the requested model or account route. Auxiliary Haiku serving checks under
   ISSUE.md remain separate and are not prerequisites for Opus gather.
2. Confirm full tools/MCP and scoped read/write behavior on a fresh child
   where runtime acceptance is required. Saved argv or one host's receipt
   does not prove every host's tools.
3. Confirm only gather jobs, routes and defaults retire;
   `claude_haiku_gather` stays enabled per the r4 proof above. Preserve
   outside-T3 auxiliary Haiku use and unrelated settings/runs. Preserved
   provider availability is not a new T3 assignment route. Provider removal requires a new Victor decision.
   Root uses the host's supported lifecycle; no blanket restart requirement.
   A routing change confirms by its owner's per-host readback.

Background-helper enablement gate, audit C6 gate 4, retained as a current
gate. This applies to background helpers separately from gather's high
default:

4. Background helper calls stay off Haiku 5.5 until the hub helper profile recognises it
   and a transport rule rejects or rewrites `thinking: disabled` and pins `medium`
   (Claude Code helper calls send thinking disabled).

Dated C6 and gate-5 comparisons and the former rollback recipe: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Historical C6 comparison]].

Ledger fields (audit C10) are live since 2026-10-10 10:16 CT: every new row carries `recording_version` 2, `client` and `pool`, and pinned rows carry `pin`. `reasoning_effort` is recorded only when the request carries `thinking` type `adaptive` or `auto` with `output_config.effort`, the shape Claude Code sends; a request with effort and no `thinking` field records a blank effort, as every C6 Haiku row did. `upstream_service_tier` records the tier the hub sent upstream, not the tier served (PACK/i/I11 K4 finding 3, K6 findings 1-2).

## Opposite-model review, 2026-09-29

Reviewer selection and dispatch ownership follow [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]].
Review-and-babysit owns rounds, findings, repairs and non-writing proof.

Superseded routes:
[[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Superseded review routes]].

## Claude effort one tier up, 2026-09-24

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Claude effort one tier up, 2026-09-24]].

## GPT-6 Sol for Codex, 2026-09-22

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#GPT-6 Sol for Codex, 2026-09-22]].

## Fable 5.1 restricted, 2026-09-22

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Fable 5.1 restricted, 2026-09-22]].

T3-upstream reviewers follow [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]] and its retained panel exception.

## Muse Wonderful, Victor 2026-10-14

Victor 2026-10-14 ~20:32 CT, via Grok Bot: Muse Wonderful is a supported
model on Victor's Muse Code subscription.

This section covers Muse Code and its models. The Muse app owns the workspace VMs; see [[wiki/systems/naming-glossary#Prose terms]].

- Model id `muse-wonder-full-1.0`, effort `high`. Verified on F-D
  2026-10-14 from the T3 Muse catalog cache (`~/.t3-nightly/caches/muse.json`),
  the T3 settings favorite (`provider: muse`) and a 2026-10-13 T3 public turn
  `muse/muse-wonder-full-1.0/high` that returned `MUSE_OK`
  (`~/work/muse-hub-20261012/BOARD-log.md`). Evidence file:
  `/home/victor/work/routing-muse-20261014/MUSE-MODEL-ID.txt`. The catalog
  also lists `muse-wonder-1.0`, `muse-spark-1.3` and `muse-spark-1.2`; none
  of them is a default.
- Transport (Victor 2026-10-16 20:20 CT fleet standard, via Sats; pool
  Victor 2026-10-17): Muse Wonderful runs through the CLIProxyAPI hub on F-D
  `127.0.0.1:8332` (`:7443` from other hosts), like Codex Auto and Claude
  Auto. Every Muse Code call, T3 included, sends `X-Sats-Account: AUTO_MUSE`,
  model `muse-wonder-full-1.0`, effort `high`, and authenticates with the
  person's own hub gateway key, never on argv or in logs; without it the hub
  returns 401 `Gateway key required`. Victor's key comes from
  `~/.local/libexec/sats-hub-key` (the same source as the Codex `sats_router`
  provider). The canon review runner (`/home/victor/work/canon-review-lane.sh`)
  sends it as `Authorization: Bearer` to `/v1/chat/completions`, checks the
  response `model` and logs the hub's `X-Sats-Selected-Account`.
- Muse Auto is the hub pool `AUTO_MUSE`. It holds exactly two Meta Muse Code
  accounts: `victor.vogel@only21mil.xyz` (META_VICTOR_CODE) and
  `sats@only21mil.xyz` (META_VICTOR_CODE_2, added 2026-10-17). Both sit in the
  hub's priority pool next to the Claude and Codex accounts. A new
  conversation goes to the account § Accounts and transport (AUTO account
  choice) picks. The conversation's binding is keyed by the first of
  `X-Sats-Session`, `x-tbh-session-id`, `x-meta-ai-gateway-session-id` or
  `prompt_cache_key`; when it keeps or leaves its account follows that same
  bullet. A Meta limit error is a 429, or `rate_limit_exceeded`/quota with
  `resets_at`; a 401 or 403 passes through unchanged. A limit error that names no reset holds the account for 5
  minutes, and a fresh quota reading ends any Meta hold early. Pool live since
  hub release `muse-dfc3127262d4`, 2026-10-17 12:30 CT
  (`~/work/muse-hub-usage-20261017/r1-release/RESULT.md`); the 5-minute hold
  since `muse-da355fc16efa`, 21:22Z (it was 2 minutes). Fixed
  `META_VICTOR_CODE` or `META_VICTOR_CODE_2` pins are for per-account probes
  only. Accounts: [[sats-hub-account-lifecycle]].
- T3 Muse (Victor 2026-10-17: "I will only use it in t3 code nightly") uses
  Muse Auto on every backend of the three laptops: Victor's F13 Pro,
  Mason's F13 Pro and Rachel's MacBook Air. Rachel's MacBook Air is
  installed but not yet on `AUTO_MUSE`; per-backend status lives in the
  fleet page linked below. Each backend launches the Muse Code CLI through a `muse-via-hub` wrapper that loads the hub key into the
  CLI's environment. The CLI settings carry `endpoint_transport` to the hub
  with `X-Sats-Account: AUTO_MUSE`. Contributor mode stays ON under
  § Contributor mode through the hub, 2026-10-19 rule. The hub answers the CLI's
  `/muse-code/*` catalog and search calls with 403, so catalog refresh and
  web search do not work on this route. Per-backend paths and receipts:
  [[t3-code-fleet#2026-10-17: T3 Muse on Muse Auto, every backend]].
- T3 thread starts follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Review uses follow
  [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]], including its named exceptions.
- A Claude, Codex or other non-Muse agent that needs Muse runs the Muse Code
  CLI (`muse-via-hub exec --json`) and keeps Contributor ON (Victor, Option A,
  2026-10-23). It does not send `AUTO_MUSE` from its own client. Procedure:
  [[t3-code-fleet#2026-10-23: Claude agents run Muse Code headless (Option A)]].
  The fixed-pin per-account probes above are unchanged. Open decision for
  Victor: whether the hub refuses callers other than the Muse Code CLI, on
  `AUTO_MUSE` only or on the `META_*` pins too, which would end those probes.
  Until his GO, the hub refuses no caller by client.
- Muse Wonderful has no default outside-T3 reviewer route. Outside T3, it is the default for no other class. The Muse Spark debate
  seat stays retired (§ Muse Spark) and the Muse-app rule is unchanged.

## Contributor mode through the hub, 2026-10-19 rule (verified 2026-10-21)

**Rule (2026-10-19):** contributor mode stays ON for both Meta accounts
(`victor.vogel@only21mil.xyz` / META_VICTOR_CODE and
`sats@only21mil.xyz` / META_VICTOR_CODE_2) and must work through the Sats
hub. Disabling it, or re-adding the `*contributor*` exclusion to a Meta
account's `excluded_models`, is a failed fix.

The failure it fixed: on 2026-10-19 T3 Muse stopped responding entirely —
the hub returned 400 "Native Meta requires an unaliased Muse model ID;
Contributor models are excluded" after 10 provider attempts. The fix was in
the hub: the gateway runs the contributor-opt-in build (release
`contrib-optin-608da283aef3`) and neither Meta account's `excluded_models`
carries the `*contributor*` entry.

Verified live 2026-10-21 (desk RCA, reported 2026-10-22T03:40Z): both Meta
auth files on framework-desktop carry `excluded_models = []`, with the
pre-fix backups (the `*contributor*` state) preserved beside them;
contributor calls (`muse-wonder-full-1.0-contributor`,
`muse-spark-1.3-contributor`) book status 0 / failed 0 through the hub; and
the Window 1 hub restart that evening preserved the behavior on the new
build ([[wiki/systems/sats-hub-three-windows-2026-10-21]]).

## Muse Spark for the chief-of-staff design debate, 2026-09-22

The OpenRouter Muse Spark debate seat was retired on 2026-10-07; the hub
keeps that seat outside both AUTO pools. This does not retire native agents
inside the Muse app or change `Muse auto`. Victor's October 10 app/harness
boundary is in § Who does what. Retired debate record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Muse Spark debate seat record, moved 2026-10-14]].

## Computer-use host, 2026-09-14

Victor makes `victors-macbook-pro` the default execution host for all computer
use across runtimes: native GUI, browser interactions, simulators and devices,
screenshots, and vision. This includes authorized administration and prompt
submissions in both existing Grok Bot accounts, Victor/Sats and
Rachel/Archimedes. Select the correct existing account and confirm its visible
identity before reading or acting. Each account keeps its own canon, memory,
credentials, and permissions.

Run the computer-use driver on the MBP even when the parent runs on Framework
or Yoga. Grok uses its registered MBP machine through ListMachines and machineId
when available; other runtimes use their maintained remote MBP route. Confirm
current reachability, the intended target, and driver availability before the
interaction. A task explicitly targeting another host's local GUI or an attached
device keeps that target. If MBP execution cannot reach that target, report the
specific limitation. Victor clarified the Sats host order on 2026-09-20:
MBP is primary and Framework Desktop is secondary. Use Yoga or a MacBook Air
only when absolutely necessary for the authorized task and through an approved
host-specific route. A secondary route still requires the intended account,
reachable target, and supported driver. This Sats preference grants no access
to another person's MacBook Air, account, or private data.

Emulator and simulator exception, 2026-10-10. Victor in the crew-test T3
thread: "Are you going to test it on the emulators on the Mini? That should be
the standard." Android emulators and iOS simulators used for app verification
default to `victors-mac-mini`, including tasks that name no host. Targets and
fallbacks live in [[wiki/systems/emulator-verification-standard]] § Hosts and
targets. All other computer use keeps the MBP default and host order above.
Since 2026-10-20 (Victor) the mini is one host of a pool with the M5 Pro MBP,
the M3 MBP and the Yoga: [[wiki/systems/emulator-verification-standard]]
§ Device fleet, Victor 2026-10-20. Apple builds, signing, services and release authority stay under
[[wiki/systems/fleet-machine-roles]].

Framework retains its computer registration, account access, live canon
storage, and services. MBP canon clients use the
established live access to Framework within their own scope. This routing
change authorizes no account migration, credential copying, app restart, new
device pairing, or unrelated send. Model and effort selection continue under
this page and the active runtime adapter. Host authority is
[[wiki/systems/fleet-machine-roles]]; Grok procedure is
[[wiki/systems/grok-bot-yoga]].

## Sats design standard, 2026-09-13

Victor: "If you need to design anything use claude -p and have Fable 5.1 on
high do anything in design. Please make this the standard for all UI, UX etc..
design." He added: "I have 2 claude accounts. If one if out of usage, try the
otherone."

Model superseded 2026-09-22: the design route now runs Claude Opus 5.5 at
`high`, per § Fable 5.1 restricted above. The quote above is the 2026-09-13
origin; the transport, account failover and reuse rules below still apply.

Inside T3, design and its implementation follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]],
with reuse and verification rules below preserved. Outside T3,
Claude Code assignments follow § Claude Code routing, Victor 2026-10-03.
That seat has no `claude -p` route, so the foreground Claude CLI transport
below applies only to the Codex harness. OpenCode and other non-Claude seats
hand design work to Codex. Non-design code on those
other seats goes to GPT-6.1 Sol. Reuse of existing
design artifacts, the account failover and the emulator rule apply on every
seat.

On the Codex harness, route UI/UX design,
design specifications, visual exploration, design audits, redesigns,
prototypes' design decisions, and design QA to foreground Claude CLI
`-p --model claude-opus-5-5 --effort high`.
Use `claude-fable-5-1` for design only when Victor asks for it by name.
This external-Claude design route is an explicit exception to the Codex
native-model defaults below. It does not change the current parent
model. On the Claude Code seat, the native `designer` agent (Claude Opus 5.5
`high`) makes the design decisions and writes the HTML, CSS, rendering, game
and prototype code that implements them. On Codex, the foreground Claude
Opus 5.5 `high` worker also implements that code. Computer interaction on every harness
runs Sol 6.1 `high` for ordinary interactions or `xhigh` for difficult or
high-risk verification under § Computer-use correction. Opus judges design
evidence. 3D and Blender work, its computer use included, follows
§ 3D and Blender, Victor 2026-10-18. ProductDesign remains the workflow selector where
applicable; it does not override this model, effort, or transport requirement.
A Claude CLI design worker already launched with this exact profile performs
its assigned design directly; it does not dispatch another copy of itself.
Design QA of a built fix, upgrade or change also needs the emulator run in
[[wiki/systems/emulator-verification-standard]]. On every harness, Sol 6.1
`high` or `xhigh` drives the emulator, simulator or browser and captures
evidence; Opus judges design. For 3D and Blender work, the model that drives
the screen comes from § 3D and Blender, Victor 2026-10-18.

Use existing design artifacts, Fable- or Opus-produced, as the design authority when
Victor supplies or identifies them. Do not commission the same design again
or require another design approval solely to satisfy routing. Send only new
or unresolved design decisions to the design route.

Feed a self-contained design brief through stdin or a private mode-0600 file,
keep the worker in the foreground, and follow the scope's dispatch capacity
and completion rules. Pin both model and effort explicitly. Report the actual
model/effort only when runtime evidence establishes them; no canary is needed.
An unavailable route needs diagnosis.

Claude account failover: `AUTO_CLAUDE` selects the account and moves to
another when one runs out (§ Accounts and transport), so a worker on an
`AUTO_CLAUDE` route runs once and reports the design route failure on
confirmed usage exhaustion. New Claude design calls stay on Claude Auto /
AUTO_CLAUDE with the selected model and effort. Manual account-directory
failover and concrete Claude account pins are retired for new calls under
Victor's 2026-10-12 all-Claude rule. Preserve completed output and resume only
unfinished design work when the route recovers. Continue independent work.

On Framework Desktop, use the normal `/home/victor/bin/claude` wrapper and
the approved common AUTO settings/frontend. Preserve the existing failover
transport. Other hosts resolve their normal Claude Auto route locally;
these Framework paths are not fleet defaults. Authentication, network or
model errors need their own diagnosis and do not establish usage exhaustion.
Do not copy credentials, log in, change auth or read secret material for
failover. Existing account homes and sign-ins remain; a saved instruction
does not prove a running process changed its loaded route.

### 3D and Blender, Victor 2026-10-18

Victor, direct, 2026-10-18 about 10:40 AM CT, in T3 thread `3d6ccc7f`
(Bitcoin theme redo): "Anything done with 3D and blender need to have Opus
5.5 on high or Xhigh,By far the better model for those tasks." At 10:55 AM CT,
asked whether to add it to the T3 routing table: "Yes. and that should be for
all harnesses. Not just t3."

This section is the one owner of the rule. Other sections and startup files
point here.

Every task that involves 3D work or Blender runs on Claude Opus 5.5
(`claude-opus-5-5`) at `high`, or `xhigh` for complex 3D or Blender work.
This holds on every harness and seat, inside and outside T3. It covers 3D
design, scene building, rendering and render scripts, Blender install,
config, GPU audits and ops, and the computer use those tasks need.

Roles. The rule binds production and execution roles: the producer, worker
or child that designs, builds, renders, scripts, installs, configures,
audits or operates. Orchestration and review keep their owners in
[[wiki/systems/sats-t3-and-review-routing]]: the T3 orchestrator rows,
[[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]] for the reviewer, and the T3
upstream PR panel with its fixed members.

Precedence. For these tasks this section overrides every class row that would
send the work to another model (gather, mechanical, ordinary, ops, research,
computer use). It also overrides these computer-use paragraphs, each of which
points here: § Computer-use correction, Victor 2026-09-30, including its D24
paragraph and its split of code authoring from screen operation; the
computer-interaction and emulator sentences in § Sats design standard; the
Codex block's 2026-10-10 computer-use sentence; and item 2 of § Choose for
each assignment. The computer-use host order (§ Computer-use host,
2026-09-14), [[wiki/systems/emulator-verification-standard]] evidence and
every approval gate still apply.

Vehicles. Inside T3, the 3D and Blender row in
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]
binds Opus on `claude_auto` through AUTO_CLAUDE. Outside T3 each harness uses
its existing Opus vehicle: on the Claude Code seat the native `designer` at
`high` or `opus-xhigh` for complex work, on Codex the foreground `claude -p
--model claude-opus-5-5` worker at the chosen effort, and OpenCode
hands the work to Codex.

### Historical design fallback, 2026-09-13

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Historical design fallback, 2026-09-13]].

### Current account-limit handling

Keep a scoped receipt for each account's confirmed usage limit, observation
time, reset time when supplied, and evidence path. Reuse that evidence while
the same limit window remains current; do not repeat calls already known to
fail. Do not infer an indefinite limit when reset time is unknown: revalidate
on the next work session or when evidence suggests capacity returned. At a
known reset, retry the normal Claude design route only when work needs it. A successful
request or other reliable capacity evidence ends that account's exhaustion
state. Resume the Claude design route as soon as it has capacity.

On every Sats seat, record the design route failure and unfinished work.
Do not claim a skipped or rate-limited Claude design review occurred. Existing design artifacts remain
the design authority; limit new decisions to unresolved work. Auth, network, and model errors
do not establish quota exhaustion. Account failover authorizes no credential,
setting, credit, purchase, privacy, release, or service change. It applies only
to Victor/Sats design work, not unrelated family owners.

Account-route provenance: [[wiki/systems/claude-5h-wake]]. This standard grants
no cross-scope access, auth mutation, purchase, release, or deployment authority.
Installation and activation are tracked separately in
[[wiki/systems/instruction-surface-registry]]. Earlier dated routing records
remain history; § Model routing, Victor 2026-09-29 (evening) supersedes their
conflicting design-model, effort, and transport defaults for Sats.

## Codex authority and distribution

Maintain the block below here. Each Victor host's
`~/.config/agent-shared/codex-model-routing.md` links to this page in the local
replica; `scripts/sats-local-render-install.sh` makes and checks that link
([[wiki/systems/sats-agents-md-fleet-assembler#Local render, 2026-10-18]]).
That local file is a bootstrap cache, not a separate policy. Legacy F-D and Yoga routing paths are compatibility
pointers. Codex adapters use the local delivery cache; canon reads follow [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]] item 6, Read path; separate agents never need to
read this Sats canon. Record installation and runtime activation separately in
[[wiki/systems/instruction-surface-registry]].

Current agent account selection follows § Accounts and transport. The two
dated auth and subscription paragraphs below are history, superseded for
agent routing by Victor's 2026-10-12 AUTO instruction. Their direct-login and
fixed-pin exceptions grant no current agent authority. ChatGPT subscriptions
only and no OpenRouter fallback remain required.

Codex auth, Victor 2026-09-25: "All [GPT] accounts should all be with
proxyCLI." Every Codex account, Sats and family, reaches GPT models through
CLIProxyAPI via the Sats router (`:8332` on framework-desktop, `:7443` from
other hosts) with an `X-Sats-Account` header and a helper-command key by
default. A home with a direct ChatGPT login is a rare exception, kept open
only for a stated reason and recorded where it is made (Victor,
2026-09-28). Homes and helpers are listed in the
registry section "All Codex accounts go through CLIProxyAPI, 2026-09-26".

Subscriptions only, Victor 2026-09-28: "Use my subs not open router. That
should be the standard rule." Every GPT worker, computer use
included, uses ChatGPT subscriptions through the Sats router with an
`X-Sats-Account` header: `AUTO_CODEX` by default, an explicit `CODEX_*` pin
when a task names a reason (§ Accounts and transport). Never send GPT-6
work to OpenRouter. The
router has no OpenRouter fallback for a `CODEX_*` request: a 429, exhausted
quota or unknown model returns the error to the caller (check
`router/subs_only_check`, 2026-09-28). Send the bare model name, such as
`gpt-6.1-sol`; an OpenRouter name like `openai/gpt-6.1-sol` fails with 502.
§ Accounts and transport owns AUTO pool membership and account failover.
The Muse Spark debate seat's OpenRouter exception ended 2026-10-07
(§ Muse Spark).

<!-- BEGIN CODEX ROUTING -->
# Codex model routing

Inside T3, load [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] first.
It takes precedence over this projection and selects every T3 role, effort,
tier and reviewer pair. T3 children start under
{{release:policies/shared/sats-pm-visible-swarm.md}} § T3 Code children, Victor 2026-10-07. The defaults and
structured codex-workflow-routing block below apply outside T3 only.

Effective 2026-10-10 outside T3. Applies to all Codex parents and children on every
authorized machine in the Sats/Victor scope. It supersedes prior parent,
light-class and review defaults. Other runtimes and scopes keep their
own rules. Grok-launched Codex lanes follow § Grok-launched lanes, Victor 2026-10-18
instead.
Select speed from
{{release:policies/shared/sats-model-tier-provider-policy.md}} § Accounts and transport.

Execution-access export of the shared rule, Victor 2026-10-01: every new
Sats/Victor agent and swarm uses the supported, already-authorized full
task-access mode. Eligible Sol CLI execution uses `--sandbox
danger-full-access`; reviewer access and flags follow review-and-babysit.
Use only exposed controls, distinguish requested from supported and
runtime-observed access, and disclose unknown or unsupported modes without
bypassing denials. Scope, account/resource/credential permissions, platform
controls, approval, privacy and secret safeguards remain.

Victor, 2026-09-22: "Please make the parent lane. Sol 6 high. Then let's go
with everything else that you recommend. [Make it happen] for all codex
accounts [for] all sats machines." (Parent lane moved to GPT-6.1 Sol `xhigh` on 2026-10-10, Victor items 3 and 4.) Victor, 2026-09-24: no Codex worker runs at
`low`.

Before orchestration, read
{{release:policies/shared/sats-pm-visible-swarm.md}} § Fleet orchestration standard, Victor 2026-10-11.
That section owns dispatch defaults, root-owned codex-workflow inspection,
worker creation, titles and capacity.

Victor, 2026-09-29 (evening): GPT-6.1 Sol (`gpt-6.1-sol`) replaces
GPT-6 Sol as the builder on the Codex harness. Claude Code keeps its own
coding route in
{{release:policies/shared/sats-model-tier-provider-policy.md}} § Claude Code routing, Victor 2026-10-03.
On Codex, Sol also replaces Astra for security, auth, secrets, Bitcoin,
payments, deploys and migrations. Victor, 2026-10-10: all computer use,
including design-related interaction, runs `gpt-6.1-sol` at `high` for
ordinary interactions or `xhigh` for difficult or high-risk verification.
3D and Blender computer use follows § 3D and Blender, Victor 2026-10-18.

Review and babysit follow review-and-babysit (Codex copy). Design keeps its
foreground `claude -p` route on this harness outside T3 Code. Inside T3,
use the T3 routing owner above.

Approved Codex models: GPT-6.1 Sol (`gpt-6.1-sol`), the builder; GPT-6 Sol (`gpt-6-sol`), explicit overrides only; the parent config default is GPT-6.1 Sol `xhigh` (Victor, 2026-10-10, items 3 and 4).
GPT-6 Astra's non-design computer-use exception is retired (Victor,
2026-09-30). GPT-6 Luna's production routes are retired; extraction that is itself the deliverable uses GPT-6.1 Sol `medium`; gather that feeds a parent uses Claude Auto Opus 5.5 `high` (§ Current gather procedure).
GPT-5.6 Sol is retired. Terra stays outside the approved set.

| Work | Model and effort |
|---|---|
| Codex parent lane (config default) | GPT-6.1 Sol `xhigh` |
| Mechanical child work outside gather that feeds a parent: deliverable extraction, digest rebinds, formatting, WIP preservation, bounded checks with a decisive result | GPT-6.1 Sol `medium` |
| High-volume CI fixes, non-design | GPT-6.1 Sol `medium` for mechanical fixes, `high` otherwise (D09) |
| Ordinary child work: non-design code, repairs, docs, research, planning, synthesis | GPT-6.1 Sol `high`; Grok-launched coding: § Grok-launched lanes, Victor 2026-10-18 |
| Hard child work: security, auth, secrets, Bitcoin, payments, concurrency, production deploys, migrations, architecture, hard debugging, large three-way merges | GPT-6.1 Sol `xhigh` |
| Adversarial investigations that gather their own evidence (`verify` class) | GPT-6.1 Sol `xhigh` |
| Per-finding verification | Independent review under review-and-babysit |
| Computer use, every kind | GPT-6.1 Sol (`gpt-6.1-sol`) at `high` for every interaction (pinned, Victor 2026-10-20), at the Fast tier under the computer-use pin (Victor 2026-10-20, reaffirmed 2026-10-21); 3D and Blender: § 3D and Blender, Victor 2026-10-18 |
| Independent review and babysit | review-and-babysit |
| Gather that feeds a parent: file search, inventories, log sweeps, classification, extraction the parent re-checks | Claude Auto Opus 5.5 `high` per § Current gather procedure: codex-workflow class `gather` on AUTO_CLAUDE outside T3 Code; full tools/MCP, no imposed token/context caps; Grok-launched gather: § Grok-launched lanes, Victor 2026-10-18 |
| High-volume triage, and extraction that is itself the deliverable | GPT-6.1 Sol `medium` |
| Design, 3D, graphics, video game design and development, including their UI, rendering and game implementation code and repairs | Claude Opus 5.5 `high`: foreground `claude -p` outside T3 Code; 3D and Blender: § 3D and Blender, Victor 2026-10-18 |

Deliverable summaries follow the harness rows; session compaction follows
the live or pending harness status in § Haiku 5.5 subagent class.
Compaction (Victor 2026-10-12): every harness, subagents included, compacts on its session model at the harness default point; the hub Haiku rewrite and the 390K overrides are retired.

T3 orchestrator profiles follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].

The structured block below records the existing outside-T3 model lists and
class table for codex-workflow. It is not a T3 dispatch source. Dispatch reads this block; prose edits do not change approval.
The gather class selects Opus 5.5 high. The block does not encode
§ Grok-launched lanes, Victor 2026-10-18; a Grok-launched consumer passes that
section's model, effort and tier explicitly. Haiku remains in the general approved
model list for legitimate auxiliary uses outside T3.
Retire Haiku gather jobs and overrides within the gather class only.

Outside-T3 review class entries below describe vehicles only. Reviewer selection belongs to [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]]; these static Opus/Sol vehicles never select the ordinary reviewer. A consumer that cannot bind the selected model and effort is unavailable and must use the skill's recorded route failure/fallback procedure.

```json codex-workflow-routing
{
  "version": 1,
  "codex": {
    "approvedModels": [
      "gpt-6.1-sol",
      "gpt-6-sol"
    ],
    "victorOnlyModels": [
      "gpt-6-astra"
    ],
    "retiredPrefixes": [
      "gpt-6-luna",
      "gpt-5.6-",
      "gpt-5.5",
      "gpt-5.4"
    ]
  },
  "claude": {
    "approvedModels": [
      "claude-opus-5-5",
      "claude-haiku-5-5"
    ],
    "victorOnlyModels": [
      "claude-fable-5-1"
    ],
    "retiredPrefixes": []
  },
  "classes": {
    "mechanical": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "medium"
    },
    "ordinary": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "high"
    },
    "security": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "xhigh"
    },
    "deploy": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "xhigh"
    },
    "verify": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "xhigh"
    },
    "computer_use": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "high"
    },
    "computer_use_hard": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "high"
    },
    "review": {
      "engine": "claude",
      "model": "claude-opus-5-5",
      "effort": "high"
    },
    "codex_review": {
      "engine": "codex",
      "model": "gpt-6.1-sol",
      "effort": "high"
    },
    "design": {
      "engine": "claude",
      "model": "claude-opus-5-5",
      "effort": "high"
    },
    "gather": {
      "engine": "claude",
      "model": "claude-opus-5-5",
      "effort": "high"
    }
  }
}
```

No Codex parent or child that a bot or seat launches runs at `low`; the
floor is `medium`. Victor's own picks in the T3 picker keep every model and
reasoning level (Victor ruling 2026-10-10 04:23 CT, relayed by Sats). `max`
and `ultra` need Victor's explicit request for the task.

Sats/Victor design route: all UI/UX and other design work, 3D, graphics,
video game design and development, their UI, rendering and game implementation
code and repairs, design specification and design QA go to Claude Opus 5.5
`high` (Fable 5.1 until 2026-09-22): foreground Claude CLI
`-p --model claude-opus-5-5 --effort high` outside T3 Code. Inside T3,
use the T3 routing owner above.
Codex keeps non-design code implementation and repairs under the table above. Before
design work, read the Sats design standard in
`[[wiki/systems/sats-model-tier-provider-policy]]` for existing-design reuse,
Claude account failover and account-limit handling.

Choose directly for the task. Diagnose a failure before changing the profile.
No standing escalation moves a Sol child to Astra. When a diagnosed failure
shows the effort was too low, give the repair its own assignment at the next
Sol class effort (`medium` to `high`, `high` to `xhigh`). The parent
explicitly selects each child's model and effort independently of its own
profile and passes both through the supported dispatch controls. The
codex-workflow skill's class table applies this table per worker. Above
`high` outside those rows needs a recorded reason.

The Codex parent lane default is `model = "gpt-6.1-sol"` with `model_reasoning_effort = "xhigh"` (Victor, 2026-10-10, items 3 and 4). F-D victor and MBP `~/.codex` were set that way on 2026-10-10 (mrr-20261010 P1, accepted CP1-r2); other homes and hosts were not checked. Victor decided the parent-lane move on 2026-10-10 (first sentence of this paragraph; audit
`/home/victor/work/model-routing-audit-clean-2026-10-10/RESULT.md` § 5 item 7).

Outside T3 Code, the Claude Code seat's Sol calls pass
`run_foreground_worker.sh --account AUTO_CODEX`, so the Sats hub picks the
subscription account (Victor, 2026-10-02). That leaves each host's Codex
account config, and the account the Codex seat uses there, unchanged.

Confirm effective model and effort from runtime evidence before claiming a
profile. The rollout `turn_context` carries both. Missing evidence is
uncertainty, not a dispatch blocker. Correct an observed mismatch; report an
unsupported profile or actual transport failure.

Parent Mode procedures remain under the scope's dispatch doctrine;
orchestration defaults follow the fleet orchestration owner above.
Substantive review follows review-and-babysit. Model choice changes no privacy boundary, approval, permission, or scope.
<!-- END CODEX ROUTING -->

## Crew app chat turns, 2026-10-10 (retired 2026-10-24)

Retired with Crew on 2026-10-24; grants no current route. Record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-25#Crew app chat turns section body]].

## Hermes authority and distribution (retired 2026-10-24)

History (Hermes retired 2026-10-24, Victor): native Hermes authority and
distribution are retired. Former homes and profiles are dated history only.

<!-- BEGIN HERMES ROUTING -->
# Hermes model routing (retired 2026-10-24)

History (Hermes retired 2026-10-24, Victor): native Hermes bot-turn routing,
auxiliary vehicles and delegation rules no longer apply.

## Family routing and Sats history, 2026-09-08

History (Hermes retired 2026-10-24, Victor): the former family Hermes routing
block is retired for every profile and grants no current route.
<!-- END HERMES ROUTING -->

## Other runtime policy

The following assignment, role, and reasoning rules apply outside Codex
and outside T3 only. Inside T3, use
[[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
Where a rule or row below names Codex seats, it restates the Codex block for
cross-reference; the Codex block wins on any conflict.
When another runtime hands work to Codex, its handoff requirement still
applies and the Codex worker selects its profile under the Codex block above.

Before execution or dispatch for any role, apply § Execution access, Victor
2026-10-01 above through the current executor's supported controls.

### Choose for each assignment

1. Classify actual work through § Who does what. Claude Code non-design
   coding uses Opus 5.5; Codex non-design coding uses Sol 6.1, effort by
   task. Grok-launched lanes follow § Grok-launched lanes, Victor 2026-10-18.
   Other seats run Sol 6.1 by § Sol 6.1 effort by class for coding
   and non-coding work. Design follows § Sats design standard, including
   implementation code and repairs on Opus 5.5 `high`. Gather that feeds a
   parent on Claude Code and Codex outside T3 uses Claude Auto Opus 5.5 `high`
   through § Current gather procedure. Gather may use shell and write tools scoped
   by its brief. Session compaction follows § Who does what.
   Cursor
   is undecided. A code-producing HTML
   report from verified content remains coding. Security, auth, secrets,
   Bitcoin, payments, concurrency, deploys, migrations and architecture
   are hard work.
2. All computer interaction on every harness runs Sol 6.1
   (`gpt-6.1-sol`), `high` for ordinary interactions or `xhigh` for
   difficult or high-risk verification, on the default MBP host. This
   includes design-related browser, GUI, simulator and screenshot work.
   Opus judges design under § Sats design standard. 3D and Blender
   computer use follows § 3D and Blender, Victor 2026-10-18.
3. Outside design, authorized Claude Auto gather and Grok-launched lanes, Codex and other seats run Sol 6.1 by
   § Sol 6.1 effort by class for coding and non-coding work. Claude Code
   outside T3 uses its permitted native Sonnet or Opus class. Inside T3,
   use [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]]. Research lanes use Sol `high` with Standard, hard
   research included (Victor 2026-10-18). Consequential security,
   privacy, authority and architecture analysis is hard; adversarial
   investigators use verify. Session compaction follows § Who does what.
   A read-only command alone does not make work
   coding. The
   Codex parent seats (GPT-6.1 Sol `xhigh` since 2026-10-10; GPT-6 Sol `high` from 2026-09-22) and the Claude Code parent (Claude Opus 5.5 `xhigh` since 2026-10-10) integrate child results, but their profile
   does not change the assignment routes.
4. If the required model is unavailable, report the actual route failure.
   Confirmed Claude usage exhaustion under the Sats design standard's account
   failover means reporting the design route failure on every Sats seat and
   continuing independent authorized work.
   All other unavailable routes retain their existing boundary. Outside
   Claude Code, never swap GPT-6.1 Sol for Opus, Astra or Fable to cover a
   failed code route.
   Never swap Opus for Sol to cover a failed design route on any seat.
   Native Claude coding remains the Claude Code default outside T3. T3
   assignments follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] without silent fallback. Failed Sol computer-use routes cannot be replaced by
   Opus. A wrapper or shell does not change the class.
5. Choose reasoning for that child's task, independently of the parent and
   sibling settings. Consider ambiguity, dependent decisions, strength of the
   completion check, and cost of error, using the guidance below.
6. Pass the exact model and effort in dispatch fields or wrapper flags. Report
   the selected profile in the board item. Do not rely on a default or inherited
   parent effort when an explicit selection is available.
7. Check actual runtime evidence against the selected profile when available
   and run the task's completion check. Record missing or unavailable profile
   evidence as uncertainty; it must not block ordinary dispatch or completion.
   Correct an observed profile mismatch without silently accepting a different
   role or model. A canary is optional diagnostic evidence, not a prerequisite.
   If effort was insufficient, make the repair assignment explicit and select
   greater effort. On Claude Code, select the repair definition through
   § Claude Code routing, Victor 2026-10-03. Review follows the
   review-and-babysit routine.

### Role eligibility

| Role | Model |
|---|---|
| Parent session on the Claude Code seat | Claude Opus 5.5 at `xhigh` (Victor 2026-10-10, item 3) |
| Design work: front-end design, all design, 3D, graphics, video game design and development, including the UI and game code that implements it | Claude Opus 5.5 at `high`: the native `designer` agent on the Claude Code seat, foreground `claude -p` only on the Codex harness; other non-Claude seats hand this work to Codex; 3D and Blender: § 3D and Blender, Victor 2026-10-18 |
| Claude Code production and computer use | Follow § Claude Code routing and § Who does what |
| Coding and non-coding work on other seats, outside design and authorized Claude Auto gather | Sol 6.1 by § Sol 6.1 effort by class; Cursor is undecided |
| Grok-launched lanes outside T3 | § Grok-launched lanes, Victor 2026-10-18 |
| Non-design coding and repairs on Codex | Sol 6.1 by § Sol 6.1 effort by class |
| Adversarial verification outside Claude Code | Sol 6.1, verify class in § Sol 6.1 effort by class |
| Computer use, every kind, on every harness | Sol 6.1 at `high`, pinned (Victor 2026-10-20), at the Fast tier under the computer-use pin (Victor 2026-10-20, reaffirmed 2026-10-21); 3D and Blender: § 3D and Blender, Victor 2026-10-18 |
| Claude Fable 5.1, any role | Only when Victor asks for it by name; record his request on the board |
| Gather on Claude Code and Codex outside T3, through ordinary Claude Auto | Opus 5.5 `high`, full tools/MCP and no imposed token/context caps, per § Current gather procedure |
| Codex and T3 Codex session compaction | Session model at the harness default point (§ Who does what) |
| Claude Code and T3 Claude Code session compaction | Session model at the harness default point (§ Who does what) |
| Separate reviewer and babysit | review-and-babysit |

Review, reviewer selection and repair routing follow review-and-babysit.
Model selection changes no scope, permission, or approval.
Terra remains outside the approved set. GPT-5.6 Sol is retired. No Codex worker runs at `low` (Victor, 2026-09-24); the 2026-09-22 Sol `low` route is retired.

Pin design and Claude Code Opus producer dispatch to `claude-opus-5-5`,
Sol dispatch to `gpt-6.1-sol`, and any permitted Fable use to
`claude-fable-5-1`. A floating `fable` or `opus` alias is not proof of the
version. Check effective version when available; report an observed wrong
version and correct it. Never silently fall back to Fable 5 or another model.

### Reasoning guidance

The orchestrator chooses effort at dispatch. These are starting points, not
fixed effort assignments or a rule that every task uses the same level.

On Claude Code, select the model and effort from § Claude Code routing,
Victor 2026-10-03. Other seats select the class and effort from
§ Sol 6.1 effort by class.

Choose for the hardest consequential part of a mixed assignment. Those two
sections own the effort floor, the `max` and `ultra` gate, design effort and
relay effort.

Codex seats take classes and efforts from the Codex block above. Transport
support does not grant elevated-effort authorization. Select speed by
§ Accounts and transport.

### Claude child effort, 2026-09-22

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Claude child effort, 2026-09-22]].

### Opus 5.5 replaces Astra for Claude-seat dispatch, 2026-09-22

Historical record: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-03#Opus 5.5 replaces Astra for Claude-seat dispatch, 2026-09-22]].

## Evidence and history

Six 2026-09-04 canaries proved staged Astra wrapper transport on Framework
Desktop and Yoga at `low`, `medium`, and `high`. They do not prove support in
the installed wrapper or task quality. Judge effort by task checks and observed
corrections. Read host status in [[wiki/systems/instruction-surface-registry]]
when useful and check the actual dispatch result. Historical proof gaps are
informational; an actual unsupported profile or failed transport requires an
operational fix.

The pre-migration page is preserved unchanged at
[[wiki/archive/sats-model-tier-provider-policy-pre-astra-20260904]]. Its model
tables and historical host records grant no current route. Host/version proof
and rollout status belong in [[wiki/systems/instruction-surface-registry]].
