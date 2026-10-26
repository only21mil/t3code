---
aliases: ['auto-push', 'Agent-Shared + 01-daily → victor-vault AUTO-PUSH (standing)', 'Canon Git backup export to victor-vault (standing)']
title: Canon read and write contract (victor-vault)
created: 2026-09-19
updated: 2026-10-25
type: system
status: active
tags: [agent-shared, victor-vault, standing-policy, sot, fleet, daily-notes]
confidence: high
owner: sats
sources:
  - 'Victor 2026-10-20: GitHub is main for the shared canon; record [[wiki/systems/github-canon-main-cutover-2026-10-20]]'
  - 'Victor 2026-10-24, canon-gh-main-20261024: GitHub main is the canon read source; local copies are caches'
  - 'Victor 2026-10-24, GitHub-main reads on all hosts and harnesses: Agent-Shared/knowledge/log.md, 2026-10-24 entry; importer fields read back at 2026-10-24T11:32:28Z'
  - 'Victor 2026-10-24 6:43 PM CT: review scope (owner review-and-babysit § 1); the canon writer confirms the landed SHA; replaces the 10:51 CT canon bypass and the C05 review requirement, preserves fast-forward only, no force-push and no history rewrite'
  - 'Victor 2026-10-25 9:14 PM CT, deploy-gate-github-main-20261025: deploy and install gates check GitHub main, not the F-D projection; importer and replica health report separately and never block installs'
  - Victor 2026-09-24, objective canon_sync (Sats agents edit canon in their own scope without per-change permission)
  - 'Dated rules before 2026-10-20 (AUTO-PUSH 2026-09-19, exporter standing rule 2026-09-24, replica write paths): `git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/agent-shared-victor-vault-auto-push.md`'
---

# Canon read and write contract (victor-vault)

This page owns canon read and write authority for every Sats agent, host and
harness. Other pages link § Current contract instead of restating it.

## Current contract (2026-10-20)

Victor's ruling of 2026-10-20: **GitHub is main for the shared canon.** For
`only21mil/victor-vault`:

