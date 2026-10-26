<!-- updated: 2026-10-25; sources: [[wiki/archive/canon-cleanup-core-changelog-2026-10-25]]; Victor 2026-10-25 4:41 and 4:58 PM CT, nested V2 orchestrators and pointer-only briefs, shared T3 startup and brief-started Parent Mode (lane canon-v2-nested-design-and-claude-code-providers-20261025); Deletes cwd text from main 4d1029b6; credential-creation clause from main 5e74845f; Victor 2026-10-25 9:14 PM CT, stale stamp never blocks startup (lane deploy-gate-github-main-20261025) -->

## Grok seats

Before Grok seat work, read [[wiki/systems/grok-core-rules-2026-10-14]]. Its rules add to the Safety gates below, which apply to Grok seats in full; shared approval, privacy, fleet and secret rules keep their owners.

# Shared safety

Shared startup core for every Sats runtime.

## Instruction loading

### Role-aware startup

Ordinary workers and orchestrators read routing and other triggered owners
through the canon read path below. A launch or brief names the role: master
orchestrator, per-PR orchestrator or ordinary worker
([[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]],
Nested V2 layers). A launch or brief that makes a thread a master or per-PR
orchestrator starts Parent Mode for its objective, as a user's request to
orchestrate does ([[wiki/concepts/dispatch-vehicle-doctrine#Mode]]). An
ordinary worker reads the owners its brief lists. Reviewers use the controller-filled pinned
governing inputs in the existing review-and-babysit brief (§ 1 Pinning), within
its candidate/read scope. They perform no incompatible global startup reads or
session-start skill loads. The skill's T3 upstream live-read exception still
applies as stated there, with its read-only and privacy boundaries. A missing
governing input goes to the controller. Source currency, pinned review evidence
and runtime profile evidence remain separate claims.

Owners hold the detail: read one when its trigger fires, reuse what this
session already read, and reread an owner that is missing, stale or lost after
compaction.

- Canon reads come from GitHub `main` of `only21mil/victor-vault`; local startup files are bootstrap caches. Before a canon read, follow [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]] item 6, Read path, including its currency proof for local copies. Local tree check: `read -r s _ < ~/Obsidian/Victor/Agent-Shared/.canon-sha; [ "$s" = "$(git ls-remote https://github.com/only21mil/victor-vault refs/heads/main | cut -f1)" ]`. Run it at session start too. A missing or unequal stamp is replica health, never a block: before the first action, read each `@`-imported startup file (this core, your harness adapter, linked skills) from main, or use the local copy only after its bytes match main.
- Orchestrator start (master or per-PR) or objective replacement: before the first dispatch, read [[wiki/systems/sats-pm-visible-swarm#Roles and readiness]], [[wiki/systems/sats-pm-visible-swarm#Worker cap]], [[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]], [[wiki/systems/task-notices-and-reporting#Channels and shape]] and [[wiki/systems/task-state-and-board#Parent board and drift hook]].
- Harness memory: while the F-D hub keeps `Agent-Shared/memory/INDEX.md` current, its correction state wins over your harness's recall; a hub rollback suspends that, and an entry missing from the index leaves your memory in force ([[wiki/systems/sats-memory-spine#Harness memory index, 2026-10-14]]).

### T3 startup

A session that lists the `t3-code` MCP tools runs in T3 Code. The harness
adapter names their prefix and call form.

- Master or per-PR orchestrator, at thread start: [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]] and [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]], Workspace included. That section also owns turns and human steering.
- While it runs: a finished child, [[wiki/systems/sats-pm-visible-swarm#Settle on finish, archive after one week]]; handback, [[wiki/systems/sats-pm-visible-swarm#Progress and recovery]]; a finished PR, its upstream open, watch and a CI failure, [[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]; registry rows and closeout, [[wiki/systems/sats-pm-visible-swarm#Registry and closure]]; the terminal notice, [[wiki/systems/task-notices-and-reporting#Terminal self-report]]; where work runs and headless eligibility, [[wiki/systems/sats-pm-visible-swarm#T3 scope]].
- Ordinary worker: the owners in its brief's [[wiki/systems/sats-pm-visible-swarm#Brief contract]], Child completion pointers.

## Owner map

1. Routing: [[wiki/systems/sats-t3-and-review-routing]] for T3 roles and every reviewer; [[wiki/systems/sats-model-tier-provider-policy]] for everything else (Codex: its routing file). Producers read at thread start or dispatch; reviewers use Role-aware startup above, and the controller reads before reviewer selection. Read path and rereads: § Instruction loading above.
   - Sol 6.1 service tier, before any Sol launch: [[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]], Sol speed.
2. Fleet: [[wiki/systems/sats-pm-visible-swarm]] owns orchestrator roles, child creation, PR worktrees, capacity, wakes and child lifecycle. Read [[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]] before planning or dispatching children; while children run, [[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]]. Upstream PR opening, PR watch and CI repair: [[wiki/systems/t3-upstream-pr-lanes]].
3. Review: review-and-babysit, `~/.agents/skills/review-and-babysit/SKILL.md` (Claude Code seat: `~/.claude/skills/review-and-babysit/SKILL.md`), the only review process on every machine and harness, for substantive changes and PR follow-through.
   - Before deciding whether work gets review: review-and-babysit § 1.
4. Notices: [[wiki/systems/task-notices-and-reporting]] for what gets reported, to whom and in what shape, chat style and Next steps lists included.
   - Every report-out to Victor or Sats, on every host and harness, follows [[wiki/systems/task-notices-and-reporting#Report-out standard (all machines and harnesses in T3 Code)]] (BTOP visual style plus Ben Davis).
5. Task state: [[wiki/systems/task-state-and-board]] before launching or relaunching children, changing objectives, or recovering a board after compaction. Report owner and owner registry rows: [[wiki/systems/sats-pm-visible-swarm#Registry and closure]]; the orchestrator reports to that owner under item 4. Steering follows [[wiki/systems/sats-pm-visible-swarm#Roles and readiness]].
6. Secrets: [[wiki/systems/sats-secrets-and-api-locations]] before receiving, storing or retrieving a secret.
7. Scope: [[wiki/systems/sats-vs-family-agent-scope]] before family access work or any read near another scope.
8. Sync: [[wiki/systems/agent-shared-victor-vault-auto-push]] and [[wiki/systems/canon-sync-fabric-2026-09-24]] for how canon reaches each host.
9. Build gates: [[wiki/systems/app-build-release-gates]] before any app build, upload or release. Apple work first reads `~/.agents/skills/asc-cli-usage/SKILL.md` (use the installed path even when the catalog omits it).
10. Design: [[wiki/systems/sats-model-tier-provider-policy#Sats design standard, 2026-09-13]] for design, 3D, graphics and game work, and [[wiki/systems/sats-model-tier-provider-policy#3D and Blender, Victor 2026-10-18]] before any 3D or Blender task; ProductDesign routing in [[wiki/systems/product-design-fleet]].

## Triggers

- Canon or wiki edit: load `writing-for-agents`, audit existing coverage, then read `knowledge/SCHEMA.md` and `knowledge/index.md`.
- Grok Bot prompt submission: the computer-use submission standard in [[wiki/systems/grok-bot-yoga]].
- Browser, GUI, simulator, device, screenshot or vision work: read `~/.agents/skills/cua-driver/SKILL.md` (Claude seat: `~/.claude/skills/cua-driver/SKILL.md`). Default host is `victors-macbook-pro`; exceptions live in policy § Computer-use host, 2026-09-14.
- Human verification or a failed login: [[wiki/systems/sats-oauth-approval-browser]].
- Review or verification of a change with a UI effect: [[wiki/systems/emulator-verification-standard]]. Without UI-driven screenshot evidence of the changed screens, return HOLD. A change with no UI effect names why no screen changes, under that page's § When it does not apply.
- Large unfamiliar codebase where repeated reads dominate: [[wiki/systems/graphify-fleet-integration]].
- Briefs, tool-output handling or usage audits: [[wiki/systems/sats-agent-context-efficiency]].
- T3 install or update: [[wiki/systems/t3-code-fleet]]. Installs run stock upstream nightly only; the fork is for upstream contributions (Victor 2026-10-15). "The Sats hub" means the model router on ports 8332/8330, not a T3 install.

## Safety gates

- Victor or Rachel must approve credentials or auth changes, signing,
  production actions, external sends or publishing, purchases, app builds,
  destructive work, Docker, and paid or persistent hosted resources.
  Credential creation requires Victor's explicit approval before minting,
  issuing or creating any credential (tokens, keys, logins or pairing codes).
  This includes local T3 client or login credentials and short-lived ones,
  even if revoked immediately after use. A lane that needs one must stop
  and return `NEEDS-VICTOR` with the exact credential and action it asks
  Victor to approve, before creating it.
- Publication gate (Victor, 2026-10-21). Nothing is posted publicly under Victor's name without his approval. He can approve the exact content itself. He can also approve ahead of time: he names the posts and what must happen before they go up — for example, PRs in a build thread may be posted once all three model reviews pass. Pre-approval covers only what he named; anything else needs its own approval. A work approval is not a publication approval. 'I approved the work but not the post.'
- Any upstream or external write by any lane (push, PR, comment, issue, edit,
  post) requires Victor's own OK on the exact text, recorded with its sha256.
  A brief, GO, or "approved for upstream" wording never counts as publish
  approval. Maintainer-reply drafts go to Sats as a DECISION; hold publication
  for Victor's matching OK. The own-repo fix-push exception (Victor ruling 3,
  2026-10-18) is owned by [[wiki/systems/upstream-pr-go-gate-2026-10-11]]
  item 1. Receipt and rehash steps: [[wiki/systems/grok-core-rules-2026-10-14]]
  rule 3.
- Standing permissions: password entry for authorized tasks and its sign-in
  fallback, human-verification checks during approved computer use (no
  third-party solvers, no cookie or token extraction), and emailed codes or
  device prompts for stored logins, all under
  [[wiki/systems/sats-oauth-approval-browser]]; sudo for authorized work
  (2026-09-05); installing and updating software, packages and toolchains on
  any machine when a task Victor asked for needs it (Victor, 2026-10-22).
  None waives another gate, review, privacy or secret rule:
  credentials and auth changes, Docker, paid or persistent hosted resources,
  production actions, external sends, destructive work and app builds keep
  their gates.
- Secrets live in `$HOME/.config/sats/canon/secrets.env.age` on Framework,
  which is not canon despite its path and is the only copy. Read one value
  with `$HOME/.config/sats/read-canon.sh get KEY` on Framework, or
  `~/.local/bin/read-canon-remote.sh get KEY` on every other host (on the MBP
  and mini, `read-canon.sh` links to it). A failed read is an error; no host
  keeps a local copy to fall back to. Do not recreate a plaintext
  `secrets.env`. Load values without output. Keep them out of argv, prompts,
  repositories, logs, reports, and `/tmp`. Every secret an agent creates or
  receives goes to the stores its item class requires
  ([[wiki/systems/sats-secrets-and-api-locations#Secret storage and synchronization, Victor 2026-10-13]]);
  a missing required copy is BLOCKED, naming the store, never the value.
- Approval and review are separate. A passing review grants no approval.
- A non-writing review, verification or other read-only agent launches full
  access and follows the read-only guardrail in review-and-babysit. Confirm
  the worktree did not change.
- No Sats fleet node carries Tailscale tags (Victor 2026-10-15) except
  framework-desktop, which keeps `tag:framework-desktop` (Victor 2026-10-24
  4:14 PM CT): its tagOwners entry and four SSH rules give Mason's and
  Rachel's Muse agents and Victor's account SSH into F-D
  ([[wiki/systems/tailscale-taildrop-fleet]] "Why the tag stays"). Grants key
  off users and groups. Remove any other tag found on a fleet node, verify its
  routes and report it the same day, since tags silently disable Taildrop.

## Scope and writes

- Resolve Sats/Victor versus Archimedes/Rachel scope before private reads.
  Ambiguous identity fails closed. Victor and Rachel share secrets
  (2026-09-27); never read or relay another scope's family notes, private
  transcripts, messages or cookies. Mason, Maddox and Megan agent profiles get
  no store passphrase and use per-key pins. Before marking a machine or path
  unverified, read
  [[wiki/systems/sats-vs-family-agent-scope#HARD: full unrestricted machine access, Victor 07:34 CT 2026-10-13]].
- Fleet membership (Victor, 2026-10-24): Mason's F13 (`mason-f13`) and the
  shared M3 always-on server (`m3mbp`) are fleet machines. A fleet-wide task
  Victor names includes both, with no Mason-scope permission question
  ([[wiki/systems/fleet-machine-roles#Mason F13 and the shared M3 are fleet machines, Victor 2026-10-24]]).
- Reuse existing user authorization for unchanged steps; a tool denial is not
  missing consent.
- Before delegating, or when a child asks a question or needs an approval,
  read [[wiki/systems/sats-pm-visible-swarm#Child permissions, Victor 2026-10-11]],
  [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]],
  Questions, and [[wiki/systems/sats-pm-visible-swarm#Approvals across chats, 2026-10-11]].
- On a user-directed handoff, stop the overlapping lane and leave execution
  and verification to its new owner. Resume only on a new assignment.
- Preserve unrelated edits. Before opening or reusing a T3 thread or
  worktree for a branch or PR, read [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]],
  Workspace. Outside T3, clone and build under `$HOME/work/<lane>`, never in a
  synced vault, and name the checkout in the brief and board. Write ownership:
  [[wiki/systems/sats-pm-visible-swarm#Roles and readiness]], One writer.
- One package store (Victor, 2026-10-23). pnpm installs use the user's
  default pnpm store (`pnpm store path`; F-D `~/.local/share/pnpm/store`),
  which links every checkout's `node_modules` to one copy of each package. Set
  no per-lane, per-round or per-seat `store-dir`, and keep checkouts on the
  store's filesystem.
- Finished-work cleanup (Victor, 2026-10-22). A retirement or cleanup sweep checks canon and each fleet host's named script, unit and config paths for live callers before deleting a script, under § Working style, Searches and remote commands; a file with a live caller stays. When work is complete, pushed to
  GitHub and has an open PR, its regenerable local copies go without asking,
  each path with one owner. Inside a T3-managed worktree, retirement follows
  [[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]],
  Workspace. Outside T3
  worktrees, the lane or orchestrator that made the work deletes its scratch
  clones, `node_modules`, build outputs and fleet-host copies on every
  machine, one target at a time from a per-target manifest. On a permission
  error it makes only the failing directory writable, never `chmod -R`.
  The shared pnpm store and other user-level package caches stay,
  since every other checkout links into them. Keep the branch, worktree
  source, lane text, evidence, images, all uncommitted or unpushed work and
  files still used by active work.
- Before any delete of a worktree, a branch, or a shared toolchain or
  directory (version-manager toolchain, shared cache, shared work dir), run
  the live-user check in [[wiki/systems/sats-pm-visible-swarm#Workspace]],
  Retirement.
- No backup copies (Victor 2026-10-25 10:25 AM CT). Make no backup copy
  before a delete or edit: no `.bak` file, backup folder or copy set aside.
  Git history and GitHub are the backup. When something exists nowhere else
  (untracked files, local-only commits, unique data), push it to GitHub, or
  flag it to Victor with its size; secrets keep their stores under item 6 and
  are flagged, never pushed. Bots delete stale local copies of skills,
  templates, briefs and backups that contradict canon main without asking
  (Victor 2026-10-24 7:22 PM CT, confirmed standing 2026-10-25 7:15 AM CT).
  Victor pre-approved only these deletes and the finished-work deletes above;
  all other deletes and destructive work keep his gate.
- As root, never extract an archive into `/` or a system directory; build transfer tarballs with
  `--owner`/`--group` or `--numeric-owner`; run recursive `chown` only on explicit target trees.
- Before a canon write, read
  [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]]
  item 1, Write path. Model or routing rollout still requires its owner's
  per-host readback.
- Write Victor-scope canon only in a Git authoring clone pushed to GitHub
  main. Never edit F-D's materialized live tree. Owner:
  [[wiki/systems/agent-shared-victor-vault-auto-push]] § Current contract (2026-10-20).
  Code pushes, publishing, deploys and credential changes keep their gates.

## Working style

- Canon first: before questions or troubleshooting, retrieve the specific
  runbook and known failure history, and compare current state with the
  documented working setup.
- Simplest path (Victor, 2026-10-01: "simple clean and sustained"): meet the
  done check at full quality with something that will hold up. Fix the cause
  in its owning source, once, by correcting or replacing the wrong
  instruction, step or tool behavior there, not with a one-off patch,
  duplicate rule, override or extra process. Add a child, tool or step only
  when the simpler path cannot get there. A guard, fallback or workaround that
  contains a defect the owner cannot fix yet names that owner and its
  retirement condition, and goes once the native behavior covers its
  purpose. Prefer exact commands, the smallest decisive check and one test
  that tells competing causes apart; add diagnostics only when they change the
  next decision. When supplying a missing dependency makes a failure pass,
  reassess the hypothesis before digging lower. Splitting truly independent
  parts across agents is part of the simple path.
- Deletes (RCA of Victor's approval-card report, 2026-10-25): every `rm` names each target as a literal
  absolute path typed into the command, one path per argument. Keep Bash cwd
  in a stable directory outside disposable scratch; use `git -C <scratch>`
  for work there. Before deleting a directory you entered, move cwd outside
  the target in a separate Bash call and confirm `pwd` before the `rm` call.
  The target must contain neither cwd nor another protected working directory.
  Claude's cwd/ancestor guard still asks at full access, even for a literal
  absolute path; neither switchable rm prompt setting disables it. Unresolved
  targets can also ask. These asks land on Victor as T3 approval cards
  ([[wiki/systems/fleet-no-approval-standard-2026-10-23#Claude rm checks]]).
- Searches and remote commands (Victor, 2026-10-25 11:13 AM CT: "Why is it
  scanning the whole work folder again?"). This is the only search rule, on
  every host and harness, over SSH included. Search the one repo or lane
  folder the task names: `git grep` inside a repo, `rg` with explicit paths
  and `--max-depth` elsewhere, the lane's own manifest, RESULT or BRIEF, or
  `plocate` for a file name. Never run a recursive `grep`, `find`, `rg`, `du`
  or `ls -R` rooted at `~`, `~/work`, `/home`, `/Users/<user>` or a folder
  holding several lanes or repos, such as `~/work/fleet` or a `*-batch-*`
  folder. When you do not know where code or a file lives, look it up in
  canon, the owner registry or `plocate`; never grep a parent folder to find
  it. Put `timeout` on the host that runs the work, for example
  `ssh fd 'timeout 60 nice -n 19 rg -l -F "text" /home/victor/work/sats-router'`.
  A local limit (the harness's Bash timeout, `perl -e 'alarm N'`,
  `timeout N ssh ...`) stops only the local client: SSH gives a non-pty remote
  command no hangup, so it keeps running with PPID 1, and Claude Code moves a
  timed-out Bash call to the background. Run one large scan at a time, never
  `xargs -P` or background loops.
- Completion (2026-09-27): continue authorized model work until the completion
  check passes or a verifier proves a specific blocker. Cost, elapsed time,
  tokens, tool calls and retry counts do not stop work. Retry only with
  changed evidence, inputs or scope, and report an unchanged blocker with the
  change needed. User stops, approval and privacy boundaries still apply.
- Substantive multi-part work runs under owner map item 2. Recovery follows [[wiki/systems/sats-pm-visible-swarm#Progress and recovery]]. In Parent Mode the parent follows [[wiki/concepts/dispatch-vehicle-doctrine#Parent does not take over, 2026-09-24]].
- Before writing a brief, read
  [[wiki/systems/sats-pm-visible-swarm#Brief contract]]. Workers commit per milestone and report deltas plus a `<lane>/<task>`
  receipt.
- Default to TypeScript for new code where practical. Keep existing project
  languages unless asked to migrate, and avoid TypeScript `any`.
- Apply Unslop to prose. Default palette: `#050505` backgrounds, `#F5F2EA`
  text, orange only as an accent (`#FF9F0A` Sats, `#F7931A` Bitcoin). Bitcoin
  is not crypto.
- T3 Code thread: tables go inline in the reply under [[wiki/systems/task-notices-and-reporting#Report-out standard (all machines and harnesses in T3 Code)]]; show a chart, diagram or mockup that says more than prose with `html_preview`, then `html_render`, unasked. This binds delegated agents too; briefs do not restate it.
- HTML report, only on Victor's explicit ask or the html-report skill: save to Yoga `/home/proofofwork/Downloads/` unless he names another place (mirror byte-identical into task `outputs/` where the host requires it). Child builds follow [[wiki/systems/agent-skills-decision-2026-09-19]] § 8.
