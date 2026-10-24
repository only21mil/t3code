#!/usr/bin/env bash
# notice-package-20261023: install items 1, 2 and 5-7 on framework-desktop in one step (INSTALL.md).
#   install.sh --head <reviewed candidate commit> [--dry-run]
# Order: verify everything, back up every live file it changes, place files, migrate asks.sqlite3 in one
# transaction, recheck the replay entry's thread and apply the requeue triage, then enable and start only the new
# requeue units. It restarts no service: the watchdog picks up its new modules at its next timer tick. --dry-run
# stops after verification; it reads systemctl state and local files only and writes nothing.
# A rerun after an interrupted install resumes it: a file already at the candidate keeps its ORIGINAL base backup,
# found beside it and recorded for rollback, and is never backed up again (SOL-8).
set -euo pipefail
umask 077

LANE=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48
CAND="$LANE/candidate"
RECORD_ROOT="${NOTICE_PACKAGE_RECORD_ROOT:-$LANE}"  # a sandbox rehearsal keeps its record in the sandbox
LIB="$HOME/.local/lib/sats-stall-watchdog"
ASKS="$LIB/sats_stall_asks.py"
WATCHDOG="$LIB/sats_stall_watchdog.py"
NOTIFY="$HOME/.local/bin/sats-completion-notify"
MCP="$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
UNITDIR="$HOME/.config/systemd/user"
DB="$HOME/.local/state/sats-stall-watchdog/asks.sqlite3"
STATE="$HOME/.local/state/sats-completion"
RQ="$STATE/requeue"
BASE_ASKS=406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22
BASE_WATCHDOG=6ea2e6fb3fe1134b0a5f3b99962c2837842b20fda06ce9632e74e206dfa1a06d
BASE_NOTIFY=ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62
BASE_MCP=d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7

HEAD_WANT="" DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --head) HEAD_WANT="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "usage: install.sh --head <commit> [--dry-run]" >&2; exit 2 ;;
  esac
done

TS=$(date +%Y%m%dT%H%M%S)
RECORD="$RECORD_ROOT/install-record-$TS"
say() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { say "STOP: $*"; exit 1; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
real_file() {  # a regular file whose every path component is real (no symlink anywhere)
  [ -f "$1" ] && [ ! -L "$1" ] && [ "$(readlink -f "$1")" = "$1" ] || die "$1 is not a regular, symlink-free path"
}
real_dir() { [ -d "$1" ] && [ "$(readlink -f "$1")" = "$1" ] || die "$1 is not a real directory"; }
base_backup() {  # the earliest .bak-notice-package-* beside $1 that is a real file with sha $2: the original backup
  local f
  for f in "$1".bak-notice-package-*; do
    if [ -f "$f" ] && [ ! -L "$f" ] && [ "$(sha "$f")" = "$2" ]; then echo "$f"; return 0; fi
  done
  return 1
}
gate() {  # wait (at most 10 min) until the watchdog is between ticks with its next tick 90 s or more away
  local i
  for i in $(seq 1 120); do
    if GATE=$(python3 -I "$CAND/install/watchdog_gate.py"); then return 0; fi
    [ "$i" = 120 ] || sleep 5
  done
  return 1
}

# ---- 1. verify -------------------------------------------------------------------------------------------
[ "$(hostname)" = framework-desktop ] || die "run on framework-desktop"
[ -n "$HEAD_WANT" ] || die "--head <reviewed commit> required"
[ "$(git -C "$CAND" rev-parse HEAD)" = "$(git -C "$CAND" rev-parse "$HEAD_WANT^{commit}")" ] || die "candidate HEAD is not $HEAD_WANT"
[ -z "$(git -C "$CAND" status --porcelain)" ] || die "candidate tree is not clean"

declare -A SRC=([asks]="$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py" [notify]="$CAND/notify/sats-completion-notify"
                [mcp]="$CAND/mcp/mcp_call.py" [watchdog]="$CAND/tools/sats-stall-watchdog/src/sats_stall_watchdog.py")
declare -A DST=([asks]="$ASKS" [notify]="$NOTIFY" [mcp]="$MCP" [watchdog]="$WATCHDOG")
declare -A BASE=([asks]=$BASE_ASKS [notify]=$BASE_NOTIFY [mcp]=$BASE_MCP [watchdog]=$BASE_WATCHDOG)
declare -A MODE=([asks]=644 [notify]=755 [mcp]=644 [watchdog]=644)
FILES="asks watchdog notify mcp"
declare -A TODO=() ORIG=()
for k in $FILES; do
  real_dir "$(dirname "${DST[$k]}")"; real_file "${DST[$k]}"
  live=$(sha "${DST[$k]}") want=$(sha "${SRC[$k]}")
  if [ "$live" = "$want" ]; then
    # An interrupted install placed it: its original backup is the base copy that install wrote beside it.
    ORIG[$k]=$(base_backup "${DST[$k]}" "${BASE[$k]}") || die "$k is already the candidate but no backup of its base ${BASE[$k]:0:12} is beside it (ROLLBACK.md)"
    say "$k already installed ($want); original backup ${ORIG[$k]}"
  elif [ "$live" = "${BASE[$k]}" ]; then TODO[$k]=1; say "$k: ${BASE[$k]:0:12} -> ${want:0:12}"
  else die "$k live hash $live is neither the base nor the candidate"; fi
done
real_dir "$UNITDIR"
for u in sats-completion-requeue.service sats-completion-requeue.timer; do
  if [ -e "$UNITDIR/$u" ] || [ -L "$UNITDIR/$u" ]; then
    cmp -s "$UNITDIR/$u" "$CAND/notify/systemd/$u" || die "$UNITDIR/$u exists and differs"
  fi
done
real_file "$DB"; real_dir "$RQ"

# The requeue holds exactly the triaged entries, unchanged (sha256), and no DONE entry is marked for replay. Whether
# the replay entry's ask is still unanswered is read from its thread right before the replay (step 5, SOL-7).
python3 -I - "$CAND/install/requeue-triage.json" "$RQ" <<'PY' || die "requeue no longer matches the reviewed triage; re-triage"
import hashlib, json, sys
from pathlib import Path
manifest, rq = json.load(open(sys.argv[1])), Path(sys.argv[2])
entries = {e['file']: e for e in manifest['entries']}
live = {p.name for p in rq.glob('*.json')}
extra, gone = sorted(live - set(entries)), sorted(set(entries) - live)
changed = [f for f in live & set(entries) if hashlib.sha256((rq / f).read_bytes()).hexdigest() != entries[f]['sha256']]
done_replay = [f for f, e in entries.items() if e['decision'] == 'replay' and (e['outcome'] == 'DONE' or e['would_send_kind'] == 'done')]
print(json.dumps({'entries': len(live), 'extra': extra, 'gone': gone, 'changed': changed, 'done_replay': done_replay}))
sys.exit(1 if extra or changed or done_replay else 0)
PY

# The watchdog is between ticks and the next tick is at least 90 s away; nothing is stopped or restarted. The timer
# is monotonic, so the gate reads list-timers' next elapse (install/watchdog_gate.py, DS-H1).
gate || die "watchdog busy or its tick is near: $GATE"
WD_TIMER_BEFORE=$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)
say "watchdog idle: $GATE"

