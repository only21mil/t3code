---
aliases: ['buzz-hub', 'Buzz hub', 'Buzz work rules']
title: Buzz
created: 2026-10-05
updated: 2026-10-05
type: system
status: draft
tags: [agent-system, workflow, coding]
sources:
  - knowledge/wiki/systems/buzz-platform-2026-08-25.md (§ Current state, 2026-10-05; § Upstream desktop v0.5.26 on F-D and Yoga)
  - knowledge/wiki/systems/buzz-agent-rollout-2026-10-04.md
  - knowledge/wiki/systems/buzz-agent-taggability-and-ownership.md
  - knowledge/wiki/systems/buzz-private-community-pilot.md
  - decisions-log.md (2026-09-21 mirrors decommissioned; 2026-09-29 fork discontinued; 1473 provider policy; 1942 writeback; 1970 Rachel access; 4048 enrollment)
  - mistakes.md (37, 98, 101, 199, 217, 236, 289)
  - knowledge/wiki/systems/instruction-surface-registry.md (1545, 1577, 1579, 1585)
  - RESEARCH/2026-10-04-buzz-sentiment-swarm.md
  - RESEARCH/BUZZ_WORKFLOWS_AND_PULSE.md
  - /home/victor/projects/buzz/AGENTS.md at f0eb5575
confidence: medium
owner: sats
---

# Buzz

Read this page whole before Buzz work: the relay on framework-desktop (F-D), Buzz desktop and mobile clients, Buzz-managed agents, or code in `only21mil/buzz`. It holds only what differs for Buzz. Routing, review, swarms, approvals, secrets and memory follow the adapters and the pages they name, unchanged.

Live facts (hosts, ports, image digest, client versions, agent wiring, open items) are on [[wiki/systems/buzz-current-state]]. The dated record through 2026-10-04 is [[wiki/systems/buzz-platform-2026-08-25]]. Treat any path, SHA or command from either page as a lead: read it back before you act on it.

## 1. Preflight

Before Buzz work on F-D or Yoga, confirm no other writer is active. On 2026-10-04 an agent on Tailscale node `muse` (100.99.104.45) installed Buzz as root and put the relay owner key on a command line.

```sh
pgrep -af 'be-child ssh.*100.99.104.45'                                  # open muse SSH sessions
sudo journalctl -u tailscaled --since '15 min ago' | grep 100.99.104.45   # recent ones
pgrep -af -i buzz                                                        # running Buzz processes
```

If `muse` is active, stop and ask Victor.

## 2. Authority

- Buzz is a collaboration surface. Source, CI and review live on GitHub; memory lives in Agent-Shared canon; secrets live in the canon store (`BUZZ_*` names: [[wiki/systems/sats-secrets-and-api-locations]]).
- GitHub is the only repository authority (Victor, 2026-09-21). The GitHub-to-Buzz git and forge mirrors and the channel sweep are retired and stay uninstalled. Victor has not yet set a replacement mirror scope.
- `only21mil/buzz` equals upstream `block/buzz` main `f0eb5575` since 2026-10-05: no fork commits, Actions off, rulesets deleted, no sync automation. Buzz-first delivery, relay-first push order, `land_on_buzz.sh`, `docs/delivery-lifecycle.md`, native CI and `deploy-local.sh` belong to a deployment that no longer exists.
- Rachel is a relay admin, not the owner; private channels and DMs stay membership-gated. Archimedes agents belong to Rachel's scope and their own orchestrator: [[wiki/systems/rachel-archimedes-lane-map]].
- Permanent parent seats and Parent Mode: [[wiki/concepts/dispatch-vehicle-doctrine]].

## 3. Gates

On top of the shared approval gates, these need Victor (Rachel too where named):

