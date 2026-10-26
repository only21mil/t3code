---
title: Sats T3 and review routing
aliases: [t3-routing, review-routing]
created: 2026-10-18
updated: 2026-10-26
type: system
status: active
tags: [agent-system, decision]
sources:
  - 'Victor direct 2026-10-25 23:52 America/Chicago: temporary Claude-role substitution uses the existing OpenCode Kimi K3.1 Pro route at high until 2026-10-26T06:00:00Z, then only on a fresh Claude usage-limit failure through 2026-11-02T04:52:12Z; [[wiki/systems/sats-model-tier-provider-policy#Temporary Claude to Kimi K3.1 high fallback, Victor 2026-10-26]] owns the rule'
  - 'Victor 2026-10-25 9:29 PM CT GO, "Remove them thn", brief hash-remove-launch-helper-gate-20261025.md sha256 5e01f122: the t3-canon-launch helper is no launch prerequisite; launches use the native T3 tools with this table read from GitHub main. Wrong-model RCA: /Users/m5mbp/work/deploy-gate-github-main-20261025/NATIVE-DOCS-RESULT.md'
  - 'Victor 2026-10-25 4:41 PM CT nested V2 design and 4:58 PM CT "audit and update the canon ... to this design", brief sha256 c38ef22b961e187048ee093fb1c48f1e8ea0d5c8f32a4512c6c31aba6729e207: a master V2 orchestrator thread opens one per-PR V2 orchestrator thread per PR worktree, each with its own delegates; the orchestrator row covers both layers and the per-PR orchestrator runs its PR''s review step. Layer mechanics: [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]]'
  - 'Victor 2026-10-25 4:58 PM CT, same brief: "Also all non codex or claude code models need to be ran through claude code like we did with muse. So Kimi and openrouter need to be set up like this and it needs to run through the hub like everything we do." Rule and route states: [[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]]; the DeepSeek reviewer keeps its current route until a proven replacement (§ Claude Code backends)'
  - 'Sats 2026-10-25 12:56 PM CT item B, lane fleet-token-audit-20261025 (T3 mcp:bd61df73): verify t3_thread_configure and, if it works, record it once here as the method for moving a limit-stuck thread to a working model. Probe mcp:562a9455 worked on an idle thread across providers (§ Move a thread off a model that is out of usage); it makes the 2026-10-18 Muse-exhaustion fallback below launchable for an existing thread'
  - 'Victor 2026-10-25, T3 thread mcp:c24e6f61-4297-4646-8ba1-80053a6175c7: "Take out the requierment completely. I do not like restrictions". Computer-use children route on AUTO_CODEX; the CODEX_MASON or CODEX_MAIN usage pick is removed'
  - 'Victor 2026-10-23 12:31 PM CT via Sats: every T3 thread and delegate_task child starts in build mode, runtimeMode full-access and interactionMode default; both read back, anything else BLOCKED'
  - 'Victor 2026-10-23, retire the reviewer scripts: "Retire the scripts for all harnesess. THey are complicated and cause issues and consiqueses. I want them gone from all machines and harnesses." Review vehicles: review-and-babysit § Vehicles. Brief: /home/victor/work/retire-review-scripts-20261023/BRIEF.md'
  - 'Victor 2026-10-23, finish-once: inside T3 DeepSeek reviews run as an opencode delegate_task child on every lane, replacing the shell-run script (Victor GO 2026-10-20 12:25 PM CT). Concurrency probe: 4 parallel children, 3 overlapping, 2026-10-23T02:35Z, /home/victor/work/t3-native-pilot-20261022/BOARD.md'
  - 'Victor 2026-10-23 11:44 AM CT via Sats: retired two pre-canon review habits: Lightning pinging him on every X review pass or fail, and Sats running her own one-pass reviews. Reviews follow review-and-babysit only.'
  - 'Victor 2026-10-22, T3-native pilot GO: DeepSeek in a T3 upstream PR lane runs as a normal T3 opencode child (variant high, agent review); /home/victor/work/t3-native-pilot-20261022/BRIEF.md'
  - 'Victor direct, 2026-10-20, sol-standard-40-20261020: every Sol 6.1 agent at every effort uses Standard, T3 serviceTier default; Fast only when Victor names Fast for that specific task'
  - 'Victor 2026-10-17 13:23 CT, all T3 threads on every harness: /home/victor/work/t3-routing-v2-20261017/BRIEF.md and DESIRED.json; addendum 1, GPT-6.1 Sol high always priority'
  - 'Victor 2026-10-17 7:09 PM CT: model and routing swaps skip review gates and close on a per-host readback'
  - 'Victor 2026-10-17 8:14 PM CT, direct: /home/victor/work/grok-lane-review-routing-20261017/BRIEF.md'
  - 'Victor 2026-10-18 7:34 AM CT via Sats: the opposite model reviews inside the producer lane'
  - 'Victor 2026-10-18, thread mcp:e2cd539d-ff6f-44b7-9407-88c510b68174: upstream panel Sol 6.1 high fast, Opus 5.5 high, Muse Wonder Full high; Muse left the panel 2026-10-20'
  - 'Victor 2026-10-18 10:40 and 10:55 AM CT: 3D and Blender row, owned by policy § 3D and Blender'
  - 'Victor 2026-10-18 4:55 PM CT GO via Sats, r6 rows 1, b and g adopted: Grok-launched standard lanes share this role table; the Muse-out-of-usage Opus 5.5 high fallback is a target, HOLD until the launcher supports it'
  - 'Victor 2026-10-18 Sol tier correction, /home/victor/work/sol-tier-rca-20261018/BRIEF.md: Fast is serviceTier priority; ultrafast only as an explicit, time-bounded, Victor-approved override named in the launch brief; frozen candidate-specific review routes preserved; readback compared with the current lane decision'
  - 'Genesis relaying Sats 2026-10-18 9:41 PM CT, /home/victor/work/sol-tier-rca-20261018/ACCOUNT-ADDENDUM.md: ordinary Sol children use codex_auto/AUTO_CODEX, not the direct codex instance; account route checked apart from tier'
  - 'Victor 2026-10-19, thread mcp:4f23c61a-f237-4ad3-aacb-ccbf8d6da1fe: add DeepSeek V4.1 Flash via hub/OpenRouter to review-and-babysit, ordinary and upstream'
  - 'Victor 2026-10-20 7:59 AM CT via Sats: "Sol-produced work is reviewed by Opus and DeepSeek, and Opus-produced work by Sol and DeepSeek, all voting. The T3 upstream panel is Sol, Opus and DeepSeek, with no Muse." Replaces the 7:07/7:08 ordinary-pair rule. Muse Wonderful left review-and-babysit for usage on 2026-10-18'
  - 'Victor 2026-10-20 8:51 AM CT GO via Sats: "Work from producers other than Sol or Opus is reviewed by Sol, Opus and DeepSeek, all voting." Replaces the HOLD for other producers'
  - 'Victor 2026-10-20 8:57, 8:59 AM CT and Sats 9:20 AM CT via Hash: DeepSeek is a full voting reviewer in every canon line; delete the 32,000 output cap (DeepSeek runs on the model defaults, no new caps); a failed DeepSeek vote is a HOLD; fix the shared OpenCode store failure. Victor 9:45 AM CT via Sats: keep the T3 delegate_task route and isolate the store per T3 opencode child. Victor 11:25 AM CT via Sats: DeepSeek waiver until its fix is proven. Victor GO 2026-10-20 12:25 PM CT via Sats and Hash: DeepSeek route change, inside T3 too through scripts/deepseek-cli-review. Receipts: /home/victor/work/deepseek-voting-install-20261020/RESULT.md'
  - 'Victor 2026-10-20 3:06 PM ET via Sats: DeepSeek restored as a voting reviewer, standard and upstream, after the route proof (/home/victor/work/deepseek-reviewer-restore-20261020/tests/STEP1-RESULT.md); the 11:25 AM CT waiver ends'
  - 'Victor 2026-10-24 2:35 PM CT: "When you open T3 threads do it in with Opus 5.5 on high instead of muse." 2:36 PM CT: "With claude auto." Grok Bot-started orchestrators move from Muse Wonder Full to claude_auto claude-opus-5-5 effort high; Muse app starts unchanged. Brief: /workspace/briefs/hash-t3-launch-opus-startup-check-20261024.md'
  - 'Victor 2026-10-24 3:56 PM CT via Sats: "Move the Muse-app row to Opus 5.5 too". Muse app-started orchestrators move from Muse Wonder Full to claude_auto claude-opus-5-5 effort high, the Grok Bot default'
  - 'Victor 2026-10-24 4:24 PM CT via Sats: "Move Mason and Rachel thread starts to Opus 5.5 too". Mason and Rachel own-scope T3 thread starts move from Muse Wonder Full to claude_auto claude-opus-5-5 effort high through AUTO_CLAUDE'
  - 'Victor 2026-10-24 6:43 and 6:59 PM CT: review scope, owned by review-and-babysit § 1. His OpenRouter key refill at 6:43 PM CT retires the 10:23 CT temporary DeepSeek skip'
  - 'Moved out of sats-model-tier-provider-policy on 2026-10-18 (canon-fix batch 2). Verbatim quotes: [[wiki/archive/sats-model-tier-provider-policy-history-2026-10-18]]'
