---
name: fleet-dispatch
description: >-
  Load when choosing a lane or thread, launching, writing a brief, monitoring or
  relaying a task.
---
Installed path: /home/box/agent-data/workflows/fleet-dispatch/SKILL.md. What a bot does itself is in grok-fleet-rules.

Owners in canon, under Agent-Shared `knowledge/wiki/systems/`. Read the section; do not copy it.
- Owner bot and route per job, and lane rules: `grok-routing-table.md` and its § Lane delivery contract. T3 or headless: `sats-pm-visible-swarm.md` § T3 scope.
- T3 behavior: `sats-pm-visible-swarm.md` § T3 scope. Task models, effort and launch settings: `sats-t3-and-review-routing.md` § T3 routing. Headless model and effort: `sats-model-tier-provider-policy.md` § Grok-launched lanes.
- Nested V2 (master thread, per-PR threads, delegates): `sats-pm-visible-swarm.md` § Fleet orchestration standard, Nested V2 layers, and § Workspace; each thread's delegate ceiling: § Worker cap; who opens and watches each PR: `t3-upstream-pr-lanes.md` § Open the PR and § PR watch.
- Before a root launch or uncertain-launch retry: `sats-pm-visible-swarm.md` § Check before launch.
- The brief and splitting: `sats-pm-visible-swarm.md` § Brief contract and § Roles and readiness.
- Steering and settling a launched thread: t3-orchestrator-prompt § Steps, Steer and Follow and finish. Every stopped thread's notice, its receipt and native child suppression: `task-notices-and-reporting.md` § Terminal self-report.
- Headless launch command: `cliproxy-spawn-skill-2026-10-07.md` § Launch recipe. Lane check-ins: `lane-milestones-and-stall-watchdog.md` § Delivery check-in and lane holds.
- Titles, registry rows and no-touch: `sats-grokbot-cross-app-protocol-2026-10-20.md`.

1. Route. Hand specialist work to its owner bot. T3 work gets one master V2 orchestrator thread per objective, launched under t3-orchestrator-prompt; each PR and related leg becomes that master's child, never a second root (§ Check before launch). An X posting lane (`sats-lane-launch`) writes its Swarm section under `grok-routing-table.md` § Lane delivery contract and keeps x-posting's one executor helper. An outage: run § Check before launch within two minutes, briefed "restore live service without restart" (hub restarts need Victor's GO, `grok-core-rules-2026-10-14.md` rule 3).
2. Brief. Write one objective brief for the master thread or lane under `sats-pm-visible-swarm.md` § Brief contract. The T3 launch template is in t3-orchestrator-prompt; headless additions stay in `grok-routing-table.md` § Lane delivery contract.
3. Launch. Apply the cross-app protocol before launch. Canon writes follow `agent-shared-victor-vault-auto-push.md` § Current contract item 1. T3 work launches under t3-orchestrator-prompt, Launch and Read back. Headless work the scope owner permits runs `sats-lane-launch --preflight` with the exact arguments, then the same command without `--preflight`. A refusal names the conflict; fix it, then retry. New work for a finished lane follows `sats-pm-visible-swarm.md` § Roles and readiness, Steering.
4. Record the launch locally: lane or thread ID, owner, objective, harness, model, effort and service tier as requested and as read back. This is the local launch record the cross-app Ownership test reads.
5. On a T3 event, read the master thread's chat report-out under `task-notices-and-reporting.md` § Report-out standard and verify its evidence. A headless event uses RESULT.md and MILESTONES.log under § Terminal self-report. Each event gets one check-in under § Delivery check-in and lane holds; a passed Due by is progress evidence for that check-in, not a stop. Report BLOCKED only for a named missing input, failure or approval, and send its stop handoff under § Terminal self-report. Acceptance follows fleet-review; settlement follows `sats-pm-visible-swarm.md` § Settle on finish.
6. Answer a launched thread's questions and approval requests under `sats-pm-visible-swarm.md` § T3 Code children, Questions. Follow a launched T3 thread through its master only; per-PR threads and delegates reach the bot through it (`sats-pm-visible-swarm.md` § Workspace, Main thread only). Send a ready Victor decision to Sats at once. Work waits on Victor's GO, not on whether he has seen an update. Hand off per canon `task-notices-and-reporting.md` § Channels and shape.
7. One seat, one ping.
8. A routine prompt states the job, schedule and skill path. Behavior stays in the skill.