- Every relay production change: image or `BUZZ_IMAGE` pin, media and CORS settings, membership and member keys, `RELAY_OWNER_PUBKEY`, compose edits, restarts. Back up the relay `.env` before any edit. `POSTGRES_PASSWORD` stays as first set.
- Enrolment: each identity is an explicit pubkey addition. Non-Sats Buzz agents stay sandboxed.
- Mobile push stays off (`BUZZ_PUSH_ENABLED=false`) until Victor accepts metadata passing through Block's push gateway.
- Agent ownership transfer: the incoming owner signs the auth tag with their own key. An agent seat mints it for no one.
- Sats Codex-R's owner-only `respond_to` and `allowed_respond_to`: loosening needs Victor or Rachel.
- Legacy Sats Buzz seats are stopped since 2026-10-03: the installed prompts (`~/.config/buzz/agents`) and the `buzz-sats-agent@` unit are absent and no seat runs, while the rehomed launcher files remain under `~/.local/libexec/buzz/fleet/` (instruction-surface-registry.md:1545). Prompts, pins, units and launchers stay untouched until an owner re-establishes the seats.
- Moving a coordinating seat to F-D: one supervised low-impact canary first, with a frozen manifest, real signed-task evidence and Yoga-off, logout and reboot checks. Agent keys stay on their host; a snapshot import is not a migration.
- Releases: no standing Buzz release approval is in force. The 2026-09-05 Mac approval was bound to the discontinued fork channel.

## 4. Code in only21mil/buzz

- Clone: `/home/victor/projects/buzz` (`origin` only21mil, `upstream` block). Worktrees follow `adapters/sats-shared-common.md` § Scope and writes.
- The repo's `AGENTS.md` (`CLAUDE.md` links to it) governs code work; read it and the VISION and TESTING docs it names. Its § Before opening a PR and § Quality Gates set the PR gates (local checks, with a mobile-only command set for Flutter/Dart changes; DCO sign-off; Hermit activation; draft until a human has tested). Topic contracts live in `docs/` (deployment identity, push gateway, admin dashboard auth and the public moderation `reason` in `docs/admin/README.md`, mention editor, agent availability and ownership, Linux rendering) and the protocol specs in `docs/nips/`.
- Actions are off on `only21mil/buzz`, so run the § Quality Gates checks locally.
- Open an upstream PR (`block/buzz`, `pingdotgg/t3code`) only for a reusable change offered for upstream review and merge. A CI-only or do-not-merge PR upstream is refused (Victor, 2026-09-04).

## 5. Relay and clients

