#!/usr/bin/env python3
"""PreToolUse guard: keep a secret out of files, commits, and commands.

Stops any Edit/Write/MultiEdit/Bash whose payload contains a configured secret
(an API key, a private key, a token). The secret is read from a file at runtime
and matched by exact substring, so there are no false positives and the secret
itself is never printed by the hook.

Configure:
  SECRET_FILE   path to a file whose contents are the secret (read verbatim), or
  SECRET_JSON_FILE + SECRET_JSON_KEY   a JSON file and the key to read from it.
Override for a deliberate, authorized case: set ALLOW_SECRET_WRITE=1.
Exits 2 to block, fails open on any error.

Wire it (settings.json) on both Bash and Edit|Write|MultiEdit:
  {"type":"command","command":"python3 /abs/path/secret-guard.py"}
"""
import sys, os, json

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if os.environ.get("ALLOW_SECRET_WRITE") == "1":
    sys.exit(0)

secret = None
try:
    sf = os.environ.get("SECRET_FILE")
    jf = os.environ.get("SECRET_JSON_FILE")
    jk = os.environ.get("SECRET_JSON_KEY")
    if sf:
        with open(os.path.expanduser(sf)) as f:
            secret = f.read().strip()
    elif jf and jk:
        with open(os.path.expanduser(jf)) as f:
            secret = str(json.load(f).get(jk) or "").strip()
except Exception:
    secret = None

if not secret or len(secret) < 12:
    sys.exit(0)  # nothing meaningful to protect

ti = data.get("tool_input") or {}

# Exempt the secret's own file, maintaining it is legitimate. realpath so a
# symlinked or relative path to the same file is still recognized.
fp = ti.get("file_path") or ti.get("path") or ""
fp = os.path.realpath(fp) if fp else ""
for p in (os.environ.get("SECRET_FILE"), os.environ.get("SECRET_JSON_FILE")):
    if p and fp == os.path.realpath(os.path.expanduser(p)):
        sys.exit(0)

# Match escaped-against-escaped: json.dumps turns a real newline/quote/backslash
# in the payload into \n, \", \\, so compare the secret escaped the same way.
# Without this, any multi-line secret (a PEM private key) slips through.
needle = json.dumps(secret)[1:-1]
if needle and needle in json.dumps(ti):
    print("BLOCKED by secret-guard: this write/command contains a protected "
          "secret. Refer to it by its file path and read it at run time instead "
          "of inlining it. If this is deliberate and authorized, re-run with "
          "ALLOW_SECRET_WRITE=1.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
