#!/usr/bin/env bash
# notice-package-20261023: install items 1, 2 and 5-7 on framework-desktop in one step (INSTALL.md).
#   install.sh --head <reviewed candidate commit> [--dry-run]
# Order: verify everything, back up every live file it changes, place files, migrate asks.sqlite3 in one
# transaction, apply the requeue triage, then enable and start only the new requeue units. It restarts no
# service: the watchdog picks up its new module at its next timer tick. --dry-run stops after verification.
set -euo pipefail
umask 077

LANE=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48
CAND="$LANE/candidate"
RECORD_ROOT="${NOTICE_PACKAGE_RECORD_ROOT:-$LANE}"  # a sandbox rehearsal keeps its record in the sandbox
LIB="$HOME/.local/lib/sats-stall-watchdog"
ASKS="$LIB/sats_stall_asks.py"
NOTIFY="$HOME/.local/bin/sats-completion-notify"
MCP="$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
UNITDIR="$HOME/.config/systemd/user"
DB="$HOME/.local/state/sats-stall-watchdog/asks.sqlite3"
STATE="$HOME/.local/state/sats-completion"
RQ="$STATE/requeue"
BASE_ASKS=406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22
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

# ---- 1. verify -------------------------------------------------------------------------------------------
[ "$(hostname)" = framework-desktop ] || die "run on framework-desktop"
[ -n "$HEAD_WANT" ] || die "--head <reviewed commit> required"
[ "$(git -C "$CAND" rev-parse HEAD)" = "$(git -C "$CAND" rev-parse "$HEAD_WANT^{commit}")" ] || die "candidate HEAD is not $HEAD_WANT"
[ -z "$(git -C "$CAND" status --porcelain)" ] || die "candidate tree is not clean"

declare -A SRC=([asks]="$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py" [notify]="$CAND/notify/sats-completion-notify"
                [mcp]="$CAND/mcp/mcp_call.py")
declare -A DST=([asks]="$ASKS" [notify]="$NOTIFY" [mcp]="$MCP")
declare -A BASE=([asks]=$BASE_ASKS [notify]=$BASE_NOTIFY [mcp]=$BASE_MCP)
declare -A MODE=([asks]=644 [notify]=755 [mcp]=644)
declare -A TODO=()
for k in asks notify mcp; do
  real_dir "$(dirname "${DST[$k]}")"; real_file "${DST[$k]}"
  live=$(sha "${DST[$k]}") want=$(sha "${SRC[$k]}")
  if [ "$live" = "$want" ]; then say "$k already installed ($want)"
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

# The requeue holds exactly the triaged entries, unchanged, and the one replay is still live.
python3 -I - "$CAND/install/requeue-triage.json" "$RQ" "$DB" <<'EOF' || die "requeue no longer matches the reviewed triage; re-triage"
import hashlib, json, sqlite3, sys
from pathlib import Path
manifest, rq, db = json.load(open(sys.argv[1])), Path(sys.argv[2]), sys.argv[3]
entries = {e['file']: e for e in manifest['entries']}
live = {p.name for p in rq.glob('*.json')}
extra, gone = sorted(live - set(entries)), sorted(set(entries) - live)
changed = [f for f in live & set(entries) if hashlib.sha256((rq / f).read_bytes()).hexdigest() != entries[f]['sha256']]
done_replay = [f for f, e in entries.items() if e['decision'] == 'replay' and (e['outcome'] == 'DONE' or e['would_send_kind'] == 'done')]
connection = sqlite3.connect('file:%s?mode=ro' % db, uri=True, timeout=10)
stale_live = []
for f, e in entries.items():
    check = e.get('live_check')
    if e['decision'] == 'replay' and check:
        row = connection.execute('SELECT data FROM threads WHERE key=?', (check['watchdog_thread_key'],)).fetchone()
        if row is None or json.loads(row[0]).get('sig') != check['sig']:
            stale_live.append(f)
print(json.dumps({'entries': len(live), 'extra': extra, 'gone': gone, 'changed': changed, 'done_replay': done_replay,
                  'replay_no_longer_live': stale_live}))
sys.exit(1 if extra or changed or done_replay or stale_live else 0)
EOF

# The watchdog is between ticks and the next tick is at least 90 s away; nothing is stopped or restarted.
for _ in $(seq 1 120); do
  state=$(systemctl --user show -p ActiveState --value sats-stall-watchdog.service)
  next=$(systemctl --user show -p NextElapseUSecRealtime --value sats-stall-watchdog.timer)
  left=$(( $(date -d "$next" +%s 2>/dev/null || echo 0) - $(date +%s) ))
  if [ "$state" != activating ] && [ "$state" != active ] && [ "$left" -ge 90 ]; then break; fi
  sleep 5