if [ "$DRY" = 1 ]; then say "dry run: every check passed; nothing changed"; exit 0; fi

# ---- 2. back up ------------------------------------------------------------------------------------------
# Each file's rollback source is its ORIGINAL base backup: written now for a file still at its base, or the one an
# interrupted install wrote for a file already at the candidate. No backup is ever overwritten.
mkdir -m 700 "$RECORD"
declare -A BAK=()
for k in $FILES; do
  if [ -n "${TODO[$k]:-}" ]; then
    BAK[$k]="${DST[$k]}.bak-notice-package-$TS" from="this install"
    [ ! -e "${BAK[$k]}" ] && [ ! -L "${BAK[$k]}" ] || die "${BAK[$k]} exists"
    cp -p "${DST[$k]}" "${BAK[$k]}"
  else
    BAK[$k]="${ORIG[$k]}" from="an interrupted install"
  fi
  [ "$(sha "${BAK[$k]}")" = "${BASE[$k]}" ] || die "backup of $k does not match its base"
  cp -p "${BAK[$k]}" "$RECORD/$k.bak"
  printf '%s %s %s (%s)\n' "$k" "${BASE[$k]}" "${BAK[$k]}" "$from" >> "$RECORD/backups.txt"
done
per_ask() {  # exit 0 when the asks.sqlite3 at $1 already keys events per ask; read-only
  python3 -I -c 'import sqlite3,sys
d=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=30)
sys.exit(0 if any(r[1]=="ask" for r in d.execute("PRAGMA table_xinfo(events)")) else 1)' "$1"
}
python3 -I -c 'import sqlite3,sys
s=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()' \
  "$DB" "$DB.bak-notice-package-$TS"
DB_BAK_ORIGINAL="$DB.bak-notice-package-$TS"
if per_ask "$DB"; then  # an interrupted install migrated it: the original copy is the one that install took
  DB_BAK_ORIGINAL=""
  for f in "$DB".bak-notice-package-*; do
    if [ -f "$f" ] && [ ! -L "$f" ] && ! per_ask "$f"; then DB_BAK_ORIGINAL="$f"; break; fi
  done
fi
printf 'db %s\n' "${DB_BAK_ORIGINAL:-no one-per-generation copy found}" >> "$RECORD/backups.txt"
cp -p "$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py" "$RECORD/sats_stall_asks.candidate.py"  # rollback runs its down-migration
cp -p "$CAND/install/events_migration.py" "$CAND/install/watchdog_gate.py" "$RECORD/"
{
  printf 'TS=%q\nRECORD=%q\nHEAD=%q\nWD_TIMER_BEFORE=%q\nDB_BAK_ORIGINAL=%q\n' "$TS" "$RECORD" "$(git -C "$CAND" rev-parse HEAD)" \
    "$WD_TIMER_BEFORE" "$DB_BAK_ORIGINAL"
  for k in $FILES; do printf 'BAK_%s=%q\nBASE_%s=%q\nCAND_%s=%q\n' "$k" "${BAK[$k]}" "$k" "${BASE[$k]}" "$k" "$(sha "${SRC[$k]}")"; done
} > "$RECORD/install.env"  # sourced by rollback.sh
say "backups written ($TS):"; sed 's/^/  /' "$RECORD/backups.txt"

