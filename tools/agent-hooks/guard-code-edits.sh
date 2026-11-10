#!/bin/sh
# PreToolUse hook shared by Claude Code (.claude/settings.json) and Codex
# (.codex/hooks.json). Code edits (*.py, *.ipynb, Makefile) in this repo are
# allowed only on a branch feature/NNN-name whose specs/NNN-name/spec.md
# exists, i.e. only through the `feature` skill. Exit 2 with a reason on
# stderr blocks the call in both tools.
#
# Input (JSON on stdin):
#   Claude Code: tool_input.file_path or tool_input.notebook_path
#   Codex apply_patch: tool_input.command holds the patch, whose
#     "*** Add/Update/Delete File: <path>" and "*** Move to: <path>" lines
#     name the files.
#
# Rules, for each code file named by the call:
# - The file's repo is found from the file's own location, so each git
#   worktree is checked on its own branch. Files outside this repo (scratch
#   scripts in a temp dir, other repos) are not guarded.
# - During a merge (MERGE_HEAD exists), files still in conflict can be edited
#   on any branch, so a `sync` conflict on main can be resolved.
#
# Limits:
# - An edit made through a shell command (sed, cat > file) is not seen.
# - Only exit 2 blocks. If the hook command itself cannot start (script path
#   not resolved, e.g. git rev-parse failing in .codex/hooks.json or an empty
#   CLAUDE_PROJECT_DIR), the shell exits 127 and both tools let the edit
#   through. Any error inside the guard blocks (exit 2).

if ! command -v python3 >/dev/null 2>&1; then
    echo "Blocked: the edit guard needs python3 (tools/agent-hooks/guard-code-edits.sh)." >&2
    exit 2
fi

HOOK_INPUT=$(cat)
GUARD_REPO=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)
export HOOK_INPUT GUARD_REPO
python3 -I - <<'PY'
import json, os, re, subprocess, sys

def block(msg):
    print("Blocked: " + msg, file=sys.stderr)
    sys.exit(2)

def git(where, *args):
    try:
        r = subprocess.run(["git", "-C", where, *args],
                           capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None

def common_dir(where):
    d = git(where, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return os.path.realpath(d) if d else None

def existing_dir(path):
    d = os.path.dirname(path)
    while not os.path.isdir(d):
        d = os.path.dirname(d)
    return d

try:
    data = json.loads(os.environ.get("HOOK_INPUT", ""))
    ti = data.get("tool_input") or {}
    paths = [ti[k] for k in ("file_path", "notebook_path")
             if isinstance(ti.get(k), str)]
    cmd = ti.get("command")
    if isinstance(cmd, str) and "*** Begin Patch" in cmd:
        paths += re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$",
                            cmd, re.M)
except Exception:
    block("the edit guard could not read the hook input.")

try:
    code = [p for p in paths if re.search(r"\.(py|ipynb)$|(^|/)Makefile$", p)]
    if not code:
        sys.exit(0)
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    # The repo this hook belongs to (the one holding this script), identified
    # by its common git dir, which every worktree of the repo shares.
    project = None
    for start in (os.environ.get("GUARD_REPO"), os.environ.get("CLAUDE_PROJECT_DIR"), cwd):
        if start and os.path.isdir(start):
            project = common_dir(start)
            if project:
                break
    problems = []
    for p in code:
        full = os.path.realpath(os.path.join(cwd, p))
        d = existing_dir(full)
        repo_common = common_dir(d)
        if repo_common is None or (project and repo_common != project):
            continue  # not in this repo
        root = os.path.realpath(git(d, "rev-parse", "--show-toplevel") or d)
        branch = git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        m = re.fullmatch(r"feature/(\d{3}-.+)", branch)
        if m:
            spec = os.path.join(root, "specs", m.group(1), "spec.md")
            if not os.path.isfile(spec):
                problems.append(f"{spec} is missing. Write the spec first (feature skill).")
            continue
        if git(root, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None:
            unmerged = (git(root, "diff", "--name-only", "--diff-filter=U") or "").splitlines()
            if os.path.relpath(full, root) in unmerged:
                continue  # resolving a merge conflict
        problems.append(f"code edits ({p}) need the feature skill: spec in "
                        f"specs/NNN-name/, branch feature/NNN-name (current branch: {branch}).")
    if problems:
        block(" ".join(problems))
except SystemExit:
    raise
except Exception as e:
    block(f"the edit guard failed ({e}).")
PY
