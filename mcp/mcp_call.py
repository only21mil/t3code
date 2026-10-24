"""Minimal MCP (streamable HTTP) client for the T3 Nightly servers.

Usage: python3 -I mcp_call.py [--host NAME] list            -> writes tool schemas to mcp-tools.json
       python3 -I mcp_call.py [--host NAME] call TOOL JSON  -> calls one tool, prints the result
       python3 -I mcp_call.py pick                          -> prints `host: NAME URL` for a new thread
--env NAME is the same as --host NAME: it drives that environment with its own token.
Without --host, existing RPC reads and project operations still use F-D.
`pick` selects the existing Muse VM (`muse`) for a NEW thread started by the Muse app only (r16, Victor 2026-10-21; scoped to Muse the same evening). Other seats name their host.
It requires the VM's configured T3 URL and usable token; failure never falls back to another host.
Record NAME and pass --host NAME on every call for the thread, project lookup first:
a project ID belongs to one host, so pick once per thread. Thread creation requires an explicit
--host/--env, including fd for a deliberately named F-D task. Existing threads keep their host.
--host NAME prints the same `host:` line before the output.
The bearer token is read from the 0600 token file and never printed, errors included.
"""
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

FD_URL = "http://100.94.71.50:3774"
TOKEN_DIR = "/home/victor/.config/t3-mcp"
HOSTS = "/home/victor/.config/sats-pick/hosts"
PACK = "/home/victor/work/t3-mcp-connect-2026-10-07"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
T3URL = re.compile(r"https?://[A-Za-z0-9.-]+(:[0-9]+)?/?")


def token_file(name: str) -> str:
    return f"{TOKEN_DIR}/victor-{name}-nightly.token"


def read_token(name: str) -> str | None:
    """Return the host's bearer, or None when its file is missing, empty or not one line of printable ASCII."""
    try:
        with open(token_file(name), encoding="ascii") as fh:
            token = fh.read().strip()
    except (OSError, ValueError):
        return None
    if not token or not all("!" <= c <= "~" for c in token):
        return None
    return token


def host_url(host: str) -> str:
    """Return the T3 base URL for --host NAME: fd, or a hosts-file row with a T3 URL."""
    if host == "fd":
        return FD_URL
    rows = []
    if NAME.fullmatch(host):
        try:
            with open(HOSTS) as fh:
                rows = [line.split() for line in fh if line.strip() and not line.lstrip().startswith("#")]
        except FileNotFoundError:
            pass
    row = next((r for r in rows if r[0] == host), None)
    if row is None or len(row) < 3 or not T3URL.fullmatch(row[2]):
        raise SystemExit(f"host {host}: no T3 URL in {HOSTS}")
    return row[2].rstrip("/")


def pick() -> tuple[str, str]:
    """Select the existing Muse VM for a new thread, without fleet fallback or SSH probes."""
    name = "muse"
    base = host_url(name)
    if read_token(name) is None:
        raise SystemExit(f"pick: host {name} has no usable T3 MCP token at {token_file(name)}; no fallback")
    return name, base


def failure(e: Exception) -> str:
    """Name a transport error by HTTP status, errno or class only.

    Exception messages and OSError.strerror can quote headers, the bearer too, so neither is printed.
    The errno text comes from os.strerror on the validated number.
    """
    if isinstance(e, urllib.error.HTTPError):
        code = e.code
        return f"HTTP {code}" if type(code) is int and 100 <= code <= 599 else type(e).__name__
    reason = e.reason if isinstance(e, urllib.error.URLError) else e
    if isinstance(reason, OSError):
        num = reason.errno
        if type(num) is int and 0 < num < 4096:
            return f"{type(reason).__name__} errno {num}: {os.strerror(num)}"
        return type(reason).__name__
    return type(e).__name__