done
[ "$state" != activating ] && [ "$state" != active ] && [ "$left" -ge 90 ] || die "watchdog busy or its tick is near"
WD_TIMER_BEFORE=$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)
say "watchdog idle ($state), next tick in ${left}s"

if [ "$DRY" = 1 ]; then say "dry run: every check passed; nothing changed"; exit 0; fi

# ---- 2. back up ------------------------------------------------------------------------------------------
mkdir -m 700 "$RECORD"
for k in "${!TODO[@]}"; do
  cp -p "${DST[$k]}" "${DST[$k]}.bak-notice-package-$TS"
  cp -p "${DST[$k]}" "$RECORD/$k.bak"
  [ "$(sha "${DST[$k]}.bak-notice-package-$TS")" = "${BASE[$k]}" ] || die "backup of $k does not match its base"
done
python3 -I -c 'import sqlite3,sys
s=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=30); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()' \
  "$DB" "$DB.bak-notice-package-$TS"
cp -p "$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py" "$RECORD/sats_stall_asks.candidate.py"  # rollback runs its down-migration
cp -p "$CAND/install/events_migration.py" "$RECORD/"
printf 'TS=%s\nRECORD=%s\nHEAD=%s\nWD_TIMER_BEFORE=%s\n' "$TS" "$RECORD" "$(git -C "$CAND" rev-parse HEAD)" "$WD_TIMER_BEFORE" > "$RECORD/install.env"
say "backups written ($TS)"

# ---- 3. place files (same-directory temp, then rename) ---------------------------------------------------
for k in "${!TODO[@]}"; do
  tmp="$(dirname "${DST[$k]}")/.$(basename "${DST[$k]}").notice-package-$TS"
  install -m "${MODE[$k]}" "${SRC[$k]}" "$tmp"
  mv -f "$tmp" "${DST[$k]}"
done
rm -f "$LIB"/__pycache__/sats_stall_asks.*.pyc
for u in sats-completion-requeue.service sats-completion-requeue.timer; do
  [ -e "$UNITDIR/$u" ] || install -m 644 "$CAND/notify/systemd/$u" "$UNITDIR/$u"
done
say "files placed"

# ---- 4. migrate asks.sqlite3 with the installed module, one transaction, no VACUUM or checkpoint -------
python3 -I "$CAND/install/events_migration.py" --lib "$LIB" up "$DB" > "$RECORD/migration-up.json" || die "migration failed; see $RECORD/migration-up.json and ROLLBACK.md"
say "events migrated"

# ---- 5. requeue triage: archive stale and DONE entries; the replay entry stays queued -------------------
ARCHIVE="$STATE/requeue-archive-$(date +%Y%m%d)"
[ -d "$ARCHIVE" ] || mkdir -m 700 "$ARCHIVE"
python3 -I - "$CAND/install/requeue-triage.json" "$RQ" "$ARCHIVE" "$RECORD" <<'EOF'
import json, os, sys
from pathlib import Path
manifest, rq, archive, record = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
moved = []
for e in manifest['entries']:
    if e['decision'] == 'archive' and (rq / e['file']).exists():
        target = archive / e['file']
        if target.exists():
            raise SystemExit('archive target exists: %s' % target)
        os.rename(rq / e['file'], target)
        moved.append(e)
(archive / 'MANIFEST-notice-package-20261023.json').write_text(json.dumps({'source': str(rq), 'triage': manifest['triaged_at_ct'],
                                                                         'moved': moved}, indent=1) + '\n')
(record / 'requeue-archived.json').write_text(json.dumps([e['file'] for e in moved], indent=1) + '\n')
print('archived %d; DONE entries listed: %s' % (len(moved), [e['lane'] for e in moved if e['outcome'] == 'DONE']))
EOF
ls "$RQ" > "$RECORD/requeue-after-triage.txt"

# ---- 6. the new requeue units only ----------------------------------------------------------------------
systemctl --user daemon-reload
systemctl --user enable --now sats-completion-requeue.timer
systemctl --user start --no-block sats-completion-requeue.service
say "requeue timer enabled; drainer started"

# ---- 7. verify ------------------------------------------------------------------------------------------
for k in asks notify mcp; do [ "$(sha "${DST[$k]}")" = "$(sha "${SRC[$k]}")" ] || die "$k hash after install"; done
[ "$(systemctl --user is-active sats-completion-requeue.timer)" = active ] || die "requeue timer not active"
[ "$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)" = "$WD_TIMER_BEFORE" ] || die "watchdog timer was restarted"
python3 -I -c 'import sqlite3,sys
d=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
assert d.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert any(r[1]=="ask" for r in d.execute("PRAGMA table_xinfo(events)"))
print("asks.sqlite3 per-ask schema, integrity ok")' "$DB"
say "installed; record $RECORD; next: canon push (INSTALL.md step 3), then the first watchdog tick check"
