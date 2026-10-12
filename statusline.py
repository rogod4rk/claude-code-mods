#!/usr/bin/env python3
"""A responsive statusline for Claude Code.

Shows model, project + git branch/dirty, context-window fullness (colored),
session cost, and run-state flags (fast mode, effort). On a narrow terminal it
keeps only the core segments (model, context, cost) and drops the extras, so
nothing critical scrolls off. Reads the statusline JSON on stdin. Fails soft, a
missing or off-schema field drops its own segment, never the whole line.

Install: settings.json -> "statusLine": {"type":"command",
"command":"python3 /absolute/path/statusline.py"}.
"""
import sys, os, json, subprocess

G = "\033[38;5;108m"; Y = "\033[38;5;178m"; R = "\033[38;5;196m"
D = "\033[38;5;240m"; X = "\033[0m"

try:
    d = json.load(sys.stdin)
    assert isinstance(d, dict)
except Exception:
    d = {}


def sub(key):
    """Nested object as a dict, or {} if absent/wrong-typed (never raises)."""
    v = d.get(key)
    return v if isinstance(v, dict) else {}


def cols():
    c = os.environ.get("COLUMNS")
    if c and c.isdigit():
        return int(c)
    try:  # read the real terminal size directly, no subprocess, no pipe fallback
        with open("/dev/tty") as tty:
            n = os.get_terminal_size(tty.fileno()).columns
            if n:
                return n
    except Exception:
        pass
    return 120  # unknown -> assume wide, preserve all segments


WIDE = cols() >= 95
core, extra = [], []

model = sub("model").get("display_name")
if isinstance(model, str) and model:
    core.append(f"{D}⬡{X} {model}")

pct = sub("context_window").get("used_percentage")
if isinstance(pct, (int, float)):
    c = G if pct < 50 else (Y if pct < 75 else R)
    tag = f"{c}ctx {int(round(pct))}%{X}"
    if d.get("exceeds_200k_tokens"):
        tag += f" {R}!200k{X}"
    core.append(tag)

cost = sub("cost").get("total_cost_usd")
if isinstance(cost, (int, float)) and cost > 0:
    core.append(f"{D}${cost:.2f}{X}")

# Extras only when the terminal is wide, so no work is done for output we'd drop.
if WIDE:
    cwd = sub("workspace").get("current_dir") or d.get("cwd")
    if isinstance(cwd, str) and cwd:
        try:
            base = os.path.basename(cwd.rstrip("/")) or "/"
            gs = subprocess.run(["git", "-C", cwd, "status", "--porcelain=v1", "--branch"],
                              capture_output=True, text=True, timeout=2)
            if gs.returncode == 0:
                lines = gs.stdout.splitlines()
                branch = lines[0][3:].split("...")[0].split(" ")[0] if lines and lines[0].startswith("## ") else ""
                star = f"{Y}*{X}" if any(not l.startswith("## ") for l in lines) else ""
                extra.append(f"{D}{base} ⎇ {branch}{X}{star}")
            else:
                extra.append(f"{D}{base}{X}")
        except Exception:
            pass

    flags = []
    if d.get("fast_mode"):
        flags.append("⚡fast")
    lvl = sub("effort").get("level")
    if lvl and lvl != "medium":
        flags.append(str(lvl))
    if flags:
        extra.append(f"{D}{' '.join(flags)}{X}")

print(f" {D}·{X} ".join(core + extra))