TERMINAL_RUN = {"completed", "failed", "cancelled", "interrupted", "rolled_back"}
VERDICT = re.compile(r"(ACCEPT|REQUEST_CHANGES)\b")
RESULT_PATH = re.compile(r"(/(?:home|Users)/[A-Za-z0-9._/-]+/RESULT\.md)")
STILL_OPEN = re.compile(r"NEEDS-VICTOR|^[ \t>*_-]*(?:BLOCKED|FAILED|CANCEL+ED)\b", re.M)
# A reviewer child: one that voted, or whose title or thread id names a review seat in the fleet's forms: a
# review_<task> name ("Sol 6.1 High review · review_notice_package_20261023_r3"), a leading review ("review-r1-opus"),
# "<seat> review · <task>", a numbered review or re-review ("Kimi K3.1 review round 1 DeepSeek", "re-review 2 Opus"),
# a re-review named for its seat ("focused re-review DeepSeek"), or a review right after the model's separator
# ("DeepSeek V4.1 Flash high - re-review of notice package"). A title that names a producer anywhere in a producer
# role is no seat (NEW-2, R3-5): a producer word that opens the title, prefixes a task name ("repair_<task>") or is
# followed by of, for, by, round, a number or a separator ("Round-1 repair of review findings", "Notice package review
# round 2 repair by Sol", "Opus 5.5 XHigh repair · repair_<task>_r3"). A producer word inside a task name
# ("review_hub_fix_r2") or after of or the ("re-review of the repair") names the work under review, not the seat's.
REVIEWER = re.compile(r"(?:^|[\s·:|/-])(?:re-?)?review_|^\s*(?:re-?)?review\b|\b(?:re-?)?review\s+·"
                      r"|\b(?:re-?)?review\s+(?:round\s*|r)?\d"
                      r"|\bre-?review\s+(?:opus|deepseek|sol|gpt|claude|kimi|grok|gemini|qwen|glm|sonnet|haiku|fable|codex)\b"
                      r"|\s[-–—|·:]\s+(?:focused\s+)?(?:re-?)?review\b", re.I)
PRODUCER = re.compile(r"(?:^|(?<=[\s·:|/(\[]))(?:repair|producer|produce|fix|implement|build|write|draft)(?=_|\b)", re.I)
PRODUCER_ROLE = re.compile(r"_|\s*(?:of|for|by|round|r?\d|[·:|]|[-–—]\s|$)", re.I)


def producer_role(name: str) -> bool:
    """True when a producer word in the title is the seat's own work (PRODUCER, PRODUCER_ROLE), not the work under review."""
    for found in PRODUCER.finditer(name):
        before = name[:found.start()].split()
        if before and before[-1].lower() in ("of", "the", "for", "on", "to", "a", "an"):
            continue
        if not before or PRODUCER_ROLE.match(name, found.end()):
            return True
    return False


def reviewer_seat(name: str) -> bool:
    """True when a child's title or thread id names a review seat (REVIEWER) and no producer role (producer_role)."""
    return REVIEWER.search(name) is not None and not producer_role(name)
# The F-D stall watchdog's install: its classify() is the ask detection a settle must agree with.
WATCHDOG_LIB = "/home/victor/.local/lib/sats-stall-watchdog"
TEXT_LIMIT = 20000


def watchdog_classify():
    """sats_stall_asks.classify from the installed watchdog, so a settle reads a reply's asks exactly as the
    watchdog's notices do (SOL-5). Missing, the guard refuses rather than guess."""
    if WATCHDOG_LIB not in sys.path:
        sys.path.insert(0, WATCHDOG_LIB)
    try:
        import sats_stall_asks
        return sats_stall_asks.classify
    except (ImportError, AttributeError, SyntaxError):
        raise SystemExit("settle guard: the stall watchdog's ask detection is unavailable; nothing settled") from None


