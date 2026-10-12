# claude-code-mods

Three small, dependency-free mods for [Claude Code](https://claude.com/claude-code):
a responsive statusline and two safety hooks. Plain Python 3, no installs, each
fails open so it can never wedge your session.

## What's here

### `statusline.py`
A statusline that stays readable on any screen. Shows model, project + git
branch (with a `*` when the tree is dirty), context-window fullness (green →
amber → red as it fills), session cost, and run-state flags (fast mode, effort
level). On a narrow terminal it automatically drops the extras and keeps only
model / context / cost, so nothing important scrolls off.

### `hooks/path-guard.py`
Blocks edits to paths you don't want touched (a vendor tree, generated code,
someone else's source). Set `PROTECTED_PATHS` to colon-separated absolute path
prefixes. An agent moving fast can't quietly rewrite them. Override a deliberate
change with `ALLOW_PROTECTED_EDIT=1`.

### `hooks/secret-guard.py`
Keeps a secret (API key, private key, token) from ever landing in a file,
commit, or shell command. Point it at the file that holds the secret; it matches
by exact substring and never prints the secret itself. Override with
`ALLOW_SECRET_WRITE=1`.

## Install

Copy the files somewhere stable and reference them by absolute path in
`~/.claude/settings.json`. See `settings.example.json` for the exact shape.

```jsonc
{
  "statusLine": { "type": "command", "command": "python3 /abs/path/statusline.py" },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit", "hooks": [
        { "type": "command", "command": "python3 /abs/path/hooks/path-guard.py" },
        { "type": "command", "command": "python3 /abs/path/hooks/secret-guard.py" }
      ]},
      { "matcher": "Bash", "hooks": [
        { "type": "command", "command": "python3 /abs/path/hooks/secret-guard.py" }
      ]}
    ]
  }
}
```

Set the env for the guards (in your shell profile or Claude Code's `env` block):

```bash
export PROTECTED_PATHS="/path/to/vendor:/path/to/generated"
export SECRET_FILE="/path/to/the/secret"      # or SECRET_JSON_FILE + SECRET_JSON_KEY
```

Restart Claude Code. Hooks take effect immediately; the statusline shows on the
next render.

## Notes

- A hook exits 2 to block and prints the reason to stderr; it exits 0 to allow.
- Everything fails open: a parse error or missing config means "allow", so a
  broken hook never blocks your work.
- No network, no dependencies, no telemetry.

## Limitations (read before you rely on these)

These are convenience guards that stop the common mistake, not hardened security
boundaries. Known limits:

- They act on the path and payload a tool reports. `path-guard` resolves symlinks
  and folds case on macOS/Windows, but an agent that shells out to write a file by
  some other means is outside its view. Pair it with real filesystem permissions
  for anything that must not be writable.
- `secret-guard` blocks a known secret from appearing verbatim in a payload. It
  will not catch a re-encoded (base64, split, obfuscated) copy of the same secret.
- The statusline's width detection uses `COLUMNS` then the controlling terminal;
  if neither is available it assumes wide. It never crashes, worst case it shows
  all segments.

## License

MIT. See `LICENSE`.
