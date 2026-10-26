---
aliases: ['secrets-map', 'api-key-locations', 'secret-locations']
title: Sats Secrets and API Locations Map
created: 2026-08-30
updated: 2026-10-25
type: system
status: active
tags: [agent-system, system-memory]
sources:
  - 'Victor 2026-10-25 11:32 AM CT GO (2), via Hash: store-writer helpers keep no .bak and print no value, length or value hash; reviewed panel ACCEPT on ff6d1744 (lane secrets-sync-drop-bak-20261025 gen2). Bearer locator now picks by the --dry-run store-scan rows'
  - 'Sats 2026-10-25 11:35 AM CT, via Hash: find why a notice-send check printed the lane-notice URL and key, and land the fix (§ read-canon.sh verbs, presence checks; lane fd-load-rca-canon-land-20261025)'
  - 'Victor 2026-10-25 10:35 AM CT, secrets-sync backup step dropped: "Drop the secrets-sync backup step; 1Password is the copy of the secret stores"'
  - 'Victor 2026-10-24, canon-gh-main-20261024 steer 7: "Crew is done. Clean it all."'
  - 'Victor 2026-10-24, canon-gh-main-20261024 steer 2: "Hermes is gone."' # History
  - path: verified on framework-desktop 2026-08-30 during the rachel-site Vercel RCA
  - Victor instruction to store newly received secrets for all Sats agents, 2026-09-30
  - Victor credential-source priority instruction and separate-task acceptance, 2026-10-01
  - read-canon.sh verbs fix after two store dumps (Victor, 2026-10-02 "Fix it so it wont happen again"), installed and tested on Framework, MBP and mini
  - F-D hub-config and key-env guards after chat key copies (Victor, 2026-10-02 "Fix it so it wont happen again"), verified on framework-desktop 2026-10-03
  - X_BEARER_TOKEN minted and stored for all Sats agents (Victor, 2026-10-07), verified HTTP 200 and MBP/mini fan-out
  - Victor HARD 2026-10-07 via Sats 19:03 CT, every secret saved to 1Password, Proton Pass and the F-D encrypted file (lane `/home/victor/work/canon-secrets-triple-store-2026-10-07/`)
  - Grok completion webhook key names, 1Password SoT and Proton BLOCKED, 2026-10-07 (`/home/victor/work/native-completion-hooks-2026-10-07/le-webhook-1p/RESULT-WEBHOOK-1P-LIVE.md`)
  - Framework `sats-op` switched to the read-write service account, probe PASS 2026-10-07 19:17 CT (`/home/victor/work/expand-watch-2026-10-07/le-1p-swap/RESULT-1P-SWAP.md`)
  - Proton writes moved to the owner default pass-cli session after Victor 2026-10-07 19:39 CT ("I want all sats agents to have read and wtite access."), 8/8 filled (`/home/victor/work/le-proton-owner-fill/RESULT-PROTON-OWNER-FILL.md`)
  - Victor 2026-10-08 05:03 CT, exposure sweep closed as keep as is (`/home/victor/work/secret-exposure-sweep-2026-10-07/VICTOR-DECISION-0503.md`)
  - Canon fleet migration 2026-10-13, step 1 secrets-store naming and remote-reader list, step 2 redaction of the Mac mini login hash (`/home/victor/work/canon-fleet-migration-20261013/s1/u04-secrets-page/RESULT.md`)
  - Victor 2026-10-13 via Sats, secrets-sync storage policy and task-specific RESUME deletion approval (`/home/victor/work/secrets-sync-20261013/frozen/TASK.md`; worker `secrets_sync_20261013/produce_canon_policy`)
  - Sats 2026-10-13 RESUME 0938, expressly authorized non-secret email note (`/home/victor/work/secrets-sync-20261013/frozen/TASK-0938.md`; worker `secrets_sync_20261013/repair_canon_history`)
  - Victor ruling 8, 2026-10-18 (D26 remote reads and copy retirement, D29 Canon MCP secrets), lane `/home/victor/work/secrets-d26-d29-20261018/REPORT.md`
  - Victor 2026-10-18 via mcp:ea02f44b ("do all 3 recommendations"), Developer ID rename off its Buzz name, lane `/home/victor/work/secrets-buzz-devid-rename-20261018/REPORT.md`
confidence: high
owner: sats
---

# Sats Secrets and API Locations Map

## Secret storage and synchronization, Victor 2026-10-13

Current route status, 2026-10-18 (Victor ruling 8, D26). Framework holds the only copy of the store. Every other Sats host reads one key at a time from Framework with `~/.local/bin/read-canon-remote.sh get KEY`: Yoga, Victor F13, the MBP and the mini. On the MBP and mini, `~/.config/sats/read-canon.sh` is a symlink to that reader, so existing callers reach Framework with no code change. A failed read exits non-zero; no host has a local copy to fall back to. The MBP and mini copies were archived encrypted on Framework and removed on 2026-10-18 (§ Sats secrets store, Remote reader copies). No fan-out or sync is needed or installed.

Route status, 2026-10-15, superseded for the MBP and mini by the 2026-10-18 status above. Victor confirmed that the F-D encrypted file is the only authoritative secrets store. Required 1Password and Proton copies by item class remain as listed below. The 2026-10-14 fleet wipe removed the live `canon-fanout` script and its service, path and timer. References to automatic fan-out below describe the former setup. Victor authorized one manual run of `/home/victor/work/fleet-wipe-20261014/archive/fd-1640/bin/canon-fanout` for the MBP and mini on 2026-10-15; its execution and readback receipt belongs to `/home/victor/work/secrets-apply-20261015/RESULT.md`. A replacement sync is recommendation-only, with no installation authorized by that recommendation.

This is the storage source of truth for every Sats agent and Grok Bot seat on every harness and host. Victor's 2026-10-13 secrets-sync instruction supersedes the universal three-store requirement of 2026-10-07 and the encrypted-file-only storage wording of 2026-09-30. Lookup order, approved retrieval routes, per-key scope and read auditing remain unchanged.

| Item class | Required stores |
|---|---|
| Logins and standalone passwords | F-D encrypted secrets store, 1Password `Sats Vault`, Proton Pass `Personal` |
| API keys, tokens and other non-login secrets | F-D encrypted secrets store and 1Password `Sats Vault` only |

For secrets, Proton Pass keeps logins and standalone passwords only. Classify by the item's contents and purpose, not just its title or vault item type. An API token in a password-shaped item remains a non-login secret. Ambiguous classification is a CONFLICT with no write.

RESUME 0938 on 2026-10-13 expressly authorizes the non-secret note "Sats Grok Bot email, forward here" in all three stores. Keep this note in Proton after migration and exclude it from `DELETE-PLAN.md`. This named exception grants no general permission to store other notes in Proton.

A save is complete only when a complete copy is verified in every required store for its class. A missing copy is BLOCKED. Report the store and key or item name, never the value.

### Store routes