def sweep_settle_refusal(rpc, host: str, thread_id: str) -> str | None:
    """Why a settle of another thread must not run, or None.

    Victor 19:47 CT 2026-10-23: a sweep settles only a thread with a terminal
    ACCEPTED RESULT and no live children or pending votes. The server already
    refuses an active run, a queued message and a pending request; this adds
    the children, votes and RESULT it cannot see. A thread settling itself
    (no threadId) keeps its own self-settle checks."""
    def read(tool: str, args: dict) -> dict:
        out = rpc("tools/call", {"name": tool, "arguments": args})
        if out.get("isError"):
            raise SystemExit(f"settle guard: {tool} failed; nothing settled")
        return json.loads(out["content"][0]["text"])

    head = read("t3_thread_read", {"threadId": thread_id, "view": "messages", "limit": 1, "maxCharsPerItem": 1, "runLimit": 1})
    thread = head["thread"]
    if thread.get("activeRunId") or thread.get("pendingRequestCount"):
        return "thread has an active run or a pending request"
    tail = read("t3_thread_read", {"threadId": thread_id, "view": "messages", "runLimit": 1, "limit": 40,
                                   "maxCharsPerItem": TEXT_LIMIT, "afterPosition": max(0, thread["itemCount"] - 41)})
    items = tail["items"]
    done = [n for n, i in enumerate(items) if i["type"] == "assistant_message" and i["status"] == "completed"
            and i["text"].lstrip(" \t>*_-#").startswith("DONE")]
    if not done:
        return "no reply leads with DONE"
    final = items[done[-1]]["text"]
    classify = watchdog_classify()
    for n, later in enumerate(items[done[-1]:]):
        if n and later["type"] == "user_message":
            return "a message arrived after the DONE reply"
        if later["type"] != "assistant_message":
            continue
        if later.get("textTruncated"):
            return "a reply from the DONE reply on is too long to check whole"
        # Every form the watchdog notifies (NEEDS-VICTOR, BLOCKED lines, bold **BLOCKED**, "Decision for you",
        # Closed as BLOCKED, fenced or inline) keeps the thread open, in the DONE reply and every reply after it.
        verdict = classify(later["text"], final=True)
        if (verdict is not None and verdict[3] is not None) or (n and STILL_OPEN.search(later["text"])):
            return ("the DONE reply" if not n else "a reply after DONE") + " is BLOCKED or asks Victor"
    children = []
    cursor = None
    while True:
        page = read("t3_thread_list", {"projectId": thread["projectId"], "includeSubagents": True, "limit": 100,
                                       **({} if cursor is None else {"cursor": cursor})})
        children += [t for t in page.get("threads", []) if t.get("parentThreadId") == thread_id]
        cursor = page.get("nextCursor")
        if cursor is None:
            break
    votes: dict[str, tuple[str, str]] = {}
    for child in children:
        state = read("t3_thread_read", {"threadId": child["threadId"], "view": "messages", "limit": 1,
                                        "maxCharsPerItem": 1, "runLimit": 1})
        runs = state.get("recentRuns") or []
        if state["thread"].get("activeRunId") or (runs and runs[0]["status"] not in TERMINAL_RUN):
            return f"child {child['threadId']} is still working (live child or pending vote)"
        last = read("t3_thread_read", {"threadId": child["threadId"], "view": "messages", "runLimit": 1, "limit": 20,
                                       "maxCharsPerItem": 200, "afterPosition": max(0, state["thread"]["itemCount"] - 21)})
        said = [i for i in last["items"] if i["type"] == "assistant_message" and i["status"] == "completed"]
        verdict = VERDICT.match(said[-1]["text"].lstrip()) if said else None
        named = (child.get("title"), state["thread"].get("title"), child["threadId"])
        if verdict or any(reviewer_seat(str(v or "")) for v in named):
            # Every reviewer seat the parent started is required, and a seat is its model: its newest review
            # stands. A review that ended without a verdict (BLOCKED, no reply, a failed or cancelled run) is that
            # seat's missing vote (SOL-6). A reviewer the parent never started is not visible here; the controller's
            # review record owns that coverage.
            seat = state["thread"].get("model") or child["threadId"]
            at = (runs[0].get("completedAt") or "") if runs else ""
            vote = verdict.group(1) if verdict and runs and runs[0]["status"] == "completed" else "no ACCEPT"
            if seat not in votes or at > votes[seat][0]:
                votes[seat] = (at, vote)
    if any(vote == "REQUEST_CHANGES" for _, vote in votes.values()):
        return "a reviewer's newest vote is REQUEST_CHANGES"
    missing = sorted(seat for seat, (_, vote) in votes.items() if vote != "ACCEPT")
    if missing:
        return f"reviewer {', '.join(missing)} ended without an ACCEPT (BLOCKED, no verdict or failed run)"
    path = RESULT_PATH.search(final)
    if path is None:
        return "final reply names no RESULT.md"
    probe = ["head", "-n", "60", path.group(1)]
    shown = subprocess.run(probe if host == "fd" else ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, *probe],
                           capture_output=True, text=True, timeout=30)
    lines = shown.stdout.splitlines()
    if shown.returncode != 0 or not lines or not lines[0].strip().startswith("DONE"):
        return "RESULT.md line 1 is not DONE"
    if not votes and not re.search(r"(?im)^.*\breview\b.*\bnot required\b", shown.stdout):
        return "no reviewer ACCEPT and RESULT.md does not say review is not required"
    return None