# ---- 3. place files (same-directory temp, then rename) ---------------------------------------------------
for k in $FILES; do
  [ -n "${TODO[$k]:-}" ] || continue
  tmp="$(dirname "${DST[$k]}")/.$(basename "${DST[$k]}").notice-package-$TS"
  install -m "${MODE[$k]}" "${SRC[$k]}" "$tmp"
  mv -f "$tmp" "${DST[$k]}"
done
rm -f "$LIB"/__pycache__/sats_stall_asks.*.pyc "$LIB"/__pycache__/sats_stall_watchdog.*.pyc
for u in sats-completion-requeue.service sats-completion-requeue.timer; do
  [ -e "$UNITDIR/$u" ] || install -m 644 "$CAND/notify/systemd/$u" "$UNITDIR/$u"
done
say "files placed"

# ---- 4. migrate asks.sqlite3 with the installed module, one transaction, no VACUUM or checkpoint -------
python3 -I "$CAND/install/events_migration.py" --lib "$LIB" up "$DB" > "$RECORD/migration-up.json" || die "migration failed; see $RECORD/migration-up.json and ROLLBACK.md"
say "events migrated"

# ---- 5. requeue triage: recheck the replay entry's thread, archive stale, DONE and answered entries ----------
# Right before the drainer starts, each replay entry's thread is read (t3_thread_read, read-only, through the
# reviewed mcp_call.py with its PACK in this record). A user message after its ask, or a failed read, archives it
# instead of replaying it (SOL-7). Settled state is not an answer: a9acdeb1 was settled by the 19:39 sweep.
python3 -I "$CAND/install/replay_recheck.py" "$CAND/install/requeue-triage.json" "$CAND/mcp/mcp_call.py" \
  "$RECORD/thread-recheck" > "$RECORD/replay-recheck.json" || say "replay recheck failed; every replay entry is archived"
ARCHIVE="$STATE/requeue-archive-$(date +%Y%m%d)"
[ -d "$ARCHIVE" ] || mkdir -m 700 "$ARCHIVE"
python3 -I - "$CAND/install/requeue-triage.json" "$RQ" "$ARCHIVE" "$RECORD" <<'PY'
import json, os, sys
from pathlib import Path
manifest, rq, archive, record = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
try:
    still = set(json.loads((record / 'replay-recheck.json').read_text())['replay'])
except (OSError, ValueError, KeyError, TypeError):
    still = set()  # no readable recheck: nothing replays
moved = []
for e in manifest['entries']:
    if e['decision'] == 'replay' and e['file'] not in still:
        e = dict(e, decision='archive', reason='answered or unverified at install (replay-recheck.json): ' + e['reason'])
    if e['decision'] == 'archive' and (rq / e['file']).exists():
        target = archive / e['file']
        if target.exists():
            raise SystemExit('archive target exists: %s' % target)
        os.rename(rq / e['file'], target)
        moved.append(e)
(archive / 'MANIFEST-notice-package-20261023.json').write_text(json.dumps({'source': str(rq), 'triage': manifest['triaged_at_ct'],
                                                                         'moved': moved}, indent=1) + '\n')
(record / 'requeue-archived.json').write_text(json.dumps([e['file'] for e in moved], indent=1) + '\n')
print('archived %d; DONE entries listed: %s; replay entries kept: %d'
      % (len(moved), [e['lane'] for e in moved if e['outcome'] == 'DONE'], len(still)))
PY
ls "$RQ" > "$RECORD/requeue-after-triage.txt"

# ---- 6. the new requeue units only ----------------------------------------------------------------------
systemctl --user daemon-reload
systemctl --user enable --now sats-completion-requeue.timer
systemctl --user start --no-block sats-completion-requeue.service
say "requeue timer enabled; drainer started"

# ---- 7. verify ------------------------------------------------------------------------------------------
for k in $FILES; do [ "$(sha "${DST[$k]}")" = "$(sha "${SRC[$k]}")" ] || die "$k hash after install"; done
[ "$(systemctl --user is-active sats-completion-requeue.timer)" = active ] || die "requeue timer not active"
[ "$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)" = "$WD_TIMER_BEFORE" ] || die "watchdog timer was restarted"
python3 -I -c 'import sqlite3,sys
d=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
assert d.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert any(r[1]=="ask" for r in d.execute("PRAGMA table_xinfo(events)"))
print("asks.sqlite3 per-ask schema, integrity ok")' "$DB"
say "installed; record $RECORD; next: canon push (INSTALL.md step 3), then the first watchdog tick check"