- Front door: `wss://framework-desktop.tail69757d.ts.net:38444`. The community is bound to that host and port, so other URLs return 404 and non-member keys 403.
- Relay compose files: `/home/victor/work/buzz-relay/deploy/` (not a git checkout). Source: `/home/victor/projects/buzz`.
- Desktop is the upstream AppImage. Stop it by closing the window or `kill -TERM <app PID>` before stopping any systemd unit around it; a cgroup stop SIGBUS-crashes the FUSE runtime. Each start rewrites `~/.local/bin/buzz` to the live mount, so that link dangles after exit.
- Kill by explicit PID. A `pkill -f` during a Buzz deploy once matched and killed its own shell.
- Blank window on Linux: check GStreamer first (Yoga needed `gst-plugins-good`), then the repo's `docs/linux-rendering-troubleshooting.md`.
- Clients do not self-update. When you touch a client, compare it with the latest `desktop-v*` release.
- macOS invite failing on CORS: use the bypass on the current-state page. It keeps the WebKit store and keychain identity intact.
- Each machine's Nostr identity key is unrecoverable once lost. Back it up under the canon secret-store rules.
- A new client or agent machine is accepted when a cross-machine @mention of a managed agent works (block/buzz#3277).

## 6. Buzz agents

- Defaults for Buzz ACP agent seats (Victor's 2026-10-04 order as reported by a worker; no primary record): Codex on GPT-6.1 Sol `xhigh`, Claude on Opus 5.5 `xhigh`, every call through the sats-hub proxy (`127.0.0.1:8330` on F-D, `framework-desktop:7443` from Yoga), never a personal login. Leave a seat's `effort_level` unset or `xhigh`. Everything else follows [[wiki/systems/sats-model-tier-provider-policy]].
- Non-GPT Buzz agents on OpenRouter send `provider.data_collection=deny`; ZDR is optional, and each seat discloses the retention it knows.
- Tools run on the host of the ACP or CLI process. Reaching the F-D relay or hub says nothing about where an agent executes.
- Each agent has its own key, minted on and kept to its host. A human key is never an agent key.
- Core memory (`buzz://agent/core`): each seat writes its own with `buzz mem patch core --base-hash`, then reads it back. Canon records that it changed, never its body.
- Config in force is what the seat's launcher or agent record sets, not the source default. Prove it live by comparing its mtime with the process start time.

## 7. Mentions, ownership and channels

- One person can tag an agent and another cannot: check the registered owner first, then walk the gates in [[wiki/systems/buzz-agent-taggability-and-ownership]].
- The `respond_to` allowlist delivers channel mentions only. Ownership and DM access follow the registered owner and auth tag.
- Private-channel adds need a signer who owns or administers that channel. Membership changes go through the relay; the database's `channel_members` rows are the relay's to write.
- `buzz channels set-add-policy` replaces the whole kind-10100 record. Run it before membership steps, never as the last one.
- Keep each agent's DB role as it is; the `bot` role costs repo push authority.
- When the picker hides an agent, paste `nostr:npub…` into the message body for a real signed mention.
- Repo traffic goes in that repo's channel; general carries fleet-level matters only.
- Qwen (MBP, local model) works from the Qwen Work channel. Reach her by tag in a quiet channel or by DM; her GPT parent relays repo-facing items.

## 8. CLI, records and workflows

- `buzz pr list` and `buzz issues list` with a small `--limit` can return an empty array with exit 0. Page fully, or run `buzz messages search` across the relay, before asserting a negative.
- `--content -` needs a stdin producer in the same shell command. Read back the event ID of every important send.
- An auth-tag `created_at` must fit an unsigned 32-bit integer; test defaults against the relay's validator before signing. Pick auth-tag candidates by exit code. Key handling follows [[wiki/systems/sats-secrets-and-api-locations]].
- NIP-34 records, where a repo still uses them: only status events signed by the repository owner close an issue or PR. Before creating a record, raw-read the repo for a stable external ID. Before opening a PR, prove the destination repo object and its owner; an issue ledger is not the code repo. After a duplicate race, keep the earlier owner-signed root and close the later one, deleting no events.
- A claim about which ref is authoritative needs authenticated relay or GitHub evidence. A local `origin` proves nothing.
- Workflows: any channel reader can fetch a workflow definition, so treat its headers and body as public. `enabled:false` did not stop manual or webhook runs on the fork; recheck on upstream before relying on it.

## 9. Writing back to canon

Writeback, including what stays out of canon, follows [[wiki/systems/sats-wiki-first-memory-policy]]. A Buzz-originated outcome cites the channel UUID and event ID as provenance. A canvas does not replace canon. Auth tags count as credentials.

## 10. Other pages

- [[wiki/systems/buzz-current-state]]: hosts, relay image, clients, agents, open items and Victor's pending decisions.
- [[wiki/systems/buzz-platform-2026-08-25]]: dated history, 2026-08-25 to 2026-10-04.
- [[wiki/systems/buzz-agent-taggability-and-ownership]]: the mention and ownership gates, ownership transfer.
- [[wiki/systems/buzz-agent-rollout-2026-10-04]]: how the current Codex and Claude agents were wired, effort chain, open checks.
- [[wiki/systems/qwen-local-agent]], [[wiki/systems/rachel-archimedes-lane-map]], [[wiki/people/rachel-vogel]] (TestFlight test address).
- [[wiki/systems/automations-registry]] and [[wiki/systems/instruction-surface-registry]]: what Buzz automation and instruction surfaces exist.
- `RESEARCH/2026-10-04-buzz-sentiment-swarm.md`: outside view of upstream v0.5.26 and the watch list.
- `~/.agents/skills/buzz-handoff/SKILL.md`: handoff format; review goes through review-and-babysit.