def main(argv: list[str]) -> None:
    if argv == ["pick"]:
        print("host:", *pick())
        return
    host = None
    if argv[:1] in (["--host"], ["--env"]):
        if len(argv) < 2 or argv[1] == "pick" or not NAME.fullmatch(argv[1]):
            raise SystemExit("--host/--env takes a host name; run `mcp_call.py pick` once per thread, then --host NAME")
        host, argv = argv[1], argv[2:]
    if argv == ["list"]:
        arguments = None
    elif len(argv) == 3 and argv[0] == "call":
        try:
            arguments = json.loads(argv[2])
        except (ValueError, TypeError):
            raise SystemExit("call requires a JSON object") from None
        if not isinstance(arguments, dict):
            raise SystemExit("call requires a JSON object")
        if not host and argv[1] in ("t3_thread_launch", "create_threads"):
            raise SystemExit("new threads require --host NAME; run `mcp_call.py pick` first, or name the intended backend explicitly")
    else:
        raise SystemExit("usage: mcp_call.py pick | [--host NAME | --env NAME] list | call TOOL JSON")
    name = host or "fd"
    base = host_url(name)
    url = base + "/mcp"
    tok = token_file(name)
    token = read_token(name)
    if token is None:
        raise SystemExit(f"host {name}: token file {tok} is missing, empty or not one printable line")
    session_id = None

    def rpc(method: str, params: dict | None = None, notify: bool = False):
        nonlocal session_id
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = 1
        headers = {"authorization": "Bearer " + token, "content-type": "application/json",
                   "accept": "application/json, text/event-stream", "mcp-protocol-version": "2025-06-18"}
        if session_id:
            headers["mcp-session-id"] = session_id
        try:
            req = urllib.request.Request(url, data=json.dumps(msg).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                session_id = resp.headers.get("mcp-session-id") or session_id
                body = resp.read().decode()
                stream = resp.headers.get("content-type", "").startswith("text/event-stream")
        except (OSError, ValueError, http.client.HTTPException) as e:
            raise SystemExit(f"host {name}: {method} to {url} failed ({failure(e)}); token file {tok}") from None
        if notify:
            return None
        if stream:
            datas = [line[5:].strip() for line in body.splitlines() if line.startswith("data:")]
            body = datas[-1]
        out = json.loads(body)
        if "error" in out:
            code = out["error"].get("code") if isinstance(out["error"], dict) else None
            detail = f" code {code}" if type(code) is int else ""
            raise SystemExit(f"rpc error {method}{detail}")
        return out["result"]

    if host:
        print("host:", name, base)
    init = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                              "clientInfo": {"name": "hash-r2-check", "version": "1"}})
    rpc("notifications/initialized", notify=True)
    print("server:", init.get("serverInfo"), "protocol:", init.get("protocolVersion"))
    if argv[0] == "list":
        tools = rpc("tools/list", {})["tools"]
        with open(PACK + "/mcp-tools.json", "w") as fh:
            json.dump(tools, fh, indent=1)
        print(len(tools), "tools:", [t["name"] for t in tools])
    elif argv[0] == "call":
        if argv[1] == "t3_thread_organize" and arguments.get("action") == "settle" and arguments.get("threadId"):
            refused = sweep_settle_refusal(rpc, name, arguments["threadId"])
            if refused:
                raise SystemExit(f"settle refused for {arguments['threadId']}: {refused}")
        result = rpc("tools/call", {"name": argv[1], "arguments": arguments})
        with open(PACK + "/mcp-last-result.json", "w") as fh:
            json.dump(result, fh, indent=1)
        print(json.dumps(result, indent=1)[:6000])


if __name__ == "__main__":
    main(sys.argv[1:])
