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
        result = rpc("tools/call", {"name": argv[1], "arguments": arguments})
        with open(PACK + "/mcp-last-result.json", "w") as fh:
            json.dump(result, fh, indent=1)
        print(json.dumps(result, indent=1)[:6000])


if __name__ == "__main__":
    main(sys.argv[1:])
