#!/usr/bin/env python3
"""PreToolUse guard: block edits to protected paths.

Stops Edit/Write/MultiEdit whose target file sits under any protected path
prefix, so a directory you must not modify on your own (a vendor tree, a
generated dir, someone else's source) stays read-only even when an agent is
moving fast. Doctrine in a prompt slips; a hook does not.

Configure the protected prefixes in PROTECTED_PATHS (colon-separated absolute
path prefixes). Example:
  export PROTECTED_PATHS="/repo/vendor:/repo/generated"
Override for a deliberate, authorized change: set ALLOW_PROTECTED_EDIT=1.
Exits 2 to block, fails open on any parse error so it can never wedge a call.

Wire it (settings.json):
  "PreToolUse": [{"matcher":"Edit|Write|MultiEdit","hooks":[
    {"type":"command","command":"python3 /abs/path/path-guard.py"}]}]
"""
import sys, os, json

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

if os.environ.get("ALLOW_PROTECTED_EDIT") == "1":
    sys.exit(0)

prefixes = [os.path.realpath(os.path.expanduser(p))
            for p in (os.environ.get("PROTECTED_PATHS") or "").split(":") if p.strip()]
if not prefixes:
    sys.exit(0)

ti = data.get("tool_input")
ti = ti if isinstance(ti, dict) else {}
path = ti.get("file_path") or ti.get("path") or ""
if not isinstance(path, str) or not path:
    sys.exit(0)

# realpath resolves symlinks (so a symlink into a protected dir still matches),
# and on case-insensitive filesystems (macOS/APFS, Windows) fold case so
# /repo/Vendor can't edit the same file /repo/vendor protects.
fold = (lambda s: s.casefold()) if sys.platform in ("darwin", "win32") else (lambda s: s)
norm = fold(os.path.realpath(path))
if any(norm == fold(p) or norm.startswith(fold(p) + os.sep) for p in prefixes):
    print(f"BLOCKED by path-guard: {path} is under a protected path. "
          "Read it and use it, do not modify it here. "
          "If this change is intentional and authorized, re-run with "
          "ALLOW_PROTECTED_EDIT=1.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