The current helper dependency and missing post-commit ledger are recorded in [[#Credential helper retained after Crew retirement, 2026-10-24]].

1. Write the F-D encrypted secrets file `/home/victor/.config/sats/canon/secrets.env.age` on Framework only through the existing store-owner tools, including `/home/victor/work/secrets/canon_set.py` where applicable. Fan-out status: § Current route status above. Include nested `vaults` records when matching stored logins.
2. Use the read-write service account in `sats-op` for 1Password `Sats Vault`. Store status below records host-specific access limits.
3. Proton writes use the owner's default pass-cli session on Framework, `~/.local/share/proton-pass-cli`, `victor.vogel@only21mil.xyz`. Reads may use the agent identity `sats-fd-agent`, under [[proton-pass-cli-agent-2026-10-02]]. The owner-session checks below still apply.

The authorized `secrets_sync_20261013` synchronization and migration task writes each store directly, with no `.bak` copy first, under the No backup copies rule in `adapters/sats-shared-common.md` § Scope and writes. 1Password is the copy of the secret stores (Victor, 2026-10-25 10:35 AM CT: "Drop the secrets-sync backup step; 1Password is the copy of the secret stores"). Preserve encryption at rest; transfer values through pipes or memory. If temporary work is required, use a private directory with mode 0700, keep secret-bearing files encrypted with mode 0600, and shred only the task's own temporary files after use.

Fleet Proton saves are normally add-only. Create a missing eligible item, leave an identical item alone, and report a same-title item with a different value as a CONFLICT with no write. `sats-secret-save` is the existing add-only helper; this policy does not claim that it implements the new classification or synchronization rules. Select a route that writes only the required stores for the item class. If no supported route meets that rule, block the save. An explicitly authorized login synchronization may edit existing matching login items under the next section. Proton deletes require the separate gate below.

### Credential helper retained after Crew retirement, 2026-10-24

Victor, 12:03 PM CT: "Crew is done. Clean it all." F-D cleanup deleted `/home/victor/work/hermes_crew`, including a shared credential helper. `/home/victor/work/secrets/canon_set.py:25` imports `/home/victor/work/hermes_crew/secrets_execute/store_add.py`; `/home/victor/.local/bin/t3-mbp-mcp-bearer-renew:107` also names that helper. Root restored `store_add.py` byte-exact, SHA256 `14f84cbe44d58b1b5e4e21441c10a24e1896cc5948df6b427d046b380f3b7dd5`, and `canon_set.py --help` exits 0. The directory is retained for these consumers pending Victor's decision on moving the helper. It grants no current Crew route.

Unresolved: `store_add.py:588` calls `secrets_execute/ledger.sh` after group commits. That file was lost in the deletion and no copy was found. Passing import and `--help` checks do not prove the write or ledger path works. The helper's relocation and missing ledger remain open; no secret-store write, credential change or replacement implementation was performed by this canon task.

Sources: `/home/proofofwork/work/canon-gh-main-20261024/tasks/fd_clean/RESULT.md`, `tasks/fd_clean2/RESULT.md` and `BOARD.md` root remediation. Full dated host record: [[wiki/systems/fleet-machine-roles#Crew and Hermes host retirement, 2026-10-24]].

### Login synchronization

Match logins across the required stores by domain plus username. A title alone is insufficient. Duplicate matches, missing identity, or ambiguous domain or username mapping go to `CONFLICTS.md` with no write.

The newest trustworthy modified password wins. Use item modification time only when it reliably identifies the password update; copied or imported metadata, unrelated edits, or missing provenance cannot establish the winner. Tied times or ambiguous provenance are CONFLICTS with no write. For an authorized synchronization with one unambiguous winner, write that password to the other required stores.

Edit existing items through native edit operations so their history retains the prior values. Preserve unrelated fields and encrypted-store records. Never delete and recreate an existing item to synchronize it. If a route cannot preserve history, block that write.

After every write, read back each required copy and compare SHA-256 and byte length in memory or through pipes. Print only MATCH booleans. Keep values, secret hashes and lengths out of canon, prompts, argv, screenshots, tool output, reports, logs and chat. Record item names, store names and verification outcomes only. A mismatch blocks completion.

### Proton migration and deletion gate

Migrate non-login secrets from Proton into both the F-D encrypted store and 1Password. Preserve the complete item, including secret fields, notes and attachments when present. Verify the complete copy in each remaining store by SHA-256 and byte length without printing values. Partial copies or an unsupported field or attachment block deletion.

Before any Proton deletion, produce an encrypted Proton export using the existing secrets-store encryption configuration. Keep the export at mode 0600, record its path, verify that it decrypts and is readable, and confirm that its decrypted item count matches the Proton inventory count taken before export. Do not expose the plaintext export or secret values. If any export or count check fails, delete nothing.

Write `DELETE-PLAN.md` with the exact item names, types, stable item identifiers, count, verified complete-copy status in both remaining stores and the verified export path. Delete only the reviewed plan's exact set, after every migrated item has passed complete-copy verification in both remaining stores and the deletion step has passed review-and-babysit. Verify and record each deletion without values. A changed plan requires review of the changed set before deletion.

Victor's task-specific RESUME approval at 09:20 CT on 2026-10-13, relayed by Sats, covers only the reviewed `DELETE-PLAN.md` set for `secrets_sync_20261013`. Once all evidence and review gates above pass, that task need not ask for another deletion confirmation. This records authorization, not evidence that an export, copy, review or deletion has occurred. Future Proton deletes require explicit approval for that task and the same backup, complete-copy, exact-plan and passing-review evidence. This migration approval grants no blanket delete permission.

## Every secret goes to three stores (Victor HARD 2026-10-07)

Historical heading retained for existing links. Its universal storage requirement is superseded by § Secret storage and synchronization, Victor 2026-10-13.

> Victor, 2026-10-07, via Sats 19:03 CT: "They need to be put into proton pass and secrets file. that needs to be the standard for grokbot and all agents in the canon."

The dated store-access receipts below remain historical evidence; they do not verify this migration or change today's required stores.

**Store status, 2026-10-07 19:17 CT.** Source: `/home/victor/work/expand-watch-2026-10-07/le-1p-swap/RESULT-1P-SWAP.md` (PASS, reviewed ACCEPT on GPT-6.1 Sol `xhigh`).

- **1Password from Framework: open.** `sats-op` on Framework now loads the read-write service account by default (secrets store key `OP_SERVICE_ACCOUNT_TOKEN_RW`). A create and delete probe in `Sats Vault` passed and left nothing behind. `SATS_OP_LEGACY_RO=1 sats-op ...` selects the old read-only `Sats Fleet` account (secrets store key `OP_SERVICE_ACCOUNT_TOKEN`, [[grok-bot-1password-connect-catalog-empty-2026-09-19]]), kept as the rollback. Rollback steps: `ROLLBACK.md` in that lane.
- **1Password from MBP and Yoga: read-only.** Their `sats-op` still loads `OP_SERVICE_ACCOUNT_TOKEN`. The MBP switch is pending from Hash. Run 1Password saves on Framework until a host's switch is recorded here.
- **Proton Pass: open through the owner session, 2026-10-07 19:45 CT.** The `sats-fd-agent` token is read-only in practice: Proton returns `NotAllowed` on create even with role `Editor` (`/home/victor/work/le-proton-editor-probe-2/probe-evidence.json`). Writes run on Framework only, through the owner default session above. Before any write, unset `PROTON_PASS_PERSONAL_ACCESS_TOKEN`, `PROTON_PASS_SESSION_DIR` and `PROTON_PASS_AGENT_REASON`, and check that `pass-cli info --output json` shows the owner email. Never log in, log out, share or grant from that session. The 8 secrets from 2026-10-07 were filled this way and read back sha-equal to 1Password through both the owner session and the agent token: `/home/victor/work/le-proton-owner-fill/RESULT-PROTON-OWNER-FILL.md`.
- **Encrypted file: open.** Unchanged, written on Framework only.

Where to find credentials and API tokens on framework-desktop. **Locations and key
names only — values never enter canon** (no-secret rule, [[tracing-mortar-website-runbook]]).
All paths verified 2026-08-30.

## Credential lookup priority

> **Grok Bot fleet (Victor HARD 2026-10-07):** for seat **logins / passwords / secrets already in connected 1Password**, prefer **`ListCredentials` → credential-request**. Do **not** dig F-D Canon `~/work/secrets` / read-canon, lead with Secure Form for those passwords, or re-ask Victor when 1Password holds the item. SoT: [[1password-credentials-fleet-2026-10-07]]. For current storage destinations, read § Secret storage and synchronization, Victor 2026-10-13. Approved API-token retrieval routes remain unchanged.
>
> **Fill fails, 2026-10-11 (Victor 08:33 CT, relayed by Sats):** when the in-app 1Password fill fails, any Sats agent, Grok Bot seats included, may sign in with the password from 1Password, Proton Pass or the secrets folder (the encrypted Canon file, read with `read-canon.sh`), whichever is simplest. Rule and guardrails: [[sats-oauth-approval-browser#Sign-in fallback when 1Password fill fails, 2026-10-11]].

Victor's instruction, 2026-10-01: all Sats agents on every harness use the
existing encrypted secrets store as the primary credential source, then
the Proton Pass browser extension as secondary where supported. Use the
existing authorized retrieval route for the consuming host. The 1Password,
Bitwarden, GitHub and retired-store entries below retain their consumer or
historical scope. This preference creates no new access or extension setup.

## Tailscale API token locator, 2026-10-01

- Encrypted-store key: `TAILSCALE_API_KEY_SATS_AGENT_ACL`.
- Tailscale description: `sats-agent-acl`; account:
  `thevictorvogel@gmail.com`. Victor created this API access token with a
  selected 90-day expiry.
- Storage receipt: Victor's local MBP-to-Framework `canon_set.py` pipeline
  returned `store_exit=0` at 10:05:04 UTC on 2026-10-01. Victor then requested
  shared Sats storage at 10:09 UTC. This records the completed encrypted-store
  receipt, without reading or copying the value.
- Primary destination: Framework's existing
  `/home/victor/.config/sats/canon/secrets.env.age`. On Framework, the existing
  retrieval route is `/home/victor/.config/sats/read-canon.sh get TAILSCALE_API_KEY_SATS_AGENT_ACL`;
  capture its output inside the authorized consuming process. MBP can run the
  consuming process on Framework through its existing `framework` SSH alias;
  Yoga's existing route is `~/.local/bin/read-canon-remote.sh get KEY`.
  Apply the credential lookup priority above and the existing read-audit requirement.
- Intended for already-authorized Sats agents as needed through their existing
  approved routes. This locator grants no new access. The storage receipt does
  not verify fan-out to every account, retrieval on every harness, live API
  validity, or ACL-only privileges; the description alone proves no scope.
- API-token expiry cannot be disabled: [Tailscale's API documentation](https://tailscale.com/docs/reference/tailscale-api)
  specifies an automatic expiry selected from 1–90 days. The exact expiration
  timestamp was not independently read back; the Tailscale Keys page remains
  authoritative. Replacement or rotation remains separately authorized.

## MBP T3 Nightly MCP bearer (sats-muse-vm)

Locator, first added 2026-10-18. This is the Sats MCP bearer for the MBP T3 Nightly server (`http://100.65.3.65:3774/mcp`).

- Source of truth: the live file `/home/victor/.t3-nightly/userdata/secrets/mcp-bearer-sats-muse-vm-mbp.token` on framework-desktop (0600, `victor`). Consumers read this file.
- Store copies: each renewal by `/home/victor/.local/bin/t3-mbp-mcp-bearer-renew` creates an item titled `T3 Nightly MCP — sats-muse-vm (MBP) renewed <YYYY-MM-DDTHH:MM:SSZ>` in 1Password Sats Vault, Proton Pass Personal and the encrypted Canon file (key `SATS_SECRET_SAVE_` plus the uppercase SHA-256 hex of the title). The stores are add-only for this bearer: the script only creates items.
- Current copy: the items that the `t3-mbp-mcp-bearer-renew --dry-run` store-scan rows name as holding the live bearer. The script compares each store copy with the live file in memory and prints no value hash (helper fix ff6d1744, 2026-10-25). Pick by those rows, never by the newest title.
  - Current: `T3 Nightly MCP — sats-muse-vm (MBP) renewed 2026-10-18T23:02:41Z`, session `68547149`, expires 2026-11-17T23:02:52Z.
  - Retired (their bearer is no longer the live value; do not use): `T3 Nightly MCP — sats-muse-vm (MBP)` (session `f17685a7`) and `T3 Nightly MCP — sats-muse-vm (MBP) renewed 2026-10-09T10:41:36Z` (session `10e53f47`, revoked 2026-10-18).
- Scopes: since 0.1.1-nightly.20261018.3331, T3 gives a full-access MCP client `orchestration:read`, `orchestration:operate`, `settings:write` and `source-control:write`, and the pairing code must carry all four or the decision fails "insufficient_scope" and uses the code up. The script mints with that set (fixed 2026-10-18). The 10-09 bearer had only the two orchestration scopes.
- Renewal: before expiry, with Victor's go each time. After a run, move the titles its `locator` row names into the retired list above. Runbook: `~/work/t3-mbp-env-rca-2026-10-08/repair-bearer-r6/RUNBOOK.md`.

## X / Twitter research access

**Live 2026-10-07: X API v2 works for every Sats agent through encrypted-store key `X_BEARER_TOKEN`.** Start here for X/Twitter search, credentials or access trouble.

- Key: `X_BEARER_TOKEN`, the app-only Bearer Token of Victor's developer app `2028256853444984834Only_21Mil` (app ID `32496013`, Pay Per Use, [open the app](https://console.x.com/accounts/2028256853444984834/apps/32496013)). Victor ordered it minted and shared with all Sats agents on 2026-10-07; a Sol computer-use lane regenerated it and stored it with `canon_set.py` straight from the MBP clipboard (canon commit `4132503`, length 114). Nothing used the previous bearer.
- Verified 2026-10-07: `GET /2/users/by/username/poteto` returned HTTP 200 on Framework; `canon-fanout` pushed the store to the MBP and mini (hash `ec9c8f779d36`) and `read-canon.sh get X_BEARER_TOKEN` finds it on both. Yoga was offline; its route `~/.local/bin/read-canon-remote.sh get X_BEARER_TOKEN` reads Framework at call time and is unverified for this key.
- Call pattern (token stays out of argv, files and output; GET only):

  ```bash
  bash -c 'T=$(/home/victor/.config/sats/read-canon.sh get X_BEARER_TOKEN); printf "Authorization: Bearer %s\n" "$T" | curl -sS -H @- "https://api.x.com/2/tweets/search/recent?query=..."'
  ```

  On the MBP and mini, `~/.config/sats/read-canon.sh` has been a link to the remote reader since 2026-10-18 and still answers `get`; on Yoga and Victor F13 use `read-canon-remote.sh`. App-only auth is read-only: search, user timelines, post lookup. It cannot post, like, follow or DM. Docs: [X API v2](https://docs.x.com/x-api).
- Spend: every read draws Pay Per Use credits. Balance on 2026-09-30 was $34.36 with auto-recharge on ($5 trigger, $25 refill). Bound each research task's post count and record request and post counts. Billing settings change only with Victor's approval.
- Rotation: Regenerate in the app's Keys page revokes the old bearer. Store the new one with the same clipboard pipeline: `ssh victors-macbook-pro pbpaste | python3 -I /home/victor/work/secrets/canon_set.py X_BEARER_TOKEN --stdin -m "why"`, then clear the MBP clipboard.
- X web login source of truth: the F-D encrypted store's `vaults` record `x.com / Only_21mil`, identified by nested item name `x.com` and username `Only_21mil`. It worked 2026-10-07. The Proton copy was rejected on 2026-10-07, but the 2026-10-15 comparison found it equal to the store and 1Password, `MATCH=true`. This equality check does not establish a new X sign-in test. Receipt: `/home/victor/work/secrets-sync-20261015/receipts/phase1-apply.json`.
- X box sign-in, refresh finished 2026-10-13 under Victor's permanent X sign-in permission: 1Password Login item `v4mf7s2uu2hwj6ayugcizj4pcy` in `Sats Vault` is the Grok box login path from now on. Its imported title was blank in the 2026-10-15 inventory; `x.com` is the site name, not a verified title at that inventory. Use the stable item ID. The existing item was refreshed from the `vaults` source of truth, preserving item history; password readback matched in memory. The source has no populated TOTP. This records the credential refresh, not a box sign-in test. Owner: Lightning, `d045f3b0-e763-4eb3-b909-f49ef8bfb55a` ([[grok-bot-fleet-seats]] § Lightning owns @Only_21Mil posting, Victor decision 2026-10-16). Receipt: `/home/victor/work/x-1p-refresh-20261013/RESULT.md`.
- Other providers: last30days v3.23.0 reads X only through `xurl` app-only auth, bird (`AUTH_TOKEN` plus `CT0`) or xAI (`XAI_API_KEY`); it does not read `X_BEARER_TOKEN` directly and no `xurl` store is configured. Browser-cookie extraction stays forbidden. The app's OAuth 1 user-context keys (read and write) are a different credential and are not stored.

History: the 2026-09-30 check on Yoga found the app and its bearer but no safe way to move the value into the store, so API research stayed blocked until the clipboard-to-`canon_set.py` pipeline above.

## MBP credential and browser reuse check, 2026-10-01

Use this section for MBP saved-credential connectivity or a fresh-task session
reuse check. Initial setup evidence is from `victors-MBP-2`, macOS 26.5.2 arm64, between
01:13 and 01:22 UTC. Earlier Yoga success is separate evidence.

### Tested route and remaining CLI blocker

- Existing CLI: `/opt/homebrew/bin/op` 2.39.0. Existing secure launcher:
  `/Users/m5mbp/.local/bin/sats-op`. Its source retrieves only
  `OP_SERVICE_ACCOUNT_TOKEN` through the existing encrypted reader, captures
  the value in memory, removes account/session/Connect overrides, and supplies
  the token only to the native CLI child environment.
- Existing reader: `/Users/m5mbp/.config/sats/read-canon.sh`; local encrypted
  copy: `~/.config/sats/canon/secrets.env.age`. The encrypted file and existing
  passphrase file are owned by `m5mbp`, mode 0600. Keep Framework as sole writer.
- A found check with secret stdout discarded passed outside the task sandbox:
  `read-canon.sh get OP_SERVICE_ACCOUNT_TOKEN >/dev/null`, exit 0.
  `sats-op --help` also passed in 0.46 seconds. These prove the reader and
  launcher load path, not remote token validity or vault access.
- Inside this Codex task sandbox, the required append to
  `/var/log/canon-reads.log` is denied; the reader refuses to decrypt. The
  tested route was a scoped approved execution outside that sandbox. Keep the
  audit requirement; permission to read the encrypted file alone is insufficient.
- 1Password initially appeared not running. Opening the installed app reached
  `Sats sats566@only21mil.xyz`, locked after 60 minutes of inactivity, offering
  Mac-password unlock. Opening it did not resolve CLI account-discovery timeouts.
- Native account discovery and service-account identity timed out. The final
  15-second `sats-op --cache=false whoami --format json` probe also timed out
  with per-process `OP_BIOMETRIC_UNLOCK_ENABLED=false` and `OP_CACHE=false`.
  Stuck `op daemon --background` children were observed. The bounded RCA
  localizes the blocker to CLI daemon/transport startup; it does not establish
  an invalid token or that the locked UI caused the service-account failure.
  Only this task's stuck probes and daemon children were cleaned up.
- Current source receipts: `sats-op` SHA256
  `a8d55efb87db04f55a8614f17d9a6eb34114691d6554aff995d06901c0a0a6f2`;
  `read-canon.sh` SHA256
  `e33a5c39127015d683fdb82297376733c5541455d03c0b027b48b18eff7f71f5`.
  Neither helper was edited.

### Fresh-tab browser procedure

1. Use supported native CUA and select
   `cua.getApp('/Applications/Brave Browser.app')`. The full path avoids
   ambiguity with an existing mounted Brave installer. Browser discovery here
   exposes only Codex IAB/MCP Apps; it does not expose the daily Brave profile.
2. Read current app state. The existing Profiles menu showed `Personal`.
   Preserve unrelated tabs. Open one owned tab with `super+t`, type
   `https://myaccount.google.com/`, press Return, then fetch fresh AX state.
3. Require visible Google Account identity `Victor Vogel` /
   `thevictorvogel@gmail.com`. Stop a read-only persistence check at any login
   or human verification gate and report it; a stored credential is not needed
   to manufacture this test.
4. Close only the owned test tab after readback. Keep Brave running.

Two fresh owned tabs passed with that exact account and no password or MFA
prompt. Both were closed; four pre-existing tabs remained, including the other
lane's Tailscale ACL editor and Apple's sign-in tab. No ACL, device tag, API key,
Apple account, browser storage or security setting was changed. Native app
controls hold no portable browser-tab ID; the next task must bind the app afresh.

### Separate-task acceptance and practical route, 2026-10-01

Both acceptance checks passed; receipt recorded at 01:33 UTC.

- Browser: a new native CUA binding to `/Applications/Brave Browser.app`
  on `victors-MBP-2` (macOS 26.5.2 arm64), profile `Personal`, opened one
  owned tab with `super+t` at `https://myaccount.google.com/`. Fresh AX
  state visibly identified `Victor Vogel / thevictorvogel@gmail.com`
  without password, MFA or autofill action. Only that tab was closed; the
  four pre-existing Tailscale, OpenAI, Apple and about:blank tabs remained.
- API: MBP's existing `framework` SSH alias reached `victor@100.94.71.50`,
  host `framework-desktop` (Linux x86_64), with `BatchMode=yes` and
  `StrictHostKeyChecking=yes` against existing host keys. The installed
  `/home/victor/.local/bin/sats-op user get --me --format json`, bounded
  to 25 seconds, exited 0 and returned only allowlisted identity evidence:
  `Sats Fleet / SERVICE_ACCOUNT / ACTIVE`. Native CLI:
  `/home/victor/.local/bin/op` 2.32.0.
- Framework launcher SHA256:
  `20e98241dee7b48f38f4db32182b3c0b1131e3cefbbd7191582de7517027db0c`,
  mode 0755. Its inspected source uses Framework's fixed
  `/home/victor/.config/sats/read-canon.sh` locator; MBP uses its home-relative
  locator. Each loads `OP_SERVICE_ACCOUNT_TOKEN` from its own encrypted
  reader into the native child environment. No secret crossed SSH; no
  vault or item contents were queried.
- Practical default: use MBP Brave Personal for browser work and invoke
  existing Framework consumers over the authorized SSH route for API work.
  Apply the credential lookup priority above. This verifies separate-task
  browser reuse and a usable MBP-to-Framework authenticated consumer route,
  independently of Yoga. The earlier MBP native CLI timeout remains.
- Proton Pass installation/autofill, reboot/sleep recovery, continuous
  availability and zero-prompt operation were not tested. Requested model
  profile: GPT-6.1 Sol/xhigh; effective profile was not exposed by these checks.
  Credentials, lock settings, services, ACLs and keys were unchanged.

### Unattended limits and unverified evidence

The encrypted reader can run without interactive unlock on this existing
account when its audit append is permitted. The existing service-account
design supports headless consumers, but MBP API authentication remains
unverified because of the daemon timeout. No vault/item inventory was attempted.

The browser reused a valid session in a logged-in GUI. Reboot/sleep recovery
and always-on operation were not tested. A fresh task still
needs supported native CUA access to this same host/profile. Codex's separate
browser or the dot VM is not a demonstrated cookie/credential bridge.

Keep the observed 60-minute 1Password lock. Human account CLI access can still
require app unlock and per-process authorization; an unlocked desktop alone
does not prove CLI authentication. This session did not have a verified
non-echoing secret-to-native-unlock helper. Touch ID, an unreachable MFA device,
hardware key or account-required reauthentication can require the person's
action. Existing accessible verification routes remain task-scoped under
[[sats-oauth-approval-browser]]. The successful tab checks establish no
zero-prompt guarantee.

Requested profile was GPT-6.1 Sol/xhigh. The current installed routing source
supports it; available local thread metadata did not confirm the running model
or effort. No unrelated running session was claimed to reload.

## When any Sats agent receives a secret

> Storage destinations and copy verification follow § Secret storage and synchronization, Victor 2026-10-13. The 2026-09-30 direction below retains its secure-transfer and scope rules; it no longer defines the complete set of required stores.

Victor's direction, 2026-09-30: whenever a Sats agent obtains a secret for
authorized Victor/Sats work, arrange to save it in the existing encrypted
Sats secrets store so all already-authorized Sats agents can retrieve
it through their existing approved routes.

1. Resolve the task's scope and the existing encrypted destination. Framework's
   `/home/victor/.config/sats/canon/secrets.env.age` remains the writable store;
   Yoga's `read-canon-remote.sh` is a retrieval route, not a storage writer.
2. Verify a supported secure-entry or store-owner transfer route and its
   destination before transferring the value. If that route is unavailable,
   stop the storage step, retain the secret at its existing secure origin,
   and report the exact capability gap without the value. This page supplies
   no new writer or handoff.
3. Preserve existing keys unless replacement or rotation is specifically
   authorized. Confirm completion through a non-secret storage receipt and
   supported found/missing check with secret-bearing stdout discarded and
   only its exit status reported; never emit secret values. Report a requested distribution as pending
   (fan-out status: § Secret storage and synchronization). Report pending
   or failed checks without claiming that a documentation edit proves storage,
   access, or runtime adoption.
4. Put only variable names, store locators, and retrieval instructions in WIKI.
   Keep values out of plaintext or temporary files, prompts, argv, screenshots,
   tool output, reports, logs, and chat.

Existing shared-store access and per-key scope boundaries remain unchanged.
This directive grants no access to additional people or agents, creates no
credentials or persistent access, and waives no higher-priority confirmation,
authentication, rotation, signing, or handoff requirement.

## Framework Laptop 13 Pro (`only21mil-F13Pro`), 2026-10-10

Swarm root `a61193bf`, pack `/home/victor/work/13pro-yoga-fix-20261010`; Victor 04:51 CT answers relayed by Sats (Q1).

- No canon push target. `canon-fanout` did not copy `secrets.env.age` or `read-canon.sh` to this host. The `only21mil` login reads canon secrets through `~/.local/bin/read-canon-remote.sh get KEY` (SSH to F-D, the Yoga design; `fix/F05a-wrappers-only21mil`). The `sats` login has no route: its copy of that script, `sats-op` and its SSH identity were moved out and removed on 2026-10-10 (`fix/F05b-wrappers-sats`, `fix/F19-sats-creds-strip`). An agent on that login has no canon route until someone designs one (F19 RESULT). The canon markdown mount at `~/Obsidian/Victor/Agent-Shared` (SSHFS, `fix/F09-canon-mount`) does not carry the store.
- Hub key file: `~/.config/sats-hub/client-key` for each of `only21mil` and `sats`, mode 600, owned by that login, holding `CREW_CLIPROXY_KEY_VICTOR` (`key_4e531f35b2419b144f38d937`). `~/.local/libexec/sats-hub-key` prints it for Claude Code (`apiKeyHelper`, both logins) and for `only21mil` default Codex (`auth.command`), and refuses a missing, symlinked, foreign-owned or non-600/400 file. `sats` Codex does not use the helper: its wrapper exports `SATS_HUB_KEY` from the key file to the provider's `env_key`. The `only21mil` ChatGPT app home also uses `env_key`, fed by `~/bin/chatgpt`; `~/bin/codex` no longer exports the key (F01d). The older `client.key` and the tunnel's `/run/user/1000/sats-hub/client.key` are gone. See [[sats-router-usage-sources]] § Per-person keys.
- Lesson (R-F17 r1, fixed in F17r): the first hub-key probe wrote the key to a 600 `mktemp` header file in `/tmp` for a few seconds and the reply to `/tmp`. It was deleted and a residue scan found nothing, but the rule above still failed. Probes pipe the header into `curl -H @-` and stream the reply to the parser, so no key touches disk or argv.

## Checking rendered hub config and key env vars, 2026-10-03

Victor, 2026-10-02: "Fix it so it wont happen again". Agent tool output is
stored with the chat (T3 `state.sqlite`, Claude Code and Cursor transcripts,
Codex rollouts and `shell_snapshots`), so a printed value becomes a lasting copy.

- Check the rendered hub config under `/run/user/1000/sats-hub/` (for example
  `cliproxyapi.yaml`) by counts and key names only:
  `grep -c 'api-key' FILE`, `grep -o '^ *[a-z-]*:' FILE | sort | uniq -c`.
  Compare a value through `cmp -s` or `sha256sum` exit status.
- Check a key env var by presence only: `[ -n "${NAME:-}" ]`. Keep `env`,
  `printenv`, `export -p` and `bash -x` traces out of shells that hold `SATS_*`
  keys.
- F-D guards (2026-10-03): Claude Code `permissions.deny`
  `Read(//run/user/1000/sats-hub/**)` in `~/.claude` and
  `~/.claude-accounts/thevictorvogel-gmail`; every F-D Codex home has a
  `[shell_environment_policy] exclude` for `SATS_*` key, token, secret and pass
  names, so they stay out of Codex child shells and `shell_snapshots`;
  `t3-router-agent.py` sets `SATS_ROUTER_API_KEY` only for `CODEX_MASON`, whose
  provider reads it through `env_key`. Bash, Cursor and other harnesses rely on
  the count-only rule. Record: `theo_build/deploy/fd-key-copies.md`.

## Hub router keys — durable residences (2026-10-21)

The 2026-10-21 hub key census and vault organize phase 1 fixed the durable homes of the router keys. Full record: [[wiki/systems/sats-hub-one-hub-decision-and-failback-2026-10-21]] (Hub key census). Locations only — values are never written here.

- `SATS_ROUTER_API_KEY` — 1Password, Sats Vault, "Sats Hub / Router API key (SATS_ROUTER_API_KEY)" (item gmx5exqfuxmocgpugrdibgtyhq).
- `SATS_ROUTER_MASON_API_KEY` — 1Password, Sats Vault, "Sats Hub / Router API key — Mason (SATS_ROUTER_MASON_API_KEY)" (item xzbvlj6zelcfod35v7vu5uswo4).
- `SATS_ROUTER_CLIENT_MASON_API_KEY` — 1Password, Sats Vault, "Sats Hub / Router client key — Mason (SATS_ROUTER_CLIENT_MASON_API_KEY)" (item ojpzfwdhocuqc2xu2fovefaume).
- `SATS_ROUTER_OPENROUTER_CREDENTIAL_ID` — 1Password, Sats Vault, "Sats Hub / Router OpenRouter credential ID (SATS_ROUTER_OPENROUTER_CREDENTIAL_ID)" (item fzocqgp5oxoup6qdbffyyfuwq4).
- Router management secret — Proton Pass, Personal vault, item "Sats Router", the password field.
- `OPENROUTER_API_KEY` — Proton Pass, Personal vault, item "openrouter.ai", the "API Key" field.
- `SATS_HUB_CLIENT_API_KEY` / CREW client key — 1Password, Sats Vault, "CLIProxy hub key: Victor (sats-router)".

The four SATS_ROUTER_* items are those keys' first durable residence; before 2026-10-21 they existed only in the standby's env on the MacBook Pro.

## Stores and consumers (reference)

### Sats secrets store (path `canon/`)

Formerly "Sats secret store (Canon)"; links to § Sats secret store land here. The file is `/home/victor/.config/sats/canon/secrets.env.age`. Despite the `canon/` path, the secrets store is not canon: canon is a scope's `Agent-Shared` tree ([[wiki/systems/naming-glossary]] § Canon and the secrets store).

**Always encrypted at rest** (age, passphrase-based) since 2026-09-19. The old
plaintext `/home/victor/.config/sats/secrets.env` no longer exists on disk.

#### Fleet keychain, Yoga keyring and Yoga disk unlock, 2026-10-17

The MBP, F-D, Mac mini and Yoga login keychains and keyrings all use the
saved `SATS_FLEET_LINUX_LOGIN_PASSWORD` (verified 2026-10-17). Yoga
`proofofwork` logs in through SDDM autologin. User unit
`sats-yoga-keyring-unlock.service` decrypts
`/etc/credstore.encrypted/sats-yoga-login-keyring` (host key plus TPM2) and
unlocks the login keyring. Yoga root LUKS2 unlocks through a PCR7 TPM2 token
in keyslot 1; passphrase slot 0 stays usable. One test reboot passed
acceptance on 2026-10-17. Backups, rollback steps and receipts are in
[[wiki/archive/sats-secrets-host-diaries-2026-10-17]].

#### read-canon.sh verbs (2026-10-02)

The reader prints only what its verb names. Scripts capture one value in
memory: `VAR="$(read-canon.sh get KEY)"`.

| Command | Prints |
|---------|--------|
| `read-canon.sh get KEY` | KEY's value only, no key name, no trailing newline. Missing key: exit 1. |
| `read-canon.sh env KEY [KEY...]` | The store's own `KEY=value` lines for the named keys, in store order. One decrypt for callers that need several keys (the sats-mail family). A missing key gets a stderr note; exit stays 0. |
| `read-canon.sh list-keys` | Key names, one per line. Never values. |
| `read-canon.sh dump --yes-print-all-secrets` | The whole store, for a person at a terminal. Refused with exit 2 when stdout is a pipe, file or agent tool. |

Off Framework the reader is `read-canon-remote.sh`, which answers `get KEY`
only: Framework's `read-canon.sh` prints the value, and a missing key exits 1.
Any other verb or an invalid key name exits 64 before any SSH. A caller that
needs several keys calls `get` once per key.

Check that a key loads without printing it. A presence check prints only its
exit status: `v=$(read-canon-remote.sh get KEY) && [ -n "$v" ]; echo $?`. For
a lane-notice entry, run `sats-lane-notice route --owner <bot>`. It reports
`"route":"owner"` only when both `LANE_NOTICES_URL_<BOT>` and
`LANE_NOTICES_KEY_<BOT>` load, and prints neither. Never pipe a reader's
stdout, even after `>/dev/null`. zsh, the login shell on the MBP and mini and
in Claude Code's Bash tool, has MULTIOS on, so `get KEY 2>&1 >/dev/null | head`
sends the value both to `/dev/null` and into the pipe. That is how a T3
thread printed the Hash lane-notice URL and key into its tool output on
2026-10-25 (fd-load-rca-canon-land-20261025). The sender was not involved.

No arguments, `-h`, `--help`, `help`, an unknown verb or a malformed verb
prints usage to stderr and exits 2 without decrypting. Two agents dumped the
store on 2026-10-02 by running the old helper with no arguments; that path is
closed on every host.

Legacy exception: the running sats-router reads the whole store with no
arguments (`cmd/sats-router/store.go`, `readCanonValues`). The helper honours
that call only on Linux, from a process in `sats-router.service` or
`sats-hub-dashboard.service` whose parent executable is named `sats-router`,
with stdout not a terminal. Remove the exception once the router reads with
`list-keys` plus `get`/`env`; that needs a router build and deploy.

- Source of truth: Framework `/home/victor/.config/sats/read-canon.sh`, the
  only decrypting copy since 2026-10-18. The former `canon-fanout`, removed
  2026-10-14, used to push it to the MBP and mini; their copies and `.bak`
  versions are in the D26 archives below. Test harness (throwaway
  age store, never the real secrets store): `/home/victor/.config/sats/test-read-canon.sh SCRIPT`.
- This age build needs a TTY for passphrase entry, so the helper drives age
  through a pty; the passphrase never goes to age on stdin. The helper never
  writes plaintext to disk.
- Read sign-in sheet (added 2026-09-19): every decrypting `read-canon.sh`
  invocation appends an attempt line to `/var/log/canon-reads.log` BEFORE
  decryption is attempted (failed attempts included), plus a completion line
  with the exit status afterward. Refused invocations are logged best-effort
  with `result=exit_2`. Fields: UTC timestamp, invoking user, sudo user if any,
  hostname, PID, argv. Names/paths only — never the passphrase, never secret
  values. The log is root-owned, mode `0622` (any user may append, only root
  may read), with the filesystem append-only flag (`chattr +a`; works on this
  host's btrfs) — no non-root user can modify or delete entries. Fail-closed:
  if the log cannot be appended, the helper refuses to decrypt. Remote reads
  run Framework's helper, so Framework's log records them as user `victor`.
  On 2026-10-18 the MBP and mini had no `/var/log/canon-reads.log`, so their
  local readers had been refusing every decrypt before D26 retired them.
- Passphrase: `$HOME/.config/sats/.passphrase` (0600) on each approved Sats
  and Archimedes account that holds a store copy; Victor and Rachel share this one
  store (Victor, 2026-09-27). Never in git, wiki, logs, or chat.
  gnome-keyring/secret-tool was evaluated 2026-09-19 and is not usable
  non-interactively on Framework (no D-Bus session), hence the 0600 file.
- Store location: Framework's `/home/victor/.config/sats/canon/` git repo is
  the authoritative copy and, since 2026-10-18, the only one. Until the
  2026-10-14 fleet wipe, `canon-fanout` pushed copies of the encrypted
  `secrets.env.age` and `read-canon.sh` to `$HOME/.config/sats/` on the MBP
  (`m5mbp`) and the mini (`m4mini`). On 2026-10-18 (Victor ruling 8, D26)
  both copies were stale against Framework. Each host's store file, its two
  `.bak` copies, `.passphrase`, `read-canon.sh` and its `.bak` versions (plus
  the MBP's `~/.cache/canon.passphrase.age`) were archived encrypted with the
  store passphrase, round-trip checked, then removed. Archives, base64 tar
  inside age:
  `/home/victor/work/secrets-d26-d29-20261018/archive/mbp-m5mbp-sats-store-copy-20261018.tar.b64.age`
  (sha256 `59299257ed7c6e2babec0a8044ae5ef9d4542eac722dfbe6f6d39c3d67482652`) and
  `/home/victor/work/secrets-d26-d29-20261018/archive/mini-m4mini-sats-store-copy-20261018.tar.b64.age`
  (sha256 `ce1ace2d99b6ae8d915c53f89637ae5aa6c30558a3cfffafe10842122656b33c`).
  Restore steps are in the lane's `REPORT.md`. `canon-fanout` never copied
  the store to Yoga, Victor F13 or a family host.
- Remote reader copies. Yoga and Victor F13 checked 2026-10-13
  (`/home/victor/work/canon-fleet-migration-20261013/s0/u14-yoga-host/RESULT.md`
  findings 6 and 14); MBP and mini installed and proved 2026-10-18. No copy
  holds the store file. The reader script runs one SSH command,
  `read-canon.sh get KEY` on Framework, and has no fallback.
  - MBP `m5mbp`: `~/.local/bin/read-canon-remote.sh` (mode 755,
    byte-identical to Yoga and F13, sha256
    `43aae1ae15f06ea1253748c61eac92473070628f2604bf6f923164a2a7863945`),
    through the existing `framework` alias. `~/.config/sats/read-canon.sh` is
    a symlink to it. Callers: `sats-op` and
    `~/.local/share/sats-standby/bin/runtime.py` for the standby cliproxy
    launchd jobs. `~/.local/libexec/sats-hub-mgmt-key` already read over SSH.
  - Mini `m4mini`: `~/.local/bin/read-canon-remote.sh` (sha256
    `334eb18c66fe3005ed04d42f34c9ca6afb3c4b051b59099ab6b1fc7f95422171`). It
    differs from the Yoga copy only in using the `framework-victor` alias,
    because the mini's `framework` alias logs in to Rachel's `rachelvogel`
    account and stays unchanged. `~/.config/sats/read-canon.sh` is a symlink to
    it. No live caller on the mini used the store.
  - Yoga `proofofwork`: `/home/proofofwork/.local/bin/read-canon-remote.sh`
    (mode 755). It checks the key name, then runs `read-canon.sh get KEY` as
    `victor` on Framework through the `framework` ssh alias. Caller:
    `sats-op` (line 14).
  - Yoga `muse-sats` (uid 1210, GECOS "Muse non-root (U21
    fleet-handoff-20261010)"; no canon or lane record names its owner):
    `~/.local/bin/read-canon-remote.sh` (mode 700), with
    `~/.config/sats/read-canon.sh` a symlink to it. Its ssh config logs in to
    Framework as `muse-sats`, where `/etc/sudoers.d/60-muse-sats` lets that
    user run `/usr/local/libexec/muse-sats/read-canon` as `victor`.
  - Victor F13 `only21mil`: `~/.local/bin/read-canon-remote.sh`, see
    § Framework Laptop 13 Pro above.
- Tamper-evident history: `/home/victor/.config/sats/canon/` is a git repo;
  every change to the store = one commit (hash-linked, append-only).
  Convention documented in `canon/README.md`. **2026-09-30 correction:** the
  earlier decrypt/edit/re-encrypt/shred-temporary-file recipe is retired for
  agent secret intake. Follow § When any Sats agent receives a secret.
- The encrypted pre-merge backup `secrets.env.backup-2026-09-19.age` and the
  other pre-rotation `.age` backups were deleted on 2026-09-27
  (task `secrets/execute`, item X12).
- 2026-09-19 merge: the 1Password-export payload from the Yoga added 3 keys
  (`userId`, `vaults`, `version`; `vaults` holds 510 vault items as JSON).
  Zero conflicts — all three keys were new.
- Bootstrap passphrase came from the `Today.odt` doc in the Yoga's
  `~/Downloads` (Victor deletes the bootstrap himself when ready).
  The short bootstrap phrase was replaced on 2026-09-19 19:25 (canon
  `b9ac899`) by a 44-character random passphrase; the old phrase opens only
  pre-rotation git blobs, which never leave Framework.

Verified key families (2026-08-30, carried into the encrypted Canon unchanged):

| Key family | Purpose |
|------------|---------|
| `GH_TOKEN` | GitHub |
| `OPENROUTER_API_KEY` | OpenRouter |
| `EXPO_TOKEN` | Expo |
| `CONVEX_DEPLOY_KEY` / `CONVEX_READ_TOKEN` / `CONVEX_SYNC_TOKEN` | Convex |
| `BW_EMAIL` / `BW_CLIENTID` / `BW_CLIENTSECRET` / `BW_MASTER_PASSWORD` | Bitwarden CLI unlock |
| `PROTON_BRIDGE_*` (host, port, user, pass) | Proton Mail Bridge IMAP |
| `RESTIC_PASSWORD_FRAMEWORK` / `RESTIC_PASSWORD_SATS_HOME` | restic backups |
| `SUNSHINE_*` (framework/mbp/mini user+pass) | Sunshine game-stream hosts |
| OpenAI, 3 accounts: `OPENAI_SATS21M_LOGIN` / `_TOTP_URI`, `OPENAI_PROOF_OF_WORK1_LOGIN` / `_PASSWORD`, `OPENAI_SATS566_LOGIN` / `_PASSWORD`. Cursor, 2: `CURSOR_VICTOR_LOGIN` / `_PASSWORD`, `CURSOR_RACHEL_LOGIN` / `_PASSWORD`. Muse, 1: `MUSE_VICTOR_LOGIN` / `_PASSWORD` (Mason's `MASON_MUSE_*` predates this) | Sats Router hub account web logins, promoted from `vaults` 2026-09-27 (canon `0c223df`, trimmed to hub accounts in `7f96202`) |
| Mason: `MASON_MUSE_LOGIN` / `_PASSWORD`; `MASON_GMAIL_LOGIN` / `_PASSWORD`; `MASON_OPENAI_LOGIN` / `_PASSWORD` | Mason's account logins. `MASON_MUSE_*` added 2026-09-24 (canon `9123a58`). `MASON_GMAIL_*` is Mason's 566 Gmail, the Google account used for Mason's Claude login, added 2026-09-27 (canon `babd175`). `MASON_OPENAI_*` is Mason's OpenAI web login (a different Gmail address from `MASON_GMAIL_LOGIN`), from the Fold Markor note, added 2026-09-27 (canon `c53c12b`) |
| Rachel: `RACHEL_MBA_MACOS_LOGIN` / `RACHEL_MBA_MACOS_PASSWORD` | macOS login for `rachelvogel` on `rachels-macbook-air-m5`, for Screen Sharing into her session (Sats Router app Keychain step). Victor 2026-10-03; canon `fc3deeb`, fanned out to MBP and mini. Also in Proton Pass, vault Personal, item "Rachel MacBook Air (macOS login)" |
| `VERCEL_TOKEN` | Vercel deploys (rachel-site, Linen Closet, tracingmortar.com). From the OpenClaw JSON, 2026-09-27 (canon `12f3307`) |
| `X_BEARER_TOKEN` | X API v2 app-only bearer, app 32496013, read-only research for all Sats agents. 2026-10-07 (canon `4132503`); see [[#X / Twitter research access]] |
| `BRAVE_API_KEY` / `DEEPSEEK_API_KEY` / `INWORLD_API_KEY` / `OPENCLAW_GATEWAY_TOKEN` | OpenClaw provider keys and Victoria voice (Inworld). From the OpenClaw JSON, 2026-09-27 (canon `12f3307`) |
| `TELEGRAM_BOT_TOKEN_ARCHIMEDES` / `_ALPHEUS` / `_SHINING` / `_ALISTAIR` | **Retired 2026-10-24 (Hermes retired, Victor):** former Hermes gateway bots for Rachel, Mason, Maddox and Megan. Secret record retained; do not render or start a Hermes service. Added 2026-09-27 (canon `47e061b`) |
| `SATS_USER_CLIPROXY_CLIENT_TOKEN` | `sats` user claudex proxy client token, fetched at call time through `canon-key-run`. 2026-09-27 (canon `91d7d71`) |
| `SATS_CLAUDEX_CLIENT_KEY` | MBP claudex CLIProxyAPI client key; `claudex-proxy-start` renders `client-key.env` from it at LaunchAgent start. 2026-09-27 (canon `91d7d71`) |
| `RACHEL_AGE_IDENTITY_20260922` | Rachel's age identity backup, moved out of her synced vault. 2026-09-27 (canon `91d7d71`) |
| `APPLE_DISTRIBUTION_P12_B64` / `APPLE_MAC_INSTALLER_P12_B64` | Apple signing p12 files, base64. Decode into a 0700 dir under `$HOME`, never `/tmp`. 2026-09-27 (canon `8c6f436`) |
| `APPLE_DEVELOPER_ID_P12_B64` / `APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD` / `APPLE_DEVELOPER_ID_PRIVATE_KEY_PEM_B64` | The store's only Apple Developer ID Application identity, team-wide signing for apps distributed outside the App Store. Moved off its Buzz name 2026-10-18 (canon `19d848a`); see [[#Apple Developer ID Application identity, 2026-10-18]] |
| `MIGRATION_20260721_*_GPG_PASSPHRASE` (5) | Passphrases for the 2026-07-21 personal migration `tar.zst.gpg` archives. 2026-09-27 (canon `08b65db`) |
| `CREW_FCM_SERVICE_ACCOUNT_JSON_B64` / `CREW_FCM_GOOGLE_SERVICES_JSON_B64` / `CREW_FCM_PROJECT_ID` / `CREW_FCM_SENDER_ID` | **Retired 2026-10-24, Victor: "Crew is done. Clean it all."** Former Crew app Firebase Cloud Messaging push (canon `42a7f01`). Retained records grant no current render, push or release route. |
| `CREW_API_SERVER_KEY_<AGENT>` (8): `_DEFAULT`, `_VICTOR_COS`, `_RACHEL_COS`, `_VICTOR_TRAVEL`, `_RACHEL_TRAVEL`, `_RACHEL_HOME`, `_MASON_COS`, `_MASON_TRAVEL` | **Retired 2026-10-24 (Hermes retired, Victor):** former Hermes `API_SERVER_KEY` records for `~/.hermes-crew` profiles. Secret record retained; do not render or use for a current route. 2026-09-27 (canon `e9032bb`) |
| `CREW_API_SERVER_KEY_MAIN_<PROFILE>` (14): `_DEFAULT` (Sats), `_CHANNEL`, `_ELECTRUM`, `_GENESIS`, `_HASH`, `_LEDGER`, `_LIGHTNING`, `_MEMPOOL`, `_MINER`, `_NODE`, `_RELAY`, `_SEED`, `_TAPROOT`, `_UTXO` | **Retired 2026-10-24 (Hermes retired, Victor):** former Hermes `API_SERVER_KEY` records for Victor's main Hermes and Crew link. Secret record retained; do not render or use for a current route. 2026-10-03 (canon `e05cc2f`) |
| `CANON_MCP_SERVER_KEYS_JSON` / `CANON_MCP_POCKETID_CLIENT_SECRET` | `canon-mcp.service` signing and OAuth-state encryption keys (the one-line `server-keys.json`) and its Pocket ID OIDC client secret. Added 2026-10-18 (canon `a32115b`, `46fb806`); see [[#Canon MCP service secrets, 2026-10-18]] |

`FAMILY_CLIPROXY_CLIENT_KEY` was never added: its source and the
family-cliproxyapi service were removed on 2026-09-27 before the merge.

### Canon MCP service secrets, 2026-10-18

Victor ruling 8 (D29). Item class: non-login secrets, so the F-D store and
1Password `Sats Vault` hold them, each read back MATCH on 2026-10-18.

| Store key | 1Password item ID | Runtime credential |
|---|---|---|
| `CANON_MCP_SERVER_KEYS_JSON` | `u6ozunlkcufm7gzv4l6zmfpvy4` | `/etc/credstore.encrypted/canon-mcp.server-keys.json`, name `server-keys.json` |
| `CANON_MCP_POCKETID_CLIENT_SECRET` | `dc36jztgbevxy4ipgbwaro6bau` | `/etc/credstore.encrypted/canon-mcp.pocketid-client-secret`, name `pocketid-client-secret` |

- `canon-mcp.service` loads both with `LoadCredentialEncrypted=` (systemd-creds,
  host key plus TPM2, no PCR binding). Service wiring and rollback:
  [[wiki/systems/canon-mcp-server-2026-09-27#Repair and secret move, 2026-10-18]].
- The OAuth state in `~/.config/canon-mcp/oauth-state` stays where the server
  writes it. Its values are Fernet ciphertext under the encryption key in
  `CANON_MCP_SERVER_KEYS_JSON`. Keep that key and that state together, with no
  rotation unless Victor asks; a new key invalidates every session.
- Rebuild a credential from the store on Framework:
  `read-canon.sh get KEY | sudo systemd-creds encrypt --name=NAME --with-key=host+tpm2 - PATH`.
  The 2026-10-18 `server-keys.json` credential also carries the original
  file's trailing newline (`{ read-canon.sh get KEY; echo; } | ...`). After a
  rotation, update the store, the 1Password item and the credential together.

### Apple Developer ID Application identity, 2026-10-18

Certificate "Developer ID Application: Victor Vogel (384ZGKG4GB)", issued by
Developer ID Certification Authority G2, valid 2026-09-07 to 2031-09-08. Victor
kept it on 2026-10-18 as team-wide signing and had it renamed off its Buzz
name. Item class: non-login secrets, so the F-D store and 1Password
`Sats Vault` hold it, each read back MATCH on 2026-10-18. The p12, its
password and the PEM key were checked in memory to be one identity.

| Store key | 1Password item ID | Contents |
|---|---|---|
| `APPLE_DEVELOPER_ID_P12_B64` | `nc55bmabjggealo6mjldnjh3fm` | base64 PKCS#12: certificate, private key and the G2 intermediate |
| `APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD` | `7dxkv4n7beoawa3nlch2zl4thu` | export password of that PKCS#12 |
| `APPLE_DEVELOPER_ID_PRIVATE_KEY_PEM_B64` | `mxqcbqtb3jb4guphrul3ache3a` | base64 of the same private key as unencrypted PEM |

Decode into a 0700 directory under `$HOME`, never `/tmp`. Each 1Password item
is titled with its store key. Receipt:
`/home/victor/work/secrets-buzz-devid-rename-20261018/REPORT.md`.

### OpenClaw legacy secrets JSON (retired 2026-09-27)

Retired 2026-09-27: the OpenClaw JSON's keys, `VERCEL_TOKEN` included, now
live in `secrets.env.age`, and the file
(`/home/victor/.openclaw/shared-memory/victor/private/openclaw-secrets.json`)
is deleted. `CODEX_API_KEY` and `GEMINI_API_KEY` were dead and were dropped.
The JSON's `CONVEX_READ_TOKEN` failed a live Convex test, so the store value
stayed.

The runbook for tracingmortar.com previously pointed at a nonexistent
`/home/victor/.openclaw/.env`; that pointer was corrected 2026-08-30 (see
[[tracing-mortar-website-runbook]]).

### Bitwarden — `bw` CLI (locked by default)

Unlock with the `BW_*` vars from the primary encrypted secrets store:

```bash
export BW_SESSION="$(bw unlock --raw --passwordenv BW_MASTER_PASSWORD)"
```

Then `bw list items --search <term>` / `bw get item <id>`. Verified items
(2026-08-30): `vercel.com` (username `thevictorvogel-8207` only — **no API token
stored**), `SMTP Proton Token`. Do not echo passwords; inspect lengths/types
with `jq` filters instead.

### GitHub CLI token — `gh auth` on Framework (2026-09-24)

The GitHub token (`GH_TOKEN`, a `gho_` OAuth token, account `only21mil`, scopes
`gist, read:org, repo, workflow`) lives in the GitHub CLI credential store on
Framework. `gh auth login --with-token` seeded it and `gh auth setup-git` wired
git to it, so `gh` and `git push` authenticate with no `GH_TOKEN` in the
environment (verified headless via `su -m victor -c "... gh api user"`). This is
the token's proper home; do not copy it into env files, scripts, or SSH command
lines. Before 2026-09-24 the muse host passed it inline over Tailscale SSH, which
logged it into the journal; task `fleet_access/token_scrub` scrubbed those copies
without rotating the token.

**GitHub `notifications` scope, Victor 2026-10-17.** Per-PR subscription
writes under [[wiki/systems/upstream-pr-go-gate-2026-10-11#GitHub PR subscription, Victor 2026-10-17]]
also need the OAuth `notifications` scope, so the target scope set for the
`only21mil` `gh` login Sats/Victor lanes use is `gist, read:org, repo,
workflow, notifications`. Victor preauthorized every Sats/Victor lane, agent
and machine to add that one scope and manage those PR subscriptions without
asking again. On 2026-10-17 the reachable Framework Desktop, MBP, Mac mini,
Yoga and Framework 13 Pro logins still read back without `notifications`;
that is the normal-login state, not a blocker for subscription writes. The
encrypted store also holds a notifications-capable GitHub credential: item
title `GH Token` in the vault export under Canon key `vaults` in
`/home/victor/.config/sats/canon/secrets.env.age`, read with
`/home/victor/.config/sats/read-canon.sh get vaults`. Names and locators
only here; the value stays out of canon. Use that credential in memory only
as the `GH_TOKEN` for the `gh` subscription set/readback subprocess. It has
broader scopes than the normal fleet login, so never install it as a
machine's `gh` login, replace `GH_TOKEN` fleet-wide with it, or copy it into
argv, files, logs or another machine. If it is unavailable, add
`notifications` through the machine's supported `gh` refresh or login route
under the same preauthorization, keep that credential in its existing `gh`
store or approved supply route, and verify with `gh auth status`. Never
print or copy a token value to make the change. On 2026-10-17 the in-memory
CLI route set and verified `SUBSCRIBED` on all 27 open `only21mil`-authored
PRs; the normal fleet logins were left unchanged.

### GH_TOKEN in the T3 environment, core dumps off (2026-09-24)

Victor chose to leave `GH_TOKEN` in the T3 nightly environment
(`t3code-nightly.service`, set by drop-in `70-gh-token.conf` and its wrapper)
instead of restarting T3, which would cut every running thread. T3 passes it to
the Claude sessions it spawns and to their children. Crash dumps of those
processes used to store it: `fleet_access/token_scrub` deleted 26 systemd
coredumps whose core files and `COREDUMP_ENVIRON` held it.

Guard (`fleet_access/coredump_guard`): every process that carries `GH_TOKEN`
runs with a core limit of exactly 1 byte. `kernel.core_pattern` pipes to
systemd-coredump, and only a limit of 1 makes the kernel abort before starting
the helper ("RLIMIT_CORE is set to 1, aborting core"), so nothing reaches the
journal or `/var/lib/systemd/coredump`. A limit of 0 does not work. The kernel
still runs systemd-coredump, which skips the core but writes the whole
environment to the user journal as `COREDUMP_ENVIRON`. `Storage=none` plus
`ProcessSizeMax=0` in coredump.conf leaks the same way. Canary crash tests
showed all three results, and no coredump.conf drop-in is installed.

- Running processes: `prlimit --pid <pid> --core=1` on all 18 token-carrying
  processes and the rest of the T3 cgroup, with nothing restarted. Children
  inherit the limit.
- Next T3 start: `~/.config/systemd/user/t3code-nightly.service.d/65-no-core.conf`
  sets `LimitCORE=1`.
- Check: `prlimit --pid <pid> --core` reads `1 1`. A process that gets
  `GH_TOKEN` from anywhere other than T3 needs the same limit.

### Grok completion webhook (Lightning), 2026-10-07

`~/.local/bin/sats-completion-notify` posts each AUTO lane's completion report to the Grok routine webhook Lightning created (delivery: [[lane-milestones-and-stall-watchdog#Terminal delivery integration]]; notice routing: [[wiki/systems/task-notices-and-reporting#Terminal self-report]], Route). Names and locators only:

- **SoT:** 1Password item "Grok completion webhook (Lightning)" in `Sats Vault` (fields `url`, `key`).
- **Secrets store keys:** `GROK_COMPLETION_WEBHOOK_URL` and `GROK_COMPLETION_WEBHOOK_KEY` in the F-D encrypted file.
- **Service accounts pass `--vault`.** Under a 1Password service account, `sats-op item get "<title>"` without `--vault` is refused; the hook names the vault explicitly.
- **Proton Pass mirror, historical 2026-10-07: BLOCKED under the then-current three-store rule.** The save through the `sats-fd-agent` session returned `NotAllowed` in the Personal vault; the receipt recorded copies in the encrypted file and 1Password. The owner-session write route opened at 19:45 CT, and a retry was not recorded here. The 2026-10-13 policy requires only the encrypted file and 1Password for this non-login secret. This wording does not verify its current copies or any migration.
- Source: `/home/victor/work/native-completion-hooks-2026-10-07/le-webhook-1p/RESULT-WEBHOOK-1P-LIVE.md`.

## Exposure sweep closed: keep as is (Victor 2026-10-08 05:03 CT)

Victor, replying to the 2026-10-07 secret exposure sweep findings: "It is what it is. Please keep it the way it is and close the thread."

- No rotation and no shredding of local copies for the keys that sweep found. Nothing was deleted or changed.
- Every NEEDS-VICTOR item of that sweep is closed as keep as is. Sats archived thread `mcp:b94e4ec7`.
- A later rotation of those keys needs a new Victor ask.
- Evidence, with secrets named only by sha12: `/home/victor/work/secret-exposure-sweep-2026-10-07/` (`RESULT-SECRET-EXPOSURE-SWEEP.md`, `VICTOR-DECISION-0503.md`).

### Mac mini m4mini macOS login (2026-10-08)

Victor, 2026-10-08: "I think its the same as all the other logins. Please verify and add to the 1password." Verified: the Mac mini's macOS login password (user `m4mini` on `victors-Mini`, SSH alias `mac-mini`, FileVault on, macOS 26.5.1) is the same value as `MBP_MACOS_LOGIN_PASSWORD`. Confirmed non-destructively with one `dscl . -authonly m4mini` probe over SSH (rc=0, password sent through a pty prompt, never argv). Lane: `/home/victor/work/mini-login-pw-2026-10-08/`.

- **Title (new dated item):** `Mac mini m4mini macOS login 2026-10-08`. Secrets store key `SATS_SECRET_SAVE_27C2584955E44BDECC4B9F79568A7043BF5B20A2610CEB6CA965126BF6BC796A`. Canon fleet migration step 2 removed its length and hash prefix from this line on 2026-10-13; the value was never recorded.
- **Three stores (all PASS, add-only create):** 1Password `Sats Vault`; Proton Pass `Personal` (owner default session); F-D encrypted Canon under deterministic title key `SATS_SECRET_SAVE_27C2584955E44BDECC4B9F79568A7043BF5B20A2610CEB6CA965126BF6BC796A`. Each store read back the same sha12 (removed 2026-10-13).
- Same value as `MBP_MACOS_LOGIN_PASSWORD`; no existing item was edited or deleted.

## Rules recap

- Values never in canon, prompts, argv, logs, or `/tmp`; load from the store in the
  same invocation that uses them.
- Edit and decrypt the store only on Framework, its only copy since 2026-10-18.
  Other hosts read one key with `read-canon-remote.sh get KEY`, and Framework's
  `/var/log/canon-reads.log` records each read.
- Pass secrets to helpers via stdin, never argv or plaintext files.
- Read with a verb: `get KEY` in scripts, `env KEY...` for several keys,
  `list-keys` for names. `dump` is for a person at a terminal.
- For receiving/storage and synchronization, follow § Secret storage and synchronization, Victor 2026-10-13 and the secure-transfer steps in § When any Sats agent receives a secret.
- Never put a token or secret on an SSH command line to a fleet host. The command
  line is logged; Tailscale SSH records it in `tailscaled`'s journal. The target
  host supplies its own auth. See [[sats-fleet-ssh-and-screen-sharing-access]]
  § Never send secrets in SSH command lines (2026-09-24).
- A secret written into a synced folder has already replicated. Remove it on
  every peer of that folder and from each peer's `.stversions/`, not only
  locally; the peers are in [[canon-sync-fabric-2026-09-24]].
- Rotation/ownership is Victor's.
- When a canon page names a token, name the variable and the store path, not the value.

## Related

- [[tracing-mortar-website-runbook]] — VERCEL_TOKEN consumer (rachel-site deploys)
- [[sats-victor-personal-gmail-access]] — Gmail OAuth credential fan-out and revocation path
- [[claude-credential-guardian]] — protects `~/.claude/.credentials.json` from blanking
- [[sats-memory-check-preflight]] — where memory/secret lookups start
- [[1password-credentials-fleet-2026-10-07]] — Grok Bot fleet: ListCredentials → credential-request first (Victor HARD 2026-10-07)
- [[proton-pass-cli-agent-2026-10-02]] — Proton Pass agent CLI for login and standalone-password storage