1. **Write path.** Canon changes are made only in Git authoring clones (a
   dedicated clone per writer under `/home/victor/work/canon-authors/<writer>/`
   on F-D, or the writer's own clone) and pushed to GitHub `main`. Canon
   review scope: review-and-babysit § 1. The writer commits and pushes fast-forward
   to main, then confirms the landed SHA. No force-push or history rewrite.
   This replaces C05's reviewed-commit requirement. Every gate in § Boundaries
   keeps its owner. Victor's instruction is standing OK for canon pushes;
   [[upstream-pr-go-gate-2026-10-11]] item 1 still governs upstream and
   external writes. This item is the one rule for who commits and pushes
   canon; other pages point here. The exporter clone
   (`/home/victor/work/canon_sync/victor-vault`) and the importer clone
   (`/home/victor/work/canon_import/victor-vault`) must never be hand-written
   or committed in.
2. **No live-tree writes.** The F-D live tree
   (`/home/victor/Obsidian/Victor`) is a materialization owned by
   `canon-git-import-victor`; direct edits there are non-authoritative and
   trip its local-divergence halt. Syncthing replicas are `receiveonly` and
   are not write surfaces either.
3. **The exporter is retired for victor.** `canon-git-export@victor` is
   stopped, disabled and retirement-marked. Never re-enable it: its overlay
   would delete post-cutover GitHub changes. The family scopes follow the
   same contract: Rachel since 2026-10-22 (`only21mil/rachel-vault`) and
   Mason since his 2026-10-23 cutover (`only21mil/mason-vault`, Victor decision 1;
   order and precondition in [[wiki/systems/canon-sync-fabric-2026-09-24]] §
   Cutover amendment). Their exporters are stopped and disabled, and
   `canon-git-import-family@<scope>.timer` materializes main into the F-D
   live tree every 5 minutes. Family agents write through authoring clones
   pushed to `main`; the F-D trees and their Syncthing replicas are
   materializations
   ([[wiki/systems/canon-sync-fabric-2026-09-24#Cutover amendment (2026-10-20) — read first]]).
4. **Daily notes.** The repo's `01-daily/` is the daily-notes source of
   truth. `daily-notes-sot` authors in the filing checkout and pushes to
   `main`; F-D sees the note via the importer.
5. **Status surface.** For victor, health is the importer status
   `/home/victor/.local/state/canon-git-import/victor-import.status.json`
   (outcome `ok`/`no-change`). For a family scope it is
   `/home/sats/.local/state/canon-git-import-<scope>/<scope>-import.status.json`
   (outcome `ok`). The exporter status files stopped updating when each
   exporter retired and report nothing current. Importer and replica health
   go to their owner as a separate report. They never gate a read, startup
   load, render or install (item 6).
6. **Read path.** Every Victor/Sats canon read, on every host and harness,
   comes from GitHub `main` of `only21mil/victor-vault`. Read a file with
   `gh api -H "Accept: application/vnd.github.raw" "repos/only21mil/victor-vault/contents/<path>?ref=main"`.
   In an authoring clone or worktree, use
   `git fetch origin && git show origin/main:<path>`.
   List a directory with
   `gh api "repos/only21mil/victor-vault/contents/<directory>?ref=main" --jq '.[].path'`
   or, after fetching, `git ls-tree --name-only origin/main:<directory>`.
   Search after fetching with `git grep <pattern> origin/main -- <path>`.
   `[[wiki/systems/x]]` maps to
   `Agent-Shared/knowledge/wiki/systems/x.md` in this repo.

   State a currency proof before using a local tree, Syncthing replica or
   host skill copy, the F-D live tree included. Source proof means the exact
   bytes used match the same file on fresh main, by byte compare, SHA-256 or
   git blob id. A render or install requires it, and a matching file passes
   while the importer is stale, stopped or unreachable. A mismatch blocks:
   read or install from main instead. For a plain read, the shared core's
   local tree check (a `.canon-sha` stamp equal to main) also passes.
   Importer status, the stamp and replica health are item 5 health signals.
   A stale one never blocks a main-verified file, and an equal one never
   replaces source proof for a render or install. Approval and safety gates
   on an install keep their owners. A local copy without either proof is
   stale; read main instead.
   Harnesses can load only local startup files, including Claude Code `@`
   imports. Those files are bootstrap caches and must say so; loading one
   proves no other local canon file current. Each family scope follows the
   same read rule through its own vault repo.

Record: [[wiki/systems/github-canon-main-cutover-2026-10-20]]. Transport and
importer mechanics: [[wiki/systems/canon-sync-fabric-2026-09-24]].

## Boundaries

These carried over unchanged from the 2026-09-24 standing rule.

1. Sats agents create, edit, move and delete canon and wiki pages in their own
   scope without asking per change, through § Current contract item 1, Write
   path. `knowledge/SCHEMA.md` governs structure. Deleting whole trees or
   archives needs Victor.
2. This contract covers canon and wiki text only. These keep their approval
   gates:
   - pushing code or any non-canon repository
   - publishing, external sends, releases and deploys
   - signing or tagging `sats-release-*` instruction releases in
     `only21mil/agent-shared-canon`
   - creating, changing or rotating credentials, deploy keys, tokens or
     `authorized_keys`
   - force-pushing, rewriting history, deleting branches or tags
   - changing sync units, Syncthing folders or device lists
   - every other gate in the shared safety rules
3. Scope isolation. An agent writes only its own scope's canon, and family
   private memory never enters Sats canon. Softfork EQ notes, Rachel therapy
   notes and other Rachel or family content are never written here. Victor and
   Rachel share everything (Victor, 2026-09-24), yet cross-scope copying still
   needs explicit Victor or Rachel approval plus review. The mini exception is
   recorded in [[wiki/systems/sats-vs-family-agent-scope]].
4. Secrets, tokens, keys, passwords and credential values never enter canon.
   They belong in the secrets store, read through `read-canon.sh`. If gitleaks
   blocks a scope, the agent that sees it removes the value from canon and
   reports the blocked scope. Only Victor clears the block, and a real secret
   gets rotated.
5. The swarm board (`Agent-Shared/swarm-board/`) is transient worker scratch
   and never ships to victor-vault.

## Canon auto-sync standing rule (Victor, 2026-09-24)

Its push mechanics, replica write destinations and exporter status watch are
history, kept in `git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/agent-shared-victor-vault-auto-push.md`.
Its boundaries that still stand are § Boundaries. Who commits, pushes and
reads canon is § Current contract.