confidence: high
owner: sats
---

# Sats T3 and review routing

This page owns two choices: the model, effort and tier for every T3 role, and
the reviewer model for every review and babysit round. Load it when you start
a T3 thread, dispatch a T3 child, select a reviewer, or move a thread whose
model is out of usage. review-and-babysit
owns the review process and its scope (review-and-babysit § 1). V2 mechanics live in
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]];
the master and per-PR orchestrator layers and who starts what live in
[[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]].
Every other model choice lives in [[wiki/systems/sats-model-tier-provider-policy]].

## T3 routing, Victor 2026-10-17

This table covers every T3 thread on every harness, for every person,
Victor, Mason and Rachel included. It overrides older T3 harness profiles,
startup splits, gather routes, standard-tier defaults, reviewer panels and
signed routing projections. This role table also governs Grok-launched
standard lanes; other outside-T3 producer routes and other scopes retain their
existing owners. Outside T3, other non-review model and effort selection stays
with the policy. The Sol tier rule is
[[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]], Sol
speed; its T3 spelling and readback are under Binding and readback below.

Before selecting a Claude row, apply
[[wiki/systems/sats-model-tier-provider-policy#Temporary Claude to Kimi K3.1 high fallback, Victor 2026-10-26]].
That owner alone holds the dated substitution, its exact Kimi target and its
automatic restoration and expiry. It changes no Sol, DeepSeek, computer-use or
other non-Claude selection.

| Role | Model | Reasoning | Mode / route |
|---|---|---|---|
| T3 V2 orchestrator: the master thread and each per-PR orchestrator thread it opens, every seat and person; Victor's explicit per-task pick overrides the default for the threads it names | GPT-6.1 Sol | high | V2; Standard (non-priority); AUTO_CODEX; launch fields below |
| Coding children | Claude Opus 5.5 | high; xhigh only for complex coding | AUTO_CLAUDE |
| 3D and Blender production and execution children, computer use included. Scope and the effort choice: [[wiki/systems/sats-model-tier-provider-policy#3D and Blender, Victor 2026-10-18]]; orchestrator, review and upstream rows unchanged | Claude Opus 5.5 | high or xhigh, per that owner | AUTO_CLAUDE |
| Gathering / filing / misc children | GPT Sol 6.1 | high | Standard, serviceTier: "default", AUTO_CODEX |
| Light writing, docs and X drafts children in Grok-launched work | Claude Opus 5.5 | high | AUTO_CLAUDE |
| Computer-use children ([[wiki/systems/sats-model-tier-provider-policy#Computer-use correction, Victor 2026-09-30]]). 3D and Blender computer use follows the 3D row | GPT-6.1 Sol | high (pinned) | `codex_auto`, Fast, serviceTier: "priority" (the standing computer-use exception), AUTO_CODEX (Victor 2026-10-25) |
| Review + babysit | GPT-6.1 Sol `gpt-6.1-sol` or Claude Opus 5.5 `claude-opus-5-5`, by producer, and the DeepSeek row below, under § Review routing, Victor 2026-10-17 20:14 CT | high | Sol: `codex_auto`, Standard, serviceTier: "default", AUTO_CODEX; Opus: `claude_auto`, Claude fast mode off, AUTO_CLAUDE |
| T3 upstream PR review + babysit | Panel, Victor 2026-10-20: GPT-6.1 Sol `gpt-6.1-sol`, Claude Opus 5.5 `claude-opus-5-5` and the DeepSeek row below, all three in parallel each round; all must ACCEPT | high for all three | Sol: `codex_auto`, Standard, serviceTier: "default", AUTO_CODEX; Opus: `claude_auto`, Claude fast mode off, AUTO_CLAUDE |
| Voting reviewer, every review round, ordinary and upstream | DeepSeek V4.1 Flash, `sats-openrouter/deepseek-v4.1-flash` (OpenRouter `deepseek/deepseek-v4.1-flash-1017`) | high (`variant: "high"`) | Inside T3 a `delegate_task` child: `opencode`, `agent: "review"`, so its finish wakes its parent ([[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]], Victor 2026-10-23). A seat outside T3 hands the review to a T3 thread under review-and-babysit § Vehicles. Sats hub (127.0.0.1:8332) to OpenRouter, with no token cap. This route is a Victor-approved exception to the AUTO-only rule, for this reviewer only. |

A delegate of either orchestrator layer, or another task thread, uses its
task-type row; when none fits, it uses Sol 6.1 high Standard.

The orchestrator default covers Grok Bot, Muse app, Codex and Claude Code
starts, including Mason's and Rachel's own-scope starts. Their scopes carry
no Grok Bot start requirement. A master passes each per-PR orchestrator these
launch fields explicitly, or Victor's pick when it names that PR or the whole
objective, and reads the thread back under Binding and readback. Victor's 2026-10-25 2:19 PM CT ruling replaces
the October 24 Opus launch defaults; his words are in [[log]].

Default launch fields for the orchestrator row only, read back from the MBP T3 instance's
`t3_thread_configuration` and `orchestrator_capabilities` on 2026-10-25:

```json
{
  "modelSelection": {
    "instanceId": "codex_auto",
    "model": "gpt-6.1-sol",
    "options": [
      { "id": "reasoningEffort", "value": "high" },
      { "id": "serviceTier", "value": "default" }
    ]
  },
  "runtimeMode": "full-access",
  "interactionMode": "default"
}
```

The configuration readback showed the instance, model and high effort, with
no tier option set. The catalog reports `serviceTier` default `"default"`,
with values `"default"`, `"priority"` and `"ultrafast"`. Non-priority is the
explicit `"default"` option above; pass it to override an inherited fast tier.
The tier actually served is unverified by these configuration/catalog reads.

Binding and readback:

- Launch with the native T3 tools: `t3_thread_launch` for a master or
  per-PR orchestrator thread, `delegate_task` for every other child. Read
  this table from GitHub main under
  [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]]
  item 6, Read path, and pass the role's row as explicit fields: provider
  instance, model and every option (`modelSelection` on `t3_thread_launch`,
  `target` with `providerInstanceId` on `delegate_task`), plus `runtimeMode`
  and `interactionMode`. T3 fills an omitted provider, model or mode from
  the caller, so a child sent without `target` runs on its orchestrator's
  model. The default launch fields above serve the orchestrator row only.
  `message` and `workspaceStrategy` are the launch keys; T3 silently drops
  `prompt` and `workspace`. A main-thread launch returns a non-null `runId`
  and status `preparing`; missing readback stays pending.
- Model ids are `muse-wonder-full-1.0`, `claude-opus-5-5` and `gpt-6.1-sol`.
  T3 instances are `muse`, `claude_auto` and `codex_auto`, routed through hub
  `AUTO_MUSE`, `AUTO_CLAUDE` and `AUTO_CODEX`. Agent-launched children and
  reviewers use only these instances, plus the DeepSeek reviewer's `opencode`
  instance, the dated Claude substitution's existing `opencode` /
  `sats-kimi/kimi-k3.1-pro` target, and a live-verified Claude Code backend
  under § Claude Code backends. A fixed-account instance such as `codex`
  (CodexSats566, `CODEX_MAIN`) stays a human pick under
  [[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]]; a
  tier override, a frozen route or an earlier lane exception never grants one.
- Use the option names `orchestrator_capabilities` advertises. Pass effort
  explicitly. Pass every Sol 6.1 launch, parent or child, the tier the Sol
  speed rule selects as `target.options.serviceTier`, which overrides
  inherited options: Standard is `"default"`, Fast is `"priority"` and
  Ultrafast is `"ultrafast"`. Record a Victor Fast instruction in the launch
  decision, and read back the tier against the current task decision, not
  merely the request. Claude fast mode stays off.
- Before each launch, write the lane decision from this table: provider
  instance and its account route, model, effort and Sol tier, plus any valid
  override or cited frozen route. Send a
  request equal to that decision. Read back each thread's model, effort,
  provider and Sol tier, plus runtimeMode and interactionMode at thread
  start, with `t3_thread_configuration`, and compare the readback with the
  lane decision. Every thread and `delegate_task` child requires runtimeMode
  `full-access` and interactionMode `default` (build); anything else is
  BLOCKED. Any other difference is a route failure; a missing readback field
  is unverified and the launch is not accepted. Check the account route
  apart from the tier: derive it from the read-back instance through the
  mapping above and record it as derived; the readback does not show the
  underlying account, so that stays unverified. Record requested settings
  apart from observed runtime evidence.
- A required profile that cannot be bound is HOLD, naming the unsupported control.

Routing swaps get no review (review-and-babysit § 1). They are DONE only after
a per-host readback of the effective configuration. Approval, publishing,
privacy and safety gates remain.

V2 transport and its HOLD: [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]].
Reviewers have no outside-T3 route (review-and-babysit § Vehicles).

### Claude Code backends

Non-Codex, non-Claude models run as Claude Code backends through the hub
([[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]],
Other models through Claude Code; that owner holds each route's state). No
role in the table defaults to one.

- DeepSeek reviewer, intended versus current. The intended route is a Claude
  Code backend. None is prepared for DeepSeek, so the `opencode` row above
  stays current. Swap it only after a Claude Code backend for the same model
  is live-verified under that owner, then read back the swap per host. A
  failed or missing replacement never removes the DeepSeek vote.
- The prepared `claudeAgent` instances `claude_openrouter_free` and
  `claude_kimi_api` are installed on no host. Launch one only when Victor or
  the brief names its model and the policy lists it live-verified.
- Readback for such an instance: provider instance, model equal to its
  pinned backend model, and the served model in the hub rows for the run. T3
  lists the bundled Claude models on every `claudeAgent` instance and takes
  effort options from its Claude catalog, so a mid-thread model change can
  leave the pin; the hub rows are the proof.

### Move a thread off a model that is out of usage

A send runs on the thread's current model selection. Prompt text that names
another model changes nothing: on 2026-10-25 a send to F13 Pro thread
`f07163de` said "this turn runs on claude_auto" and the run stayed on `muse`.
When a thread's run fails because its pool has no usable account
(`429 no_eligible_account`, or a usage-limit error naming a reset) and the
reset has not passed, move the thread before the next send. A send on the same
selection gets the same refusal, and the provider driver retries it inside the
run (Muse: 10 attempts over about 4 minutes).

1. Let the thread go idle: wait for its run to end, or stop it with
   `t3_thread_interrupt`. Configure is proven only on an idle thread.
2. Call `t3_thread_configure` with `threadId` and `modelSelection`
   `{instanceId, model, options}` from the orchestrator default above for a
   master or per-PR orchestrator thread or the task row for a child, unless
   Victor names a per-task choice. For a Claude role inside the dated
   substitution window, use the exact Kimi high target from
   [[wiki/systems/sats-model-tier-provider-policy#Temporary Claude to Kimi K3.1 high fallback, Victor 2026-10-26]]
   instead.
3. Read back `t3_thread_configuration` under Binding and readback: instance,
   model, effort, runtimeMode `full-access` and interactionMode `default`.
4. Send. T3 inserts a provider handoff that carries the thread's context to
   the new provider.

Configure leaves the title as it was, so the title still names the old model.
Proof: probe thread `mcp:562a9455`, 2026-10-25 13:00 to 13:04 CDT, moved idle
from `codex_auto` Sol to `claude_auto` Opus, and its next run answered on Opus
with context carried.

### Review routing, Victor 2026-10-17 20:14 CT

This section selects the reviewer model for T3 V2, including the T3 thread a Grok Bot lane hands its review to. Grok Bot orchestrates its lanes and hands each review round to a T3 thread that follows these rules. The T3 role table above also governs Grok-launched standard
lanes; other outside-T3 producer routes and other harnesses' non-review roles
keep their owners. Victor's intent (8:14 PM): have a different model review
the work than the one that did it.

Reviewers (Victor 2026-10-20 7:59 and 8:51 AM CT):
Sol-produced work is reviewed by Opus and DeepSeek, and Opus-produced work by Sol and DeepSeek, all voting. The T3 upstream panel is Sol, Opus and DeepSeek, with no Muse. Work from producers other than Sol or Opus is reviewed by Sol, Opus and DeepSeek, all voting.

Every voter must ACCEPT. Record the producer model from candidate runtime
evidence. Split a scope Sol and Opus both produced, by producer. The upstream
panel runs in parallel each round; panel dispatch and rounds follow
[[wiki/systems/t3-upstream-pr-lanes#Panel]].

Dispatch (Victor 2026-10-18 7:34 AM CT, 2026-10-23 and 2026-10-25): review is
part of the producer lane's own review-and-babysit step, and its reviewers run
only in T3. Inside T3, the V2 orchestrator that owns the work starts them,
DeepSeek included, under
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]]:
for a PR, its per-PR orchestrator. A delegate starts no reviewer or other
child. A lane outside
T3, Grok Bot lanes included, starts no reviewer and hands each review round to
a T3 thread under review-and-babysit § Vehicles.

Read back the selected model, effort, AUTO provider/account and Sol tier,
keeping requested settings apart from observed evidence. A missing required
route is HOLD; no same-model substitution. These routes grant
no new approval, publishing, privacy or resource authority. Source publication
does not prove launcher installation or adoption by already-running lanes.
